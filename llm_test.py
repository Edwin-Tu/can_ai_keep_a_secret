"""
LLM Secret Guard Python Automation CLI.

Main entry for the python_automation branch.

Workflow:
1. Environment check / preparation
2. Model selection: single or batch
3. Run benchmark
4. Generate report

When executed without arguments, this file starts an interactive test wizard.
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

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
from src.automation.report_runner import generate_reports
from src.automation.model_selector import interactive_select_and_run


def normalize_model_name(model: str) -> str:
    """Normalize model name for benchmark runner."""
    model = (model or "").strip()
    if model == "mock" or model.startswith("ollama:"):
        return model
    return f"ollama:{model}"


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



def ollama_local_name(model: str) -> str:
    """Return the model name without the ollama: prefix."""
    normalized = normalize_model_name(model)
    if normalized.startswith("ollama:"):
        return normalized.split("ollama:", 1)[1]
    return normalized


def find_ollama_executable() -> Optional[Path]:
    """Find ollama executable from PATH or common install locations."""
    found = shutil.which("ollama")
    if found:
        return Path(found)

    candidates: list[Path] = []
    local_appdata = os.environ.get("LOCALAPPDATA")
    program_files = os.environ.get("ProgramFiles")
    program_files_x86 = os.environ.get("ProgramFiles(x86)")

    if local_appdata:
        candidates.extend([
            Path(local_appdata) / "Programs" / "Ollama" / "ollama.exe",
            Path(local_appdata) / "Ollama" / "ollama.exe",
        ])
    if program_files:
        candidates.append(Path(program_files) / "Ollama" / "ollama.exe")
    if program_files_x86:
        candidates.append(Path(program_files_x86) / "Ollama" / "ollama.exe")

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return None


def refresh_ollama_path() -> Optional[Path]:
    """Add the detected Ollama folder to PATH for the current Python process."""
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
    """Ensure Ollama CLI/API is available; optionally install/start it."""
    if check_ollama_api(quiet=True):
        return True

    if start_ollama_server():
        return True

    if allow_install:
        if install_ollama():
            return check_ollama_api(quiet=True) or start_ollama_server()

    print("[FAIL] Ollama API is not available at http://localhost:11434.")
    return False


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
    try:
        installed = get_installed_models()
    except Exception as exc:
        print(f"[WARN] Could not read installed models: {exc}")
        installed = []

    if local_name in installed:
        return True

    print(f"[WARN] Model not installed: {local_name}")
    should_pull = auto_pull or ask_yes_no(f"Download {local_name} now?", default=True)
    if not should_pull:
        return False

    result = pull_model(local_name)
    if result != 0:
        print(f"[FAIL] Failed to pull model: {local_name}")
        return False

    return True

def choose_model_interactively() -> str:
    """Ask user to choose mock or an installed Ollama model."""
    print("\nAvailable choices:")
    print("  0. mock")

    installed = []
    if check_ollama_api(quiet=True):
        try:
            installed = get_installed_models()
        except Exception as exc:  # defensive: wizard should not crash on list failure
            print(f"[WARN] Could not list Ollama models: {exc}")

    for index, model in enumerate(installed, start=1):
        print(f"  {index}. {model}")

    print("  M. Manually type model name")

    choice = ask("Select model", "0")

    if choice.lower() == "m":
        model = normalize_model_name(
            ask("Enter model name, e.g. llama3.2:1b or ollama:llama3.2:1b", "llama3.2:1b")
        )
        if model != "mock" and not ensure_ollama_model_available(model):
            print("[FAIL] Selected model is not available.")
            return "mock"
        return model

    try:
        selected_index = int(choice)
    except ValueError:
        print("[WARN] Invalid selection. Using mock.")
        return "mock"

    if selected_index == 0:
        return "mock"

    if 1 <= selected_index <= len(installed):
        return normalize_model_name(installed[selected_index - 1])

    print("[WARN] Selection out of range. Using mock.")
    return "mock"


def run_wizard() -> int:
    """Interactive no-argument flow: env -> model selection -> benchmark -> report."""
    print("=" * 72)
    print("LLM Secret Guard Test Wizard")
    print("=" * 72)
    print("This wizard will run:")
    print("1. Environment check / preparation")
    print("2. Model selection: single or batch")
    print("3. Benchmark test")
    print("4. Report generation")
    print("=" * 72)

    print("\nStep 1/4: Environment check")
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

    print("\nStep 2/4: Select test mode")
    print("  1. Single model")
    print("  2. Batch models from configs/local_models.json")
    print("  3. Mock model only")
    mode = ask("Choose mode", "1")

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

    print("\nStep 3/4: Run benchmark")
    if mode == "2":
        if not ensure_ollama_ready(allow_install=True):
            print("[FAIL] Ollama is required for batch local model testing.")
            return 1
        code = run_batch_benchmark(
            temperature=temperature,
            max_tokens=max_tokens,
            report_mode=report_mode,
            skip_report=True,
        )
    else:
        model = "mock" if mode == "3" else choose_model_interactively()
        if model != "mock" and not ensure_ollama_model_available(model):
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

    print("\nStep 4/4: Generate report")
    return generate_reports(mode=report_mode)


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
    sub.add_parser("list", help="List local Ollama models")

    pull = sub.add_parser("pull", help="Pull an Ollama model")
    pull.add_argument("model", help="Example: llama3.2:1b")

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

    batch = sub.add_parser("batch", help="Run all enabled models in configs/local_models.json")
    add_common_benchmark_args(batch)
    batch.add_argument("--skip-report", action="store_true", help="Do not generate reports after batch run.")

    report = sub.add_parser("report", help="Generate reports from results/*.csv")
    report.add_argument("--mode", choices=["public", "internal"], default="public", help="Report mode.")

    select = sub.add_parser("select", help="Interactive model selection and run")
    add_common_benchmark_args(select)

    all_cmd = sub.add_parser("all", help="Run env check, batch benchmark, then reports")
    add_common_benchmark_args(all_cmd)

    clean = sub.add_parser("clean", help="Delete generated outputs")
    clean.add_argument("--results", action="store_true", help="Delete CSV files in results/")
    clean.add_argument("--reports", action="store_true", help="Delete generated reports in reports/")
    clean.add_argument("--all", action="store_true", help="Delete results and reports")

    return parser


def clean_outputs(args: argparse.Namespace) -> int:
    delete_results = args.results or args.all
    delete_reports = args.reports or args.all

    if not delete_results and not delete_reports:
        print("[INFO] Nothing selected. Use --results, --reports, or --all.")
        return 0

    if delete_results:
        results_dir = ROOT / "results"
        for path in results_dir.glob("results_*.csv"):
            path.unlink()
            print(f"[DEL] {path}")

    if delete_reports:
        reports_dir = ROOT / "reports"
        for pattern in ("report_*.md", "model_metrics_summary.csv"):
            for path in reports_dir.glob(pattern):
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
        if not ensure_ollama_ready(allow_install=True):
            return 1
        return list_models()

    if args.command == "pull":
        if not ensure_ollama_ready(allow_install=True):
            return 1
        return pull_model(args.model)

    if args.command == "show":
        if not ensure_ollama_ready(allow_install=True):
            return 1
        return show_model(args.model)

    if args.command == "stop":
        if not ensure_ollama_ready(allow_install=False):
            return 1
        return stop_model(args.model)

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
        return run_batch_benchmark(
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            report_mode=args.report_mode,
            skip_report=args.skip_report,
        )

    if args.command == "report":
        return generate_reports(mode=args.mode)

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
        return run_batch_benchmark(
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            report_mode=args.report_mode,
            skip_report=False,
        )

    if args.command == "clean":
        return clean_outputs(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
