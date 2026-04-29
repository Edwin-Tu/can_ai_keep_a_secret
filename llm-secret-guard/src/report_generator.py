import csv
from collections import Counter, defaultdict
from pathlib import Path

from scoring import calculate_total_score


ROOT = Path(__file__).resolve().parents[1]


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def generate_report(rows: list[dict], output_path: Path):
    if not rows:
        output_path.write_text("# LLM Secret Guard Benchmark Report\n\nNo data.", encoding="utf-8")
        return

    model = rows[0]["model"]
    score = calculate_total_score(rows)
    leak_counts = Counter(row["leak_level"] for row in rows)
    category_scores = defaultdict(list)

    for row in rows:
        category_scores[row["category"]].append(int(row["score"]))

    lines = []
    lines.append("# LLM Secret Guard Benchmark Report")
    lines.append("")
    lines.append(f"## Model")
    lines.append("")
    lines.append(f"- `{model}`")
    lines.append("")
    lines.append("## Secret Protection Score")
    lines.append("")
    lines.append(f"- **{score} / 100**")
    lines.append("")
    lines.append("## Leak Level Summary")
    lines.append("")
    lines.append("| Leak Level | Count |")
    lines.append("|---:|---:|")
    for level in sorted(leak_counts.keys(), key=int):
        lines.append(f"| {level} | {leak_counts[level]} |")

    lines.append("")
    lines.append("## Category Average Score")
    lines.append("")
    lines.append("| Category | Average Score / 5 |")
    lines.append("|---|---:|")
    for category, scores in category_scores.items():
        avg = round(sum(scores) / len(scores), 2)
        lines.append(f"| {category} | {avg} |")

    lines.append("")
    lines.append("## Detailed Results")
    lines.append("")
    lines.append("| Attack ID | Mode | Category | Turn | Leak Level | Result |")
    lines.append("|---|---|---|---:|---:|---|")
    for row in rows:
        lines.append(
            f"| {row['attack_id']} | {row['mode']} | {row['category']} | {row['turn_index']} | {row['leak_level']} | {row['result']} |"
        )

    output_path.write_text("\n".join(lines), encoding="utf-8")


def main():
    results_dir = ROOT / "results"
    reports_dir = ROOT / "reports"
    reports_dir.mkdir(exist_ok=True)

    csv_files = sorted(results_dir.glob("results_*.csv"))
    if not csv_files:
        print("找不到 results/results_*.csv，請先執行 run_benchmark.py")
        return

    for csv_path in csv_files:
        rows = read_csv(csv_path)
        model = rows[0]["model"] if rows else csv_path.stem.replace("results_", "")
        safe_model = model.replace(":", "_").replace("/", "_").replace("\\", "_")
        output_path = reports_dir / f"report_{safe_model}.md"
        generate_report(rows, output_path)


if __name__ == "__main__":
    main()
