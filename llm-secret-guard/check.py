"""
LLM Secret Guard local benchmark control console.

Usage:
    python check.py env
    python check.py list
    python check.py pull qwen2.5:3b
    python check.py test qwen2.5:3b
    python check.py run qwen2.5:3b
    python check.py multi
    python check.py report

Purpose:
    Replace the old PowerShell wrapper with a Python-based control entrypoint.
    This script manages environment checks, Ollama model download, single-model
    benchmark, multi-model benchmark, and report generation.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
OLLAMA_BASE_URL = "http://localhost:11434"


def print_header(title: str) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def run_cmd(cmd: list[str], check: bool = False) -> int:
    print("\n[CMD]", " ".join(cmd))
    result = subprocess.run(cmd, cwd=ROOT)
    if check and result.returncode != 0:
        raise SystemExit(result.returncode)
    return result.returncode


def path_status(relative_path: str) -> bool:
    path = ROOT / relative_path
    ok = path.exists()
    print(f"[{'OK' if ok else 'FAIL'}] {relative_path}")
    return ok


def ollama_api_available() -> bool:
    try:
        with urllib.request.urlopen(f"{OLLAMA_BASE_URL}/api/tags", timeout=5) as response:
            return 200 <= response.status < 300
    except Exception:
        return False


def check_env() -> int:
    print_header("Environment Check")

    print(f"[INFO] Project root: {ROOT}")
    print(f"[INFO] Python: {sys.version.split()[0]}")
    print(f"[INFO] Python executable: {sys.executable}")

    ok = True

    if shutil.which("pip"):
        print("[OK] pip found")
    else:
        print("[FAIL] pip not found")
        ok = False

    required_files = [
        "requirements.txt",
        "src/run_benchmark.py",
        "src/model_client.py",
        "src/leak_detector.py",
        "src/scoring.py",
        "src/report_generator.py",
        "src/clients/mock_client.py",
        "src/clients/ollama_client.py",
        "attacks/attacks.json",
        "data/protected_data.txt",
        "prompts/system_prompt.txt",
        "configs/local_models.json",
    ]

    print_header("Required Files")
    for rel in required_files:
        ok = path_status(rel) and ok

    print_header("Ollama")
    if shutil.which("ollama"):
        print("[OK] ollama command found")
    else:
        print("[FAIL] ollama command not found")
        print("      Please install Ollama first: https://ollama.com")
        ok = False

    if ollama_api_available():
        print(f"[OK] Ollama API available: {OLLAMA_BASE_URL}")
    else:
        print(f"[WARN] Ollama API not reachable: {OLLAMA_BASE_URL}")
        print("       If Ollama is installed, start it and try again.")

    print_header("Python Syntax Check")
    syntax_files = [
        "src/run_benchmark.py",
        "src/model_client.py",
        "src/leak_detector.py",
        "src/scoring.py",
        "src/report_generator.py",
        "src/clients/ollama_client.py",
    ]

    for rel in syntax_files:
        path = ROOT / rel
        if not path.exists():
            continue
        code = run_cmd([sys.executable, "-m", "py_compile", rel], check=False)
        ok = (code == 0) and ok

    print_header("Environment Summary")
    if ok:
        print("[OK] Environment check completed.")
        return 0

    print("[WARN] Environment check completed with issues.")
    return 1


def list_models() -> int:
    print_header("Installed Ollama Models")
    if not shutil.which("ollama"):
        print("[FAIL] ollama command not found")
        return 1
    return run_cmd(["ollama", "list"], check=False)


def pull_model(model: str) -> int:
    print_header(f"Pull Model: {model}")
    if not shutil.which("ollama"):
        print("[FAIL] ollama command not found")
        return 1
    return run_cmd(["ollama", "pull", model], check=False)


def build_benchmark_cmd(model: str, temperature: float = 0, max_tokens: int | None = None) -> list[str]:
    cmd = [
        sys.executable,
        "src/run_benchmark.py",
        "--model",
        f"ollama:{model}",
        "--temperature",
        str(temperature),
    ]

    if max_tokens is not None and max_tokens > 0:
        cmd.extend(["--max-tokens", str(max_tokens)])

    return cmd


def test_model(model: str, temperature: float = 0, max_tokens: int | None = None, generate_report: bool = True) -> int:
    print_header(f"Benchmark Model: {model}")
    code = run_cmd(build_benchmark_cmd(model, temperature, max_tokens), check=False)

    if code != 0:
        print(f"[FAIL] Benchmark failed: {model}")
        return code

    print(f"[OK] Benchmark completed: {model}")

    if generate_report:
        return run_report()

    return 0


def run_model(model: str, temperature: float = 0, max_tokens: int | None = None) -> int:
    print_header(f"Pull + Benchmark + Report: {model}")

    pull_code = pull_model(model)
    if pull_code != 0:
        print(f"[FAIL] Pull failed: {model}")
        return pull_code

    return test_model(model, temperature, max_tokens, generate_report=True)


def run_report() -> int:
    print_header("Generate Reports")
    return run_cmd([sys.executable, "src/report_generator.py"], check=False)


def load_local_models(config_path: Path) -> list[dict[str, Any]]:
    if not config_path.exists():
        raise FileNotFoundError(f"Cannot find config file: {config_path}")

    data = json.loads(config_path.read_text(encoding="utf-8"))

    if not isinstance(data, list):
        raise ValueError("configs/local_models.json must be a list of model objects")

    return data


def run_multi(pull: bool = False, report: bool = True) -> int:
    print_header("Run Multiple Local Models")

    config_path = ROOT / "configs" / "local_models.json"

    try:
        models = load_local_models(config_path)
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    enabled_models = [m for m in models if m.get("enabled", True)]

    if not enabled_models:
        print("[FAIL] No enabled models found in configs/local_models.json")
        return 1

    print(f"[INFO] Enabled models: {len(enabled_models)}")
    for item in enabled_models:
        print(f" - {item.get('name')} ({item.get('description', 'no description')})")

    success: list[str] = []
    failed: list[str] = []

    for index, item in enumerate(enabled_models, start=1):
        model = item["name"]
        temperature = float(item.get("temperature", 0))
        max_tokens = item.get("max_tokens", None)

        if max_tokens in ("", 0, "0"):
            max_tokens = None

        print_header(f"[{index}/{len(enabled_models)}] {model}")

        if pull:
            pull_code = pull_model(model)
            if pull_code != 0:
                failed.append(model)
                continue

        code = test_model(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            generate_report=False,
        )

        if code == 0:
            success.append(model)
        else:
            failed.append(model)

    if report:
        run_report()

    print_header("Multi Model Summary")
    print(f"Success: {len(success)}")
    for model in success:
        print(f"  [OK] {model}")

    print(f"Failed: {len(failed)}")
    for model in failed:
        print(f"  [FAIL] {model}")

    return 0 if not failed else 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="LLM Secret Guard local benchmark control console"
    )

    sub = parser.add_subparsers(dest="command")

    sub.add_parser("env", help="Check Python, project files, and Ollama environment")
    sub.add_parser("list", help="List installed Ollama models")

    p_pull = sub.add_parser("pull", help="Pull one Ollama model")
    p_pull.add_argument("model")

    p_test = sub.add_parser("test", help="Run benchmark for one already-installed Ollama model")
    p_test.add_argument("model")
    p_test.add_argument("--temperature", type=float, default=0)
    p_test.add_argument("--max-tokens", type=int, default=None)

    p_run = sub.add_parser("run", help="Pull one model, run benchmark, and generate report")
    p_run.add_argument("model")
    p_run.add_argument("--temperature", type=float, default=0)
    p_run.add_argument("--max-tokens", type=int, default=None)

    p_multi = sub.add_parser("multi", help="Run benchmarks for configs/local_models.json")
    p_multi.add_argument("--pull", action="store_true", help="Pull each model before running benchmark")
    p_multi.add_argument("--no-report", action="store_true", help="Do not generate report after benchmarks")

    sub.add_parser("report", help="Generate reports from results/results_*.csv")

    args = parser.parse_args()

    if args.command == "env":
        return check_env()
    if args.command == "list":
        return list_models()
    if args.command == "pull":
        return pull_model(args.model)
    if args.command == "test":
        return test_model(args.model, args.temperature, args.max_tokens)
    if args.command == "run":
        return run_model(args.model, args.temperature, args.max_tokens)
    if args.command == "multi":
        return run_multi(pull=args.pull, report=not args.no_report)
    if args.command == "report":
        return run_report()

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
