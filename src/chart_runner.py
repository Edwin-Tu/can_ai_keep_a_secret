from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from src.charting.context import ChartContext
from src.charting.registry import ChartModule, discover_charts, get_chart


def print_chart_list(charts: list[ChartModule]) -> None:
    if not charts:
        print("No chart modules found in src/charts/.")
        return

    print("Available charts:")
    for chart in charts:
        print(f"- {chart.chart_id}: {chart.name}")
        if chart.description:
            print(f"  {chart.description}")


def render_chart(chart: ChartModule, context: ChartContext) -> bool:
    print(f"[CHART] {chart.chart_id} - {chart.name}")
    try:
        output_paths = chart.render(context)
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        print(f"[FAIL] {chart.chart_id}: {exc}")
        return False

    if not output_paths:
        print(f"[WARN] {chart.chart_id}: no files were generated.")
        return True

    for output_path in output_paths:
        print(f"[OK] {output_path}")
    return True


def render_all(context: ChartContext) -> int:
    charts = discover_charts()
    if not charts:
        print("[WARN] No chart modules found in src/charts/.")
        return 0

    failed: list[str] = []
    for chart in charts:
        if not render_chart(chart, context):
            failed.append(chart.chart_id)

    if failed:
        print("[FAIL] Some charts failed:")
        for chart_id in failed:
            print(f"  - {chart_id}")
        return 1

    print(f"[OK] Generated {len(charts)} chart module(s).")
    return 0


def render_single(chart_id: str, context: ChartContext) -> int:
    chart = get_chart(chart_id)
    if not chart:
        print(f"[FAIL] Unknown chart id: {chart_id}")
        print_chart_list(discover_charts())
        return 1
    return 0 if render_chart(chart, context) else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate modular benchmark charts from results/report.json",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command")

    list_cmd = sub.add_parser("list", help="List discovered chart modules")
    list_cmd.set_defaults(command="list")

    all_cmd = sub.add_parser("all", help="Generate all discovered chart modules")
    all_cmd.add_argument("--input", default="results/report.json", help="Input structured report JSON path")
    all_cmd.add_argument("--output", default="visuals", help="Chart output directory")
    all_cmd.add_argument("--model", default=None, help="Optional model filter")

    chart_cmd = sub.add_parser("chart", help="Generate one chart module by chart id")
    chart_cmd.add_argument("chart_id", help="Chart id, for example: leak_distribution_pie")
    chart_cmd.add_argument("--input", default="results/report.json", help="Input structured report JSON path")
    chart_cmd.add_argument("--output", default="visuals", help="Chart output directory")
    chart_cmd.add_argument("--model", default=None, help="Optional model filter")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command in (None, "list"):
        print_chart_list(discover_charts())
        return 0

    input_path = Path(args.input)
    output_dir = Path(args.output)
    if not input_path.is_absolute():
        input_path = ROOT / input_path
    if not output_dir.is_absolute():
        output_dir = ROOT / output_dir

    context = ChartContext.from_file(
        report_json_path=input_path,
        visuals_dir=output_dir,
        selected_model=args.model,
    )

    if args.command == "all":
        return render_all(context)

    if args.command == "chart":
        return render_single(args.chart_id, context)

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
