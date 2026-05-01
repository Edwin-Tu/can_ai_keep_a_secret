from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

from .ollama_tools import (
    check_ollama_api,
    check_ollama_cli,
    find_ollama_executable,
    get_installed_models,
)

ROOT = Path(__file__).resolve().parents[2]

# Tuple format: (module import name, pip package name)
# Example: Python imports `dotenv`, but pip installs `python-dotenv`.
REQUIRED_PYTHON_MODULES: list[tuple[str, str]] = [
    ("requests", "requests"),
    ("dotenv", "python-dotenv"),
    ("matplotlib", "matplotlib"),
]

OUTPUT_DIRECTORIES: tuple[str, ...] = (
    "results",
    "reports",
    "visuals",
)


def _status(ok: bool, label: str, detail: str = "") -> None:
    prefix = "[OK]" if ok else "[FAIL]"
    msg = f"{prefix} {label}"

    if detail:
        msg += f": {detail}"

    print(msg)


def _check_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _run_pip_install(package_name: str) -> bool:
    """Install one Python package into the currently running interpreter."""
    cmd = [sys.executable, "-m", "pip", "install", package_name]
    print(f"[INFO] Installing missing package: {' '.join(cmd)}")

    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode == 0:
        return True

    print(f"[WARN] pip install failed for {package_name}. Trying ensurepip then retrying...")
    ensurepip_result = subprocess.run(
        [sys.executable, "-m", "ensurepip", "--upgrade"],
        cwd=ROOT,
    )
    if ensurepip_result.returncode != 0:
        print("[FAIL] ensurepip failed. Please install pip or Python packages manually.")
        return False

    retry_result = subprocess.run(cmd, cwd=ROOT)
    return retry_result.returncode == 0


def _check_or_install_python_module(
    module_name: str,
    package_name: str,
    fix: bool,
) -> bool:
    """Check one Python module and optionally install the matching pip package."""
    installed = _check_module(module_name)
    _status(installed, f"Python module {module_name}")

    if installed:
        return True

    print(f"[INFO] Install with: {sys.executable} -m pip install {package_name}")

    if not fix:
        return False

    installed_now = _run_pip_install(package_name)
    if not installed_now:
        _status(False, f"Auto-install package {package_name}")
        return False

    # Re-check after installation to avoid false positives.
    rechecked = _check_module(module_name)
    _status(rechecked, f"Python module {module_name} after install")
    return rechecked


def ensure_directories() -> None:
    for folder in OUTPUT_DIRECTORIES:
        path = ROOT / folder
        path.mkdir(exist_ok=True)
        _status(True, f"{folder}/ ready", str(path))


def check_directories() -> bool:
    ok = True
    for folder in OUTPUT_DIRECTORIES:
        exists = (ROOT / folder).exists()
        _status(exists, f"{folder}/ exists")
        ok = ok and exists
    return ok


def run_env_check(fix: bool = False, require_ollama: bool = True) -> int:
    """
    Check local environment.

    Important behavior:
    - fix=True creates required output folders.
    - fix=True auto-installs missing Python packages into the current interpreter.
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
    print(f"[INFO] Python executable: {sys.executable}")

    requirements_path = ROOT / "requirements.txt"
    requirements_ok = requirements_path.exists()
    _status(requirements_ok, "requirements.txt", str(requirements_path))
    ok = ok and requirements_ok

    for module_name, package_name in REQUIRED_PYTHON_MODULES:
        module_ok = _check_or_install_python_module(
            module_name=module_name,
            package_name=package_name,
            fix=fix,
        )
        ok = ok and module_ok

    if fix:
        ensure_directories()
    else:
        ok = check_directories() and ok

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
    print(f" - {sys.executable} -m pip install -r requirements.txt")
    print(" - Install/start Ollama if using local models")
    print(" - python llm_test.py env --fix")
    print(" - If Ollama CLI exists but is not detected, set OLLAMA_EXE manually:")
    print(r'   $env:OLLAMA_EXE="C:\Users\<YOU>\AppData\Local\Programs\Ollama\ollama.exe"')

    return 1
