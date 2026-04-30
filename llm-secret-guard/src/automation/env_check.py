from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path

from automation.ollama_tools import check_ollama_cli, check_ollama_api, get_installed_models

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
    """Check local environment without modifying system-level settings."""
    print("=" * 72)
    print("Environment check")
    print("=" * 72)

    ok = True

    py_version = sys.version.split()[0]
    _status(True, "Python", py_version)

    requirements_path = ROOT / "requirements.txt"
    _status(requirements_path.exists(), "requirements.txt", str(requirements_path))
    ok = ok and requirements_path.exists()

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
    _status(config_path.exists(), "configs/local_models.json", str(config_path))
    ok = ok and config_path.exists()

    if require_ollama:
        cli_ok = check_ollama_cli(quiet=True)
        _status(cli_ok, "Ollama CLI", shutil.which("ollama") or "not found")
        ok = ok and cli_ok

        api_ok = check_ollama_api(quiet=True)
        _status(api_ok, "Ollama API", "http://localhost:11434")
        ok = ok and api_ok

        if api_ok:
            models = get_installed_models()
            if models:
                print("[INFO] Installed Ollama models:")
                for model in models:
                    print(f"  - {model}")
            else:
                print("[WARN] Ollama API is available but no models were listed.")

    print("=" * 72)
    if ok:
        print("[OK] Environment check completed.")
        return 0

    print("[FAIL] Environment check found issues.")
    print("Suggested fixes:")
    print("  - pip install -r requirements.txt")
    print("  - Install/start Ollama if using local models")
    print("  - python llm_test.py env --fix")
    return 1
