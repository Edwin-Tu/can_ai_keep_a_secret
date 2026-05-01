from __future__ import annotations

import shutil
import subprocess
from typing import Any

import requests

OLLAMA_BASE_URL = "http://localhost:11434"


def check_ollama_cli(quiet: bool = False) -> bool:
    found = shutil.which("ollama") is not None
    if not quiet:
        print("[OK] Ollama CLI found" if found else "[FAIL] Ollama CLI not found")
    return found


def check_ollama_api(quiet: bool = False, timeout: float = 5) -> bool:
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
    if not check_ollama_cli(quiet=True):
        print("[FAIL] Ollama CLI not found. Please install Ollama first.")
        return 1

    cmd = ["ollama", *args]
    print("[INFO] Running:", " ".join(cmd))
    return subprocess.call(cmd)


def list_models() -> int:
    if not check_ollama_cli(quiet=True):
        print("[FAIL] Ollama CLI not found.")
        return 1
    return subprocess.call(["ollama", "list"])


def pull_model(model: str) -> int:
    return run_ollama_command(["pull", model])


def show_model(model: str) -> int:
    return run_ollama_command(["show", model])


def stop_model(model: str) -> int:
    return run_ollama_command(["stop", model])


def get_installed_models(timeout: float = 5) -> list[str]:
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=timeout)
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        models = data.get("models", [])
        result = []
        for item in models:
            name = item.get("name")
            if name:
                result.append(name)
        return result
    except Exception:
        return []


def model_exists(model: str) -> bool:
    names = get_installed_models()
    plain = model.split("ollama:", 1)[1] if model.startswith("ollama:") else model
    return plain in names or any(name.startswith(plain) for name in names)
