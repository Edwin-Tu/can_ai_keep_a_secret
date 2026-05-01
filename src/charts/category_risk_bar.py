from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

from src.charting.context import ChartContext
from src.charting.utils import chart_output_path, model_label, require_models

CHART_ID = "category_risk_bar"
CHART_NAME = "Category Risk Bar Chart"
DESCRIPTION = "Generate one category highest-leak-level bar chart for each model."


def render(context: ChartContext) -> list[Path]:
    models = context.models()
    require_models(models)

    output_paths: list[Path] = []
    for model in models:
        label = model_label(model)
        category_rows = model.get("category_performance", [])
        categories = [str(item.get("category", "unknown")) for item in category_rows]
        leak_levels = [int(item.get("highest_leak_level", 0) or 0) for item in category_rows]

        output_path = chart_output_path(context.visuals_dir, CHART_ID, label)

        fig_width = max(9, min(20, len(categories) * 1.4))
        fig, ax = plt.subplots(figsize=(fig_width, 6))
        if not categories:
            ax.text(0.5, 0.5, "No category data", ha="center", va="center")
            ax.axis("off")
        else:
            ax.bar(categories, leak_levels)
            ax.set_ylim(0, 4)
            ax.set_ylabel("Highest Leak Level")
            ax.set_xlabel("Attack Category")
            ax.tick_params(axis="x", rotation=35)
        ax.set_title(f"Category Risk by Highest Leak Level\n{label}")
        fig.tight_layout()
        fig.savefig(output_path, dpi=160)
        plt.close(fig)
        output_paths.append(output_path)

    return output_paths
