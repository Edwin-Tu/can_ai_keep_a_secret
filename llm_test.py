"""
LLM Secret Guard Python Automation CLI.

Main entry for the python_automation branch.

Interactive workflow:
1. Environment check / preparation
2. Select test mode:
   - Download model(s), supports multiple models
   - Model testing / list local models
3. Run benchmark when requested
4. Generate report when benchmark succeeds

Important behavior in this version:
- Local model listing uses the Ollama HTTP API first, so it still works when
  the Ollama service is running but ollama.exe is not visible in PATH.
- Multiple model testing can run directly from installed local models. It no
  longer depends on configs/local_models.json being populated.
- configs/local_models.json batch mode is kept as an advanced/legacy option.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import requests

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from src.automation.env_check import run_env_check
from src.automation.ollama_tools import (
    check_ollama_api,
    get_installed_models,
    list_models,
    pull_model,
    show_model,
    stop_model,
)
from src.automation.benchmark_runner import run_batch_benchmark, run_single_benchmark
from src.automation.report_runner import generate_charts, generate_reports
from src.automation.model_selector import interactive_select_and_run

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")


def normalize_model_name(model: str) -> str:
    """Normalize a model name for src/run_benchmark.py."""
    model = (model or "").strip()
    if not model:
        return ""
    if model == "mock" or model.startswith("ollama:"):
        return model
    return f"ollama:{model}"


def ollama_local_name(model: str) -> str:
    """Return the Ollama model name without the ollama: prefix."""
    model = (model or "").strip()
    if model.startswith("ollama:"):
        return model.split("ollama:", 1)[1]
    return model


def parse_optional_int(raw: str, default: Optional[int] = None) -> Optional[int]:
    value = (raw or "").strip()
    if not value:
        return default
    try:
        parsed = int(value)
    except ValueError:
        print(f"[WARN] Invalid integer value: {raw!r}. Using default: {default}")
        return default
    return parsed if parsed > 0 else None


def parse_model_names(raw: str) -> list[str]:
    """Parse one or more model names.

    Supported separators: comma, Chinese comma, semicolon, space, tab, newline.
    Returned names are plain Ollama names without the optional ollama: prefix.
    """
    if not raw:
        return []

    normalized = raw
    for separator in (",", "，", "、", ";", "；", "\n", "\t"):
        normalized = normalized.replace(separator, " ")

    models: list[str] = []
    seen: set[str] = set()
    for item in normalized.split(" "):
        model = ollama_local_name(item.strip())
        if model and model not in seen:
            models.append(model)
            seen.add(model)
    return models


def ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{prompt}{suffix}: ").strip()
    return value if value else default


def ask_yes_no(prompt: str, default: bool = True) -> bool:
    default_text = "Y/n" if default else "y/N"
    value = input(f"{prompt} [{default_text}]: ").strip().lower()
    if not value:
        return default
    return value in {"y", "yes", "1", "true", "是", "好"}


def find_ollama_executable() -> Optional[Path]:
    """Find ollama executable from OLLAMA_EXE, PATH, or common locations."""
    env_exe = os.environ.get("OLLAMA_EXE")
    if env_exe:
        candidate = Path(env_exe)
        if candidate.exists():
            return candidate

    found = shutil.which("ollama")
    if found:
        return Path(found)

    candidates: list[Path] = []
    local_appdata = os.environ.get("LOCALAPPDATA")
    program_files = os.environ.get("ProgramFiles")
    program_files_x86 = os.environ.get("ProgramFiles(x86)")

    if local_appdata:
        candidates.extend(
            [
                Path(local_appdata) / "Programs" / "Ollama" / "ollama.exe",
                Path(local_appdata) / "Ollama" / "ollama.exe",
            ]
        )
    if program_files:
        candidates.append(Path(program_files) / "Ollama" / "ollama.exe")
    if program_files_x86:
        candidates.append(Path(program_files_x86) / "Ollama" / "ollama.exe")

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def refresh_ollama_path() -> Optional[Path]:
    """Add detected Ollama folder to PATH for the current Python process."""
    exe = find_ollama_executable()
    if not exe:
        return None

    folder = str(exe.parent)
    current_path = os.environ.get("PATH", "")
    path_parts = [p.strip().lower() for p in current_path.split(os.pathsep) if p.strip()]
    if folder.lower() not in path_parts:
        os.environ["PATH"] = folder + os.pathsep + current_path
    return exe


def wait_for_ollama_api(timeout_sec: int = 60) -> bool:
    """Wait for the local Ollama API to become available."""
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        if check_ollama_api(quiet=True):
            return True
        time.sleep(2)
    return check_ollama_api(quiet=True)


def start_ollama_server() -> bool:
    """Start `ollama serve` in the background when the CLI exists."""
    if check_ollama_api(quiet=True):
        return True

    exe = refresh_ollama_path()
    if not exe:
        return False

    print("[INFO] Starting Ollama server in the background...")
    try:
        kwargs = {
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
            "stdin": subprocess.DEVNULL,
        }
        if os.name == "nt":
            kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        subprocess.Popen([str(exe), "serve"], **kwargs)
    except Exception as exc:
        print(f"[WARN] Could not start Ollama server automatically: {exc}")
        return False

    return wait_for_ollama_api(timeout_sec=60)


def install_ollama() -> bool:
    """Install Ollama interactively using the platform's preferred installer."""
    if find_ollama_executable():
        refresh_ollama_path()
        print("[OK] Ollama CLI already exists.")
        return True

    system = platform.system().lower()
    print("\nOllama is required for local model testing, but it was not found.")

    if system == "windows":
        print("This will run the official Ollama Windows PowerShell installer:")
        print("  irm https://ollama.com/install.ps1 | iex")
        if not ask_yes_no("Download and install Ollama now?", default=True):
            return False

        powershell = (
            shutil.which("powershell")
            or shutil.which("powershell.exe")
            or shutil.which("pwsh")
            or shutil.which("pwsh.exe")
        )
        if not powershell:
            print("[FAIL] PowerShell was not found. Please install Ollama manually from https://ollama.com/download/windows")
            return False

        cmd = [
            powershell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            "irm https://ollama.com/install.ps1 | iex",
        ]
        result = subprocess.run(cmd)
        if result.returncode != 0:
            print("[FAIL] Ollama installer returned a non-zero exit code.")
            return False

        exe = refresh_ollama_path()
        if exe:
            print(f"[OK] Ollama CLI detected: {exe}")
        else:
            print("[WARN] Ollama installer finished, but ollama.exe was not detected in this shell.")
            print("       Please restart PowerShell / VS Code, then run `python llm_test.py env` again.")
            return False

        if start_ollama_server():
            print("[OK] Ollama API is available.")
            return True

        print("[WARN] Ollama CLI is installed, but the API is not available yet.")
        print("       Open the Ollama app or run `ollama serve`, then retry.")
        return False

    if system == "linux":
        print("This will run the official Ollama Linux installer:")
        print("  curl -fsSL https://ollama.com/install.sh | sh")
        if not ask_yes_no("Download and install Ollama now?", default=True):
            return False
        result = subprocess.run("curl -fsSL https://ollama.com/install.sh | sh", shell=True)
        refresh_ollama_path()
        return result.returncode == 0 and start_ollama_server()

    if system == "darwin":
        print("Automatic macOS install is not enabled in this script.")
        print("Please install Ollama from https://ollama.com/download, then rerun this command.")
        return False

    print(f"[FAIL] Unsupported platform for automatic Ollama install: {platform.system()}")
    return False


def ensure_ollama_ready(allow_install: bool = True) -> bool:
    """Ensure Ollama API is available; optionally install/start it."""
    if check_ollama_api(quiet=True):
        return True
    if start_ollama_server():
        return True
    if allow_install and install_ollama():
        return check_ollama_api(quiet=True) or start_ollama_server()

    print("[FAIL] Ollama API is not available at http://localhost:11434.")
    print("[INFO] Open the Ollama app or run `ollama serve`, then retry.")
    return False


def get_local_models() -> list[str]:
    """Return local Ollama models using the API-first path."""
    if not ensure_ollama_ready(allow_install=True):
        return []
    models = get_installed_models()
    return sorted(dict.fromkeys(models))


def print_local_model_list(models: Optional[list[str]] = None) -> list[str]:
    """Print local Ollama models and return their names."""
    installed = get_local_models() if models is None else models

    print("\nLocal Ollama model list")
    print("=" * 72)
    if not installed:
        print("[INFO] No local Ollama models were found.")
        print("[INFO] Use download mode first, for example:")
        print("       python llm_test.py pull llama3.2:1b qwen2.5:3b")
        return []

    for index, model in enumerate(installed, start=1):
        print(f"  {index}. {model}")
    return installed


def pull_model_via_api(model: str) -> int:
    """Pull an Ollama model through the local HTTP API when CLI is unavailable."""
    if not check_ollama_api(quiet=True):
        print("[FAIL] Ollama API is unavailable. Cannot download model through API.")
        return 1

    print(f"[INFO] Pulling via Ollama API: {model}")
    try:
        with requests.post(
            f"{OLLAMA_BASE_URL}/api/pull",
            json={"name": model, "stream": True},
            timeout=600,
            stream=True,
        ) as response:
            response.raise_for_status()
            for raw_line in response.iter_lines(decode_unicode=True):
                if not raw_line:
                    continue
                try:
                    data = json.loads(raw_line)
                except json.JSONDecodeError:
                    print(raw_line)
                    continue
                status = data.get("status")
                completed = data.get("completed")
                total = data.get("total")
                if completed and total:
                    percent = completed / total * 100
                    print(f"[INFO] {status}: {percent:.1f}%")
                elif status:
                    print(f"[INFO] {status}")
                if data.get("error"):
                    print(f"[FAIL] {data['error']}")
                    return 1
    except Exception as exc:
        print(f"[FAIL] API pull failed: {exc}")
        return 1

    return 0


def pull_one_model(model: str) -> int:
    """Pull one model through CLI when possible, otherwise through API."""
    model = ollama_local_name(model)
    if not model:
        print("[FAIL] Empty model name.")
        return 1

    exe = refresh_ollama_path()
    if exe:
        return pull_model(model)
    return pull_model_via_api(model)


def pull_models(models: list[str]) -> int:
    """Pull one or more Ollama models."""
    cleaned_models: list[str] = []
    seen: set[str] = set()
    for raw_model in models:
        model = ollama_local_name(raw_model).strip()
        if model and model not in seen:
            cleaned_models.append(model)
            seen.add(model)

    if not cleaned_models:
        print("[INFO] No models selected for download.")
        return 0

    if not ensure_ollama_ready(allow_install=True):
        return 1

    failed: list[str] = []
    for index, model in enumerate(cleaned_models, start=1):
        print("\n" + "=" * 72)
        print(f"Download model [{index}/{len(cleaned_models)}]: {model}")
        print("=" * 72)
        code = pull_one_model(model)
        if code != 0:
            failed.append(model)
            print(f"[FAIL] Failed to download: {model}")
        else:
            print(f"[OK] Downloaded or updated: {model}")

    print("\n" + "=" * 72)
    print("Download Summary")
    print("=" * 72)
    print(f"Success: {len(cleaned_models) - len(failed)}")
    print(f"Failed: {len(failed)}")
    for model in failed:
        print(f"  [FAIL] {model}")

    return 0 if not failed else 1


def download_models_interactively() -> int:
    """Interactive model download flow. Supports one or many models."""
    print("\nDownload model(s)")
    print("Examples:")
    print("  llama3.2:1b")
    print("  llama3.2:1b qwen2.5:3b")
    print("  llama3.2:1b, qwen2.5:3b, gemma2:2b")
    raw = ask("Enter model name(s), separated by comma or space", "")
    return pull_models(parse_model_names(raw))


def ensure_ollama_model_available(model: str, auto_pull: bool = False) -> bool:
    """Ensure an Ollama model exists locally, offering to pull it when missing."""
    normalized = normalize_model_name(model)
    if normalized == "mock":
        return True
    if not normalized.startswith("ollama:"):
        return True
    if not ensure_ollama_ready(allow_install=True):
        return False

    local_name = ollama_local_name(normalized)
    installed = get_installed_models()
    if local_name in installed:
        return True

    print(f"[WARN] Model not installed: {local_name}")
    should_pull = auto_pull or ask_yes_no(f"Download {local_name} now?", default=True)
    if not should_pull:
        return False

    if pull_one_model(local_name) != 0:
        print(f"[FAIL] Failed to pull model: {local_name}")
        return False
    return True


def parse_model_selection(raw: str, installed: list[str]) -> list[str]:
    """Parse model selection from indices, ranges, names, or all.

    Examples:
    - all
    - 1 2 3
    - 1,3
    - 1-3
    - llama3.2:1b qwen2.5:3b
    """
    raw = (raw or "").strip()
    if not raw:
        return []
    if raw.lower() in {"all", "a", "全部"}:
        return installed[:]

    tokens = parse_model_names(raw)
    selected: list[str] = []
    seen: set[str] = set()

    def add_model(model: str) -> None:
        model = ollama_local_name(model)
        if model and model not in seen:
            selected.append(model)
            seen.add(model)

    for token in tokens:
        if "-" in token and all(part.strip().isdigit() for part in token.split("-", 1)):
            start_raw, end_raw = token.split("-", 1)
            start, end = int(start_raw), int(end_raw)
            if start > end:
                start, end = end, start
            for index in range(start, end + 1):
                if 1 <= index <= len(installed):
                    add_model(installed[index - 1])
                else:
                    print(f"[WARN] Selection index out of range: {index}")
            continue

        if token.isdigit():
            index = int(token)
            if 1 <= index <= len(installed):
                add_model(installed[index - 1])
            else:
                print(f"[WARN] Selection index out of range: {index}")
            continue

        add_model(token)

    return selected


def choose_model_interactively(allow_mock: bool = True) -> str:
    """Ask user to choose mock, an installed Ollama model, or manual model name."""
    installed = print_local_model_list()

    print("\nAvailable choices:")
    if allow_mock:
        print("  0. mock")
    print("  M. Manually type model name")

    default_choice = "0" if allow_mock else ("1" if installed else "M")
    choice = ask("Select model", default_choice)

    if choice.lower() == "m":
        model = normalize_model_name(
            ask("Enter model name, e.g. llama3.2:1b or ollama:llama3.2:1b", "")
        )
        if not model:
            print("[FAIL] No model entered.")
            return "mock" if allow_mock else ""
        if model != "mock" and not ensure_ollama_model_available(model):
            print("[FAIL] Selected model is not available.")
            return "mock" if allow_mock else ""
        return model

    try:
        selected_index = int(choice)
    except ValueError:
        print("[WARN] Invalid selection.")
        return "mock" if allow_mock else ""

    if allow_mock and selected_index == 0:
        return "mock"
    if 1 <= selected_index <= len(installed):
        return normalize_model_name(installed[selected_index - 1])

    print("[WARN] Selection out of range.")
    return "mock" if allow_mock else ""


def ask_benchmark_options() -> tuple[float, Optional[int], str]:
    """Ask common benchmark/report options."""
    temperature_raw = ask("Temperature", "0")
    try:
        temperature = float(temperature_raw)
    except ValueError:
        print("[WARN] Invalid temperature. Using 0.")
        temperature = 0.0

    max_tokens = parse_optional_int(
        ask("Max tokens per response. Leave blank for unlimited/model default", ""),
        default=None,
    )

    report_mode = ask("Report mode: public/internal", "public")
    if report_mode not in {"public", "internal"}:
        print("[WARN] Invalid report mode. Using public.")
        report_mode = "public"

    return temperature, max_tokens, report_mode


def run_multiple_local_benchmarks(
    models: list[str],
    temperature: float = 0,
    max_tokens: int | None = None,
    report_mode: str = "public",
) -> int:
    """Run benchmark for multiple selected local models."""
    cleaned = []
    seen: set[str] = set()
    for model in models:
        local_name = ollama_local_name(model)
        if local_name and local_name not in seen:
            cleaned.append(local_name)
            seen.add(local_name)

    if not cleaned:
        print("[FAIL] No models selected for multiple model test.")
        return 1

    print("\n" + "=" * 72)
    print("Run multiple local model benchmarks")
    print("=" * 72)
    print("Models:")
    for model in cleaned:
        print(f"  - {model}")

    success: list[str] = []
    failed: list[str] = []

    for index, model in enumerate(cleaned, start=1):
        print("\n" + "=" * 72)
        print(f"[{index}/{len(cleaned)}] Benchmark model: {model}")
        print("=" * 72)

        normalized = normalize_model_name(model)
        if not ensure_ollama_model_available(normalized, auto_pull=False):
            failed.append(model)
            continue

        code = run_single_benchmark(
            model=normalized,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if code == 0:
            success.append(model)
            print(f"[OK] Benchmark completed: {model}")
        else:
            failed.append(model)
            print(f"[FAIL] Benchmark failed: {model}")

    if success:
        print("\nGenerate report")
        report_code = generate_reports(mode=report_mode)
        if report_code != 0:
            print("[FAIL] Report generation failed.")
            return report_code
    else:
        print("[FAIL] No successful benchmark runs. Report generation skipped.")

    print("\n" + "=" * 72)
    print("Multiple Model Test Summary")
    print("=" * 72)
    print(f"Success: {len(success)}")
    for model in success:
        print(f"  [OK] {model}")
    print(f"Failed: {len(failed)}")
    for model in failed:
        print(f"  [FAIL] {model}")

    return 0 if not failed and success else 1


def run_model_test_menu() -> int:
    """Interactive test/list flow for local models."""
    if not ensure_ollama_ready(allow_install=True):
        print("[FAIL] Ollama is required for local model testing.")
        return 1

    installed = print_local_model_list()

    print("\nModel testing / local model list")
    print("  1. List local models only")
    print("  2. Single model test")
    print("  3. Multiple model test from local installed models")
    print("  4. Batch models from configs/local_models.json (advanced)")
    test_mode = ask("Choose action", "1")

    if test_mode == "1":
        return 0

    if test_mode not in {"2", "3", "4"}:
        print("[WARN] Invalid action. Please choose 1, 2, 3, or 4.")
        return 1

    temperature, max_tokens, report_mode = ask_benchmark_options()

    if test_mode == "2":
        model = choose_model_interactively(allow_mock=False)
        if not model:
            print("[FAIL] No valid model selected. Benchmark skipped.")
            return 1
        if not ensure_ollama_model_available(model):
            print("[FAIL] Ollama model is not available. Benchmark skipped.")
            return 1
        code = run_single_benchmark(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if code != 0:
            print("[FAIL] Benchmark failed. Report generation skipped.")
            return code
        print("\nGenerate report")
        return generate_reports(mode=report_mode)

    if test_mode == "3":
        if not installed:
            print("[FAIL] No local models available for multiple model test.")
            return 1
        print("\nSelect multiple models")
        print("Examples:")
        print("  all")
        print("  1 2 3")
        print("  1,3")
        print("  1-3")
        print("  llama3.2:1b qwen2.5:3b")
        raw = ask("Choose model numbers/names", "all")
        selected = parse_model_selection(raw, installed)
        return run_multiple_local_benchmarks(
            selected,
            temperature=temperature,
            max_tokens=max_tokens,
            report_mode=report_mode,
        )

    # Advanced legacy config-file mode.
    code = run_batch_benchmark(
        temperature=temperature,
        max_tokens=max_tokens,
        report_mode=report_mode,
        skip_report=False,
    )
    return code


def run_wizard() -> int:
    """Interactive no-argument flow: env -> download or test/list."""
    print("=" * 72)
    print("LLM Secret Guard Test Wizard")
    print("=" * 72)
    print("This wizard will run:")
    print("1. Environment check / preparation")
    print("2. Select test mode")
    print("   1) Download model(s)")
    print("   2) Model testing / list local models")
    print("=" * 72)

    print("\nStep 1/2: Environment check")
    env_code = run_env_check(fix=True)
    if env_code != 0:
        if ask_yes_no("Try to install/start Ollama automatically?", default=True):
            ensure_ollama_ready(allow_install=True)
            env_code = run_env_check(fix=True)

        if env_code != 0:
            continue_anyway = ask_yes_no(
                "Environment check still found issues. Continue anyway?",
                default=False,
            )
            if not continue_anyway:
                return env_code

    print("\nStep 2/2: Select test mode")
    print("  1. Download model(s) - supports multiple model download")
    print("  2. Model testing / list local models - single or multiple model test")
    mode = ask("Choose mode", "2")

    if mode == "1":
        return download_models_interactively()
    if mode == "2":
        return run_model_test_menu()

    print("[WARN] Invalid mode. Please choose 1 or 2.")
    return 1


def add_common_benchmark_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--temperature", type=float, default=0, help="Model temperature. Default: 0.")
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=None,
        help="Optional per-response output token limit. Omit or <=0 for unlimited/model default.",
    )
    parser.add_argument(
        "--report-mode",
        choices=["public", "internal"],
        default="public",
        help="Report mode. public hides high-risk previews; internal keeps redacted previews.",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="LLM Secret Guard automation CLI",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command")

    env = sub.add_parser("env", help="Check and prepare local environment")
    env.add_argument("--fix", action="store_true", help="Create missing output folders when possible.")

    sub.add_parser("wizard", help="Run interactive test wizard")
    sub.add_parser("install-ollama", help="Download/install Ollama, then try to start the local API")
    sub.add_parser("list", help="List local Ollama models through API-first path")

    pull = sub.add_parser("pull", help="Pull one or more Ollama models")
    pull.add_argument("models", nargs="+", help="Example: llama3.2:1b qwen2.5:3b")

    download = sub.add_parser("download", help="Alias of pull. Download one or more Ollama models")
    download.add_argument("models", nargs="+", help="Example: llama3.2:1b qwen2.5:3b")

    show = sub.add_parser("show", help="Show Ollama model information")
    show.add_argument("model", help="Example: llama3.2:1b")

    stop = sub.add_parser("stop", help="Stop an Ollama model")
    stop.add_argument("model", help="Example: llama3.2:1b")

    test = sub.add_parser("test", help="Run benchmark for one model only")
    test.add_argument("model", help="mock, ollama:<model>, or plain Ollama model name")
    add_common_benchmark_args(test)
    test.add_argument("--skip-env", action="store_true", help="Skip pre-test environment check.")

    run = sub.add_parser("run", help="Run env check, benchmark one model, then generate report")
    run.add_argument("model", help="mock, ollama:<model>, or plain Ollama model name")
    add_common_benchmark_args(run)
    run.add_argument("--pull-if-missing", action="store_true", help="Pull Ollama model if it is missing.")

    batch = sub.add_parser("batch", help="Run multiple local models. If no model is provided, run all installed models.")
    batch.add_argument("models", nargs="*", help="Optional model names. Example: llama3.2:1b qwen2.5:3b")
    add_common_benchmark_args(batch)

    batch_config = sub.add_parser("batch-config", help="Advanced: run models from configs/local_models.json")
    add_common_benchmark_args(batch_config)
    batch_config.add_argument("--skip-report", action="store_true", help="Do not generate reports after batch run.")

    report = sub.add_parser("report", help="Generate reports from results/*.csv, then generate charts by default")
    report.add_argument("--mode", choices=["public", "internal"], default="public", help="Report mode.")
    report.add_argument("--no-charts", action="store_true", help="Generate reports only; skip automatic chart generation.")

    chart = sub.add_parser("chart", help="Generate charts from results/report.json")
    chart.add_argument("chart_id", nargs="?", default=None, help="Optional chart id. Omit or use 'all' to generate every chart.")
    chart.add_argument("--list", action="store_true", help="List available chart modules.")
    chart.add_argument("--input", default="results/report.json", help="Input structured report JSON path.")
    chart.add_argument("--output", default="visuals", help="Chart output directory.")
    chart.add_argument("--model", default=None, help="Optional model filter. Example: ollama:qwen2.5:7b")

    select = sub.add_parser("select", help="Interactive model selection and run")
    add_common_benchmark_args(select)

    all_cmd = sub.add_parser("all", help="Run env check, all installed local models, then reports")
    add_common_benchmark_args(all_cmd)

    clean = sub.add_parser("clean", help="Delete generated outputs")
    clean.add_argument("--results", action="store_true", help="Delete CSV files in results/")
    clean.add_argument("--reports", action="store_true", help="Delete generated reports in reports/")
    clean.add_argument("--visuals", action="store_true", help="Delete generated chart images in visuals/")
    clean.add_argument("--all", action="store_true", help="Delete results, reports, and visuals")

    return parser


def clean_outputs(args: argparse.Namespace) -> int:
    delete_results = args.results or args.all
    delete_reports = args.reports or args.all
    delete_visuals = args.visuals or args.all

    if not delete_results and not delete_reports and not delete_visuals:
        print("[INFO] Nothing selected. Use --results, --reports, --visuals, or --all.")
        return 0

    if delete_results:
        results_dir = ROOT / "results"
        for pattern in ("results_*.csv", "report.json"):
            for path in results_dir.glob(pattern):
                path.unlink()
                print(f"[DEL] {path}")

    if delete_reports:
        reports_dir = ROOT / "reports"
        for pattern in ("report_*.md", "model_metrics_summary.csv"):
            for path in reports_dir.glob(pattern):
                path.unlink()
                print(f"[DEL] {path}")

    if delete_visuals:
        visuals_dir = ROOT / "visuals"
        for path in visuals_dir.glob("*.png"):
            path.unlink()
            print(f"[DEL] {path}")

    return 0


def main() -> int:
    if len(sys.argv) == 1:
        return run_wizard()

    parser = build_parser()
    args = parser.parse_args()

    if args.command in (None, "wizard"):
        return run_wizard()

    if args.command == "env":
        code = run_env_check(fix=args.fix)
        if code != 0 and args.fix:
            if ask_yes_no("Try to install/start Ollama automatically?", default=True):
                ensure_ollama_ready(allow_install=True)
                return run_env_check(fix=args.fix)
        return code

    if args.command == "install-ollama":
        return 0 if ensure_ollama_ready(allow_install=True) else 1

    if args.command == "list":
        print_local_model_list()
        return 0

    if args.command in {"pull", "download"}:
        return pull_models(args.models)

    if args.command == "show":
        if not ensure_ollama_ready(allow_install=True):
            return 1
        return show_model(ollama_local_name(args.model))

    if args.command == "stop":
        if not ensure_ollama_ready(allow_install=False):
            return 1
        return stop_model(ollama_local_name(args.model))

    if args.command == "test":
        model = normalize_model_name(args.model)
        if not args.skip_env:
            run_env_check(fix=True, require_ollama=(model != "mock"))
        if model != "mock" and not ensure_ollama_model_available(model):
            return 1
        return run_single_benchmark(
            model=model,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
        )

    if args.command == "run":
        model = normalize_model_name(args.model)
        run_env_check(fix=True, require_ollama=(model != "mock"))
        if model != "mock" and not ensure_ollama_model_available(model, auto_pull=args.pull_if_missing):
            return 1
        code = run_single_benchmark(
            model=model,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
        )
        if code != 0:
            return code
        return generate_reports(mode=args.report_mode)

    if args.command == "batch":
        if not ensure_ollama_ready(allow_install=True):
            return 1
        models = [ollama_local_name(model) for model in args.models]
        if not models:
            models = print_local_model_list()
        return run_multiple_local_benchmarks(
            models,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            report_mode=args.report_mode,
        )

    if args.command == "batch-config":
        if not ensure_ollama_ready(allow_install=True):
            return 1
        return run_batch_benchmark(
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            report_mode=args.report_mode,
            skip_report=args.skip_report,
        )

    if args.command == "report":
        return generate_reports(
            mode=args.mode,
            generate_chart_outputs=not args.no_charts,
        )

    if args.command == "chart":
        if args.list:
            return subprocess.call([sys.executable, "src/chart_runner.py", "list"], cwd=ROOT)
        chart_id = None if args.chart_id in (None, "all") else args.chart_id
        return generate_charts(
            chart_id=chart_id,
            report_json=args.input,
            output_dir=args.output,
            model=args.model,
        )

    if args.command == "select":
        return interactive_select_and_run(
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            report_mode=args.report_mode,
        )

    if args.command == "all":
        run_env_check(fix=True)
        if not ensure_ollama_ready(allow_install=True):
            return 1
        models = print_local_model_list()
        return run_multiple_local_benchmarks(
            models,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            report_mode=args.report_mode,
        )

    if args.command == "clean":
        return clean_outputs(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
