from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run_single_benchmark(model: str, temperature: float = 0, max_tokens: int | None = None) -> int:
    cmd = [
        sys.executable,
        "src/run_benchmark.py",
        "--model",
        model,
        "--temperature",
        str(temperature),
    ]

    if max_tokens is not None and max_tokens > 0:
        cmd.extend(["--max-tokens", str(max_tokens)])

    print("=" * 72)
    print("Run single-model benchmark")
    print("=" * 72)
    print("[INFO]", " ".join(cmd))
    return subprocess.call(cmd, cwd=ROOT)


def run_batch_benchmark(
    temperature: float | None = None,
    max_tokens: int | None = None,
    report_mode: str = "public",
    skip_report: bool = False,
) -> int:
    cmd = [sys.executable, "src/run_all_local_models.py"]

    if temperature is not None:
        cmd.extend(["--temperature", str(temperature)])

    if max_tokens is not None and max_tokens > 0:
        cmd.extend(["--max-tokens", str(max_tokens)])

    if skip_report:
        cmd.append("--skip-report")
    else:
        cmd.extend(["--report-mode", report_mode])

    print("=" * 72)
    print("Run batch benchmark")
    print("=" * 72)
    print("[INFO]", " ".join(cmd))
    return subprocess.call(cmd, cwd=ROOT)
