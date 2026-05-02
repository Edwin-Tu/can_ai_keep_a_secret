from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.charting.context import ChartContext
from src.charting.utils import chart_output_path, model_label, require_models

CHART_ID = "leak_distribution_pie"
CHART_NAME = "Leak Distribution Donut Chart"
DESCRIPTION = "Generate one leak-level distribution donut chart for each selected model."


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _autopct_with_counts(values: list[int]):
    total = sum(values)

    def formatter(percent: float) -> str:
        if total <= 0:
            return ""
        count = round(percent * total / 100)
        return f"{percent:.1f}%\n({count})"

    return formatter


def render(context: ChartContext) -> list[Path]:
    models = context.models()
    require_models(models)

    output_paths: list[Path] = []

    for model in models:
        label = model_label(model)
        distribution = model.get("leak_distribution", []) or []

        visible_items: list[tuple[str, int]] = []
        for item in distribution:
            name = str(item.get("label", "Unknown"))
            level = item.get("leak_level", "?")
            count = _to_int(item.get("count", 0))
            if count > 0:
                visible_items.append((f"L{level} - {name}", count))

        output_path = chart_output_path(context.visuals_dir, CHART_ID, label)
        fig, ax = plt.subplots(figsize=(9, 6))

        if not visible_items:
            ax.text(0.5, 0.5, "No leak distribution data", ha="center", va="center")
            ax.axis("off")
        else:
            labels = [name for name, _ in visible_items]
            counts = [count for _, count in visible_items]
            total = sum(counts)

            wedges, _, _ = ax.pie(
                counts,
                labels=None,
                autopct=_autopct_with_counts(counts),
                startangle=90,
                wedgeprops={"width": 0.42},
            )
            ax.text(0, 0, f"Total\n{total}", ha="center", va="center")
            ax.legend(
                wedges,
                labels,
                title="Leak Level",
                loc="center left",
                bbox_to_anchor=(1.02, 0.5),
            )
            ax.axis("equal")

        ax.set_title(f"Leak Distribution\n{label}")
        fig.tight_layout()
        fig.savefig(output_path, dpi=160, bbox_inches="tight")
        plt.close(fig)
        output_paths.append(output_path)

    return output_paths
