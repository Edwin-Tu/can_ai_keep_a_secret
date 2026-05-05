from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Optional

import requests

OLLAMA_BASE_URL = "http://localhost:11434"


def find_ollama_executable() -> Optional[Path]:
    """
    Find the Ollama executable from:
    1. OLLAMA_EXE environment variable
    2. PATH
    3. Common Windows install locations
    """
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
    """
    Add detected Ollama folder to PATH for the current Python process.

    This does not permanently modify Windows PATH.
    It only helps the current script find ollama.exe.
    """
    exe = find_ollama_executable()
    if not exe:
        return None

    folder = str(exe.parent)
    current_path = os.environ.get("PATH", "")
    path_parts = [
        p.strip().lower()
        for p in current_path.split(os.pathsep)
        if p.strip()
    ]

    if folder.lower() not in path_parts:
        os.environ["PATH"] = folder + os.pathsep + current_path

    return exe


def check_ollama_cli(quiet: bool = False) -> bool:
    """
    Check whether Ollama CLI exists.

    This checks PATH and common install locations.
    """
    exe = refresh_ollama_path()
    found = exe is not None

    if not quiet:
        if found:
            print(f"[OK] Ollama CLI found: {exe}")
        else:
            print("[FAIL] Ollama CLI not found")

    return found


def check_ollama_api(quiet: bool = False, timeout: float = 5) -> bool:
    """
    Check whether Ollama local API is available.

    For benchmark execution, API availability is more important than
    whether the CLI is visible in PATH.
    """
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=timeout)
        response.raise_for_status()

        if not quiet:
            print(f"[OK] Ollama API available: {OLLAMA_BASE_URL}")

        return True

    except Exception as exc:
        if not quiet:
            print(f"[FAIL] Ollama API unavailable: {exc}")

        return False


def run_ollama_command(args: list[str]) -> int:
    """
    Run an Ollama CLI command.

    Example:
        run_ollama_command(["pull", "llama3.2:1b"])
    """
    exe = refresh_ollama_path()

    if not exe:
        print("[FAIL] Ollama CLI not found.")
        print("[INFO] If Ollama is installed, try setting OLLAMA_EXE manually:")
        print(r'       $env:OLLAMA_EXE="C:\Users\<YOU>\AppData\Local\Programs\Ollama\ollama.exe"')
        return 1

    cmd = [str(exe), *args]
    print("[INFO] Running:", " ".join(cmd))
    return subprocess.call(cmd)


def list_models() -> int:
    """
    List local Ollama models.

    If CLI is available, use `ollama list`.
    If CLI is not available but API is available, fall back to /api/tags.
    """
    exe = refresh_ollama_path()

    if exe:
        return subprocess.call([str(exe), "list"])

    if check_ollama_api(quiet=True):
        models = get_installed_models()

        if not models:
            print("[INFO] Ollama API is available, but no local models were found.")
            return 0

        print("NAME")
        for model in models:
            print(model)

        return 0

    print("[FAIL] Ollama CLI not found and Ollama API is unavailable.")
    return 1


def pull_model(model: str) -> int:
    return run_ollama_command(["pull", model])


def show_model(model: str) -> int:
    return run_ollama_command(["show", model])


def stop_model(model: str) -> int:
    return run_ollama_command(["stop", model])


def get_installed_models(timeout: float = 5) -> list[str]:
    """
    Get installed Ollama model names from the local API.
    """
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=timeout)
        response.raise_for_status()

        data: dict[str, Any] = response.json()
        models = data.get("models", [])

        result: list[str] = []

        for item in models:
            name = item.get("name")
            if name:
                result.append(name)

        return result

    except Exception:
        return []


def model_exists(model: str) -> bool:
    """
    Check whether a model exists locally.

    Accepts both:
        qwen2.5:3b
        ollama:qwen2.5:3b
    """
    names = get_installed_models()
    plain = model.split("ollama:", 1)[1] if model.startswith("ollama:") else model

    return plain in names or any(name == plain or name.startswith(f"{plain}:") for name in names)