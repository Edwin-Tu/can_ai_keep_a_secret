from __future__ import annotations

import argparse
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


def normalize_max_tokens(value: Any) -> int | None:
    if value in (None, "", 0, "0"):
        return None

    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None

    return parsed if parsed > 0 else None


def normalize_model_name(model_name: str) -> str:
    if model_name == "mock" or model_name.startswith("ollama:"):
        return model_name

    return f"ollama:{model_name}"


def run_benchmark(
    model_name: str,
    temperature: float = 0,
    max_tokens: int | None = None,
) -> bool:
    cmd = [
        sys.executable,
        "src/run_benchmark.py",
        "--model",
        normalize_model_name(model_name),
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


def generate_report(report_mode: str = "public") -> int:
    print("\nGenerating reports...")

    result = subprocess.run(
        [
            sys.executable,
            "src/report_generator.py",
            "--report-mode",
            report_mode,
        ],
        cwd=ROOT,
    )

    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run benchmarks for all enabled local Ollama models"
    )

    parser.add_argument(
        "--temperature",
        type=float,
        default=None,
        help="Override temperature for all models",
    )

    parser.add_argument(
        "--max-tokens",
        type=int,
        default=None,
        help="Override max tokens. Omit or <=0 for unlimited/model default.",
    )

    parser.add_argument(
        "--skip-report",
        action="store_true",
        help="Do not generate reports after the batch run",
    )

    parser.add_argument(
        "--report-mode",
        choices=["public", "internal"],
        default="public",
    )

    args = parser.parse_args()

    try:
        models = load_local_models()
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    if not models:
        print("[INFO] No enabled local models found in configs/local_models.json.")
        print("[INFO] This is valid for a fresh/default setup.")
        print("[INFO] Add models to configs/local_models.json when you want batch testing.")
        return 0

    success: list[str] = []
    failed: list[str] = []

    for index, item in enumerate(models, start=1):
        model = item["name"]

        temperature = (
            args.temperature
            if args.temperature is not None
            else float(item.get("temperature", 0))
        )

        max_tokens = normalize_max_tokens(
            args.max_tokens
            if args.max_tokens is not None
            else item.get("max_tokens", None)
        )

        print(f"\n[{index}/{len(models)}] {model}")
        print(f"Temperature: {temperature}")
        print(
            "Max tokens:",
            max_tokens if max_tokens is not None else "unlimited / model default",
        )

        if run_benchmark(model, temperature, max_tokens):
            success.append(model)
            print(f"[OK] {model}")
        else:
            failed.append(model)
            print(f"[FAIL] {model}")

    if not args.skip_report:
        generate_report(args.report_mode)

    print("\n" + "=" * 72)
    print("Batch Summary")
    print("=" * 72)

    print(f"Success: {len(success)}")
    for model in success:
        print(f" [OK] {model}")

    print(f"Failed: {len(failed)}")
    for model in failed:
        print(f" [FAIL] {model}")

    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())