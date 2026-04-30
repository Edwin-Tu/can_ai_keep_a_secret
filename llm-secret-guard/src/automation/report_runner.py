from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def generate_reports(mode: str = "public") -> int:
    cmd = [sys.executable, "src/report_generator.py", "--report-mode", mode]
    print("=" * 72)
    print("Generate benchmark reports")
    print("=" * 72)
    print("[INFO]", " ".join(cmd))
    return subprocess.call(cmd, cwd=ROOT)
