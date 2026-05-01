from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from .ollama_tools import (
    check_ollama_api,
    check_ollama_cli,
    find_ollama_executable,
    get_installed_models,
)

ROOT = Path(__file__).resolve().parents[2]


def _status(ok: bool, label: str, detail: str = "") -> None:
    prefix = "[OK]" if ok else "[FAIL]"
    msg = f"{prefix} {label}"

    if detail:
        msg += f": {detail}"

    print(msg)


def _check_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def ensure_directories() -> None:
    for folder in ("results", "reports"):
        path = ROOT / folder
        path.mkdir(exist_ok=True)
        _status(True, f"{folder}/ ready", str(path))


def run_env_check(fix: bool = False, require_ollama: bool = True) -> int:
    """
    Check local environment.

    Important behavior:
    - Ollama API available = local Ollama service is usable.
    - Ollama CLI missing = warning only if API is available.
    - This avoids failing when Ollama is installed/running but not in PATH.
    """
    print("=" * 72)
    print("Environment check")
    print("=" * 72)

    ok = True

    py_version = sys.version.split()[0]
    _status(True, "Python", py_version)

    requirements_path = ROOT / "requirements.txt"
    requirements_ok = requirements_path.exists()
    _status(requirements_ok, "requirements.txt", str(requirements_path))
    ok = ok and requirements_ok

    for module in ("requests", "dotenv"):
        installed = _check_module(module)
        _status(installed, f"Python module {module}")
        ok = ok and installed

    if fix:
        ensure_directories()
    else:
        _status((ROOT / "results").exists(), "results/ exists")
        _status((ROOT / "reports").exists(), "reports/ exists")

    config_path = ROOT / "configs" / "local_models.json"
    config_ok = config_path.exists()
    _status(config_ok, "configs/local_models.json", str(config_path))
    ok = ok and config_ok

    if require_ollama:
        cli_ok = check_ollama_cli(quiet=True)
        ollama_exe = find_ollama_executable()

        _status(
            cli_ok,
            "Ollama CLI",
            str(ollama_exe) if ollama_exe else "not found in PATH/common install paths",
        )

        api_ok = check_ollama_api(quiet=True)
        _status(api_ok, "Ollama API", "http://localhost:11434")

        # Benchmark mainly needs Ollama API.
        # CLI missing should not fail the environment check when API is available.
        ok = ok and api_ok

        if api_ok and not cli_ok:
            print("[WARN] Ollama API is available, but CLI was not found.")
            print("[INFO] Benchmark can continue because the local API is working.")
            print("[INFO] CLI-only commands such as pull/show/stop may still need PATH setup.")

        if cli_ok and not api_ok:
            print("[WARN] Ollama CLI exists, but the API is not available.")
            print("[INFO] Open the Ollama app or run `ollama serve`, then retry.")

        if api_ok:
            models = get_installed_models()

            if models:
                print("[INFO] Installed Ollama models:")
                for model in models:
                    print(f" - {model}")
            else:
                print("[WARN] Ollama API is available but no models were listed.")

    print("=" * 72)

    if ok:
        print("[OK] Environment check completed.")
        return 0

    print("[FAIL] Environment check found issues.")
    print("Suggested fixes:")
    print(" - pip install -r requirements.txt")
    print(" - Install/start Ollama if using local models")
    print(" - python llm_test.py env --fix")
    print(" - If Ollama CLI exists but is not detected, set OLLAMA_EXE manually:")
    print(r'   $env:OLLAMA_EXE="C:\Users\<YOU>\AppData\Local\Programs\Ollama\ollama.exe"')

    return 1