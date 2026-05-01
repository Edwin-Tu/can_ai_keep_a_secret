from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

from src.charting.context import ChartContext
from src.charting.utils import chart_output_path, model_label, require_models

CHART_ID = "leak_distribution_pie"
CHART_NAME = "Leak Distribution Pie Chart"
DESCRIPTION = "Generate one leak-level distribution pie chart for each model."


def render(context: ChartContext) -> list[Path]:
    models = context.models()
    require_models(models)

    output_paths: list[Path] = []
    for model in models:
        label = model_label(model)
        distribution = model.get("leak_distribution", [])
        labels = [str(item.get("label", "Unknown")) for item in distribution]
        counts = [int(item.get("count", 0) or 0) for item in distribution]

        output_path = chart_output_path(context.visuals_dir, CHART_ID, label)

        fig, ax = plt.subplots(figsize=(8, 6))
        if sum(counts) <= 0:
            ax.text(0.5, 0.5, "No leak distribution data", ha="center", va="center")
            ax.axis("off")
        else:
            visible = [(name, count) for name, count in zip(labels, counts) if count > 0]
            visible_labels = [name for name, _ in visible]
            visible_counts = [count for _, count in visible]
            ax.pie(visible_counts, labels=visible_labels, autopct="%1.1f%%", startangle=90)
            ax.axis("equal")
        ax.set_title(f"Leak Distribution\n{label}")
        fig.tight_layout()
        fig.savefig(output_path, dpi=160)
        plt.close(fig)
        output_paths.append(output_path)

    return output_paths
