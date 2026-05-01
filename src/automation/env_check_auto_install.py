from __future__ import annotations

import importlib
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

# module_name = the import name used by Python
# package_name = the package name used by pip
REQUIRED_PYTHON_MODULES: list[tuple[str, str]] = [
    ("requests", "requests"),
    ("dotenv", "python-dotenv"),
    ("matplotlib", "matplotlib"),
]

OUTPUT_DIRECTORIES = ("results", "reports", "visuals")


def _status(ok: bool, label: str, detail: str = "") -> None:
    prefix = "[OK]" if ok else "[FAIL]"
    msg = f"{prefix} {label}"

    if detail:
        msg += f": {detail}"

    print(msg)


def _check_module(name: str) -> bool:
    importlib.invalidate_caches()
    return importlib.util.find_spec(name) is not None


def _pip_install_package(package_name: str) -> bool:
    """Install one Python package into the current Python environment."""
    print(f"[INFO] Installing missing Python package: {package_name}")
    print(f"[INFO] Command: {sys.executable} -m pip install {package_name}")

    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", package_name],
        cwd=ROOT,
    )

    if result.returncode == 0:
        return True

    print(f"[WARN] pip install failed for package: {package_name}")
    print("[INFO] Trying to bootstrap/upgrade pip with ensurepip...")

    ensurepip_result = subprocess.run(
        [sys.executable, "-m", "ensurepip", "--upgrade"],
        cwd=ROOT,
    )
    if ensurepip_result.returncode != 0:
        print("[FAIL] ensurepip failed. Please install pip manually.")
        return False

    retry_result = subprocess.run(
        [sys.executable, "-m", "pip", "install", package_name],
        cwd=ROOT,
    )
    return retry_result.returncode == 0


def check_python_modules(auto_install: bool = False) -> bool:
    """Check required Python modules and optionally install missing packages."""
    ok = True

    for module_name, package_name in REQUIRED_PYTHON_MODULES:
        installed = _check_module(module_name)

        if not installed and auto_install:
            print(f"[WARN] Python module missing: {module_name}")
            installed = _pip_install_package(package_name)
            # Re-check after install because pip success does not always mean import success.
            installed = installed and _check_module(module_name)

        _status(installed, f"Python module {module_name}")

        if not installed:
            print(f"[INFO] Install with: {sys.executable} -m pip install {package_name}")

        ok = ok and installed

    return ok


def ensure_directories() -> None:
    for folder in OUTPUT_DIRECTORIES:
        path = ROOT / folder
        path.mkdir(exist_ok=True)
        _status(True, f"{folder}/ ready", str(path))


def check_directories() -> bool:
    ok = True
    for folder in OUTPUT_DIRECTORIES:
        path = ROOT / folder
        exists = path.exists()
        _status(exists, f"{folder}/ exists", str(path) if exists else "missing")
        ok = ok and exists
    return ok


def run_env_check(
    fix: bool = False,
    require_ollama: bool = True,
    auto_install_python_deps: bool | None = None,
) -> int:
    """
    Check local environment.

    Important behavior:
    - Ollama API available = local Ollama service is usable.
    - Ollama CLI missing = warning only if API is available.
    - This avoids failing when Ollama is installed/running but not in PATH.
    - When fix=True, missing Python packages are installed into the current
      Python environment using `sys.executable -m pip install ...`.
    """
    if auto_install_python_deps is None:
        auto_install_python_deps = fix

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

    modules_ok = check_python_modules(auto_install=auto_install_python_deps)
    ok = ok and modules_ok

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
