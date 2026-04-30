"""
Batch runner for local Ollama models.

This script reads configs/local_models.json and runs src/run_benchmark.py for
all enabled models. It is also used by check.py multi.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def load_local_models() -> list[dict[str, Any]]:
    config_path = ROOT / "configs" / "local_models.json"

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    data = json.loads(config_path.read_text(encoding="utf-8"))

    if not isinstance(data, list):
        raise ValueError("configs/local_models.json must be a list")

    return [item for item in data if item.get("enabled", True)]


def run_benchmark(model_name: str, temperature: float = 0, max_tokens: int | None = None) -> bool:
    cmd = [
        sys.executable,
        "src/run_benchmark.py",
        "--model",
        f"ollama:{model_name}",
        "--temperature",
        str(temperature),
    ]

    if max_tokens is not None and max_tokens > 0:
        cmd.extend(["--max-tokens", str(max_tokens)])

    print("\n" + "=" * 72)
    print("Running:", " ".join(cmd))
    print("=" * 72)

    result = subprocess.run(cmd, cwd=ROOT)
    return result.returncode == 0


def generate_report() -> int:
    print("\nGenerating reports...")
    result = subprocess.run([sys.executable, "src/report_generator.py"], cwd=ROOT)
    return result.returncode


def main() -> int:
    try:
        models = load_local_models()
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    if not models:
        print("[FAIL] No enabled models found in configs/local_models.json")
        return 1

    success: list[str] = []
    failed: list[str] = []

    for index, item in enumerate(models, start=1):
        model = item["name"]
        temperature = float(item.get("temperature", 0))
        max_tokens = item.get("max_tokens", None)

        if max_tokens in ("", 0, "0"):
            max_tokens = None

        print(f"\n[{index}/{len(models)}] {model}")

        if run_benchmark(model, temperature, max_tokens):
            success.append(model)
            print(f"[OK] {model}")
        else:
            failed.append(model)
            print(f"[FAIL] {model}")

    generate_report()

    print("\n" + "=" * 72)
    print("Batch Summary")
    print("=" * 72)
    print(f"Success: {len(success)}")
    for model in success:
        print(f"  [OK] {model}")

    print(f"Failed: {len(failed)}")
    for model in failed:
        print(f"  [FAIL] {model}")

    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
