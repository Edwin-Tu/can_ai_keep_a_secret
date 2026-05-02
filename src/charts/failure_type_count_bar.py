from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.charting.context import ChartContext
from src.charting.utils import chart_output_path, model_label, require_models

CHART_ID = "failure_type_count_bar"
CHART_NAME = "Failure Type Count Bar Chart"
DESCRIPTION = "Generate one failure/leak type count chart for each selected model."


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def render(context: ChartContext) -> list[Path]:
    models = context.models()
    require_models(models)

    output_paths: list[Path] = []

    metric_map = [
        ("Soft Disclosure", "soft_disclosure_count"),
        ("Format Leak", "format_leak_count"),
        ("Partial Leak", "partial_leak_count"),
        ("Full Leak", "full_leak_count"),
    ]

    for model in models:
        label = model_label(model)
        metrics = model.get("metrics", {}) or {}
        labels = [name for name, _ in metric_map]
        counts = [_to_int(metrics.get(key, 0)) for _, key in metric_map]

        output_path = chart_output_path(context.visuals_dir, CHART_ID, label)
        fig, ax = plt.subplots(figsize=(9, 6))

        if sum(counts) <= 0:
            ax.text(0.5, 0.5, "No leak/failure types detected", ha="center", va="center")
            ax.axis("off")
        else:
            x_positions = range(len(labels))
            ax.bar(x_positions, counts)
            ax.set_xticks(list(x_positions), labels, rotation=20, ha="right")
            ax.set_ylabel("Count")
            ax.set_title(f"Failure / Leak Type Counts\n{label}")
            ax.grid(axis="y", linestyle="--", linewidth=0.6, alpha=0.6)

            top = max(counts)
            ax.set_ylim(0, top + max(1, top * 0.18))
            for index, count in enumerate(counts):
                ax.text(index, count, str(count), ha="center", va="bottom")

            total_turns = _to_int(metrics.get("total_test_turns", 0))
            high_risk = _to_int(metrics.get("high_risk_failure_count", 0))
            critical = _to_int(metrics.get("critical_failure_count", 0))
            ax.text(
                0.99,
                0.98,
                f"Total turns: {total_turns}\nHigh-risk: {high_risk}\nCritical: {critical}",
                transform=ax.transAxes,
                ha="right",
                va="top",
            )

        fig.tight_layout()
        fig.savefig(output_path, dpi=160, bbox_inches="tight")
        plt.close(fig)
        output_paths.append(output_path)

    return output_paths
