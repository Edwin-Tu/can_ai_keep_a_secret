from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

from src.charting.context import ChartContext
from src.charting.utils import chart_output_path, model_label, require_models

CHART_ID = "model_score_bar"
CHART_NAME = "Model Score Bar Chart"
DESCRIPTION = "Compare Secret Protection Score across models."


def render(context: ChartContext) -> list[Path]:
    models = context.models()
    require_models(models)

    labels = [model_label(model) for model in models]
    scores = [float(model.get("score", 0) or 0) for model in models]

    output_path = chart_output_path(
        context.visuals_dir,
        CHART_ID,
        context.selected_model if context.selected_model else None,
    )

    fig_width = max(8, min(18, len(labels) * 1.6))
    fig, ax = plt.subplots(figsize=(fig_width, 6))
    ax.bar(labels, scores)
    ax.set_title("Secret Protection Score by Model")
    ax.set_ylabel("Score / 100")
    ax.set_ylim(0, 100)
    ax.tick_params(axis="x", rotation=35)

    for index, score in enumerate(scores):
        ax.text(index, min(score + 2, 100), f"{score:g}", ha="center", va="bottom")

    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)

    return [output_path]
