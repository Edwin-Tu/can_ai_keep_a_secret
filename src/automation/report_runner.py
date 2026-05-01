from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run_command(cmd: list[str], title: str) -> int:
    print("=" * 72)
    print(title)
    print("=" * 72)
    print("[INFO]", " ".join(cmd))
    return subprocess.call(cmd, cwd=ROOT)


def generate_charts(
    chart_id: str | None = None,
    report_json: str = "results/report.json",
    output_dir: str = "visuals",
    model: str | None = None,
) -> int:
    """Generate benchmark charts from results/report.json.

    When chart_id is None, all discovered chart modules are rendered.
    """
    cmd = [
        sys.executable,
        "src/chart_runner.py",
        "all" if not chart_id else "chart",
    ]

    if chart_id:
        cmd.append(chart_id)

    cmd.extend(["--input", report_json, "--output", output_dir])

    if model:
        cmd.extend(["--model", model])

    return run_command(cmd, "Generate benchmark charts")


def generate_reports(
    mode: str = "public",
    generate_chart_outputs: bool = True,
) -> int:
    """Generate markdown/JSON reports, then optionally generate all chart modules.

    Chart generation is intentionally executed after report generation because
    charts read results/report.json instead of raw CSV files.
    """
    cmd = [sys.executable, "src/report_generator.py", "--report-mode", mode]
    report_code = run_command(cmd, "Generate benchmark reports")

    if report_code != 0:
        return report_code

    if generate_chart_outputs:
        chart_code = generate_charts()
        if chart_code != 0:
            print("[WARN] Chart generation failed, but reports were generated successfully.")

    return report_code
