from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.charting.context import ChartContext
from src.charting.utils import chart_output_path, model_label, require_models

CHART_ID = "category_risk_bar"
CHART_NAME = "Category Risk Horizontal Bar Chart"
DESCRIPTION = "Generate one category risk chart for each selected model, sorted by highest leak level."


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _short_label(text: str, limit: int = 34) -> str:
    text = text.strip() or "unknown"
    return text if len(text) <= limit else text[: limit - 3] + "..."


def render(context: ChartContext) -> list[Path]:
    models = context.models()
    require_models(models)

    output_paths: list[Path] = []

    for model in models:
        label = model_label(model)
        category_rows = list(model.get("category_performance", []) or [])
        category_rows.sort(
            key=lambda item: (
                _to_int(item.get("highest_leak_level", 0)),
                _to_int(item.get("fail_count", 0)),
                -_to_float(item.get("average_score", 0)),
            ),
            reverse=True,
        )

        categories = [_short_label(str(item.get("category", "unknown"))) for item in category_rows]
        leak_levels = [_to_int(item.get("highest_leak_level", 0)) for item in category_rows]

        output_path = chart_output_path(context.visuals_dir, CHART_ID, label)
        fig_height = max(6, min(18, len(categories) * 0.48 + 2))
        fig, ax = plt.subplots(figsize=(10, fig_height))

        if not categories:
            ax.text(0.5, 0.5, "No category risk data", ha="center", va="center")
            ax.axis("off")
        else:
            y_positions = range(len(categories))
            ax.barh(y_positions, leak_levels)
            ax.set_yticks(list(y_positions), categories)
            ax.invert_yaxis()
            ax.set_xlim(0, 4)
            ax.set_xlabel("Highest Leak Level (0 = safest, 4 = full leak)")
            ax.set_title(f"Category Risk by Highest Leak Level\n{label}")
            ax.grid(axis="x", linestyle="--", linewidth=0.6, alpha=0.6)

            for index, item in enumerate(category_rows):
                leak_level = _to_int(item.get("highest_leak_level", 0))
                fail_count = _to_int(item.get("fail_count", 0))
                avg_score = _to_float(item.get("average_score", 0))
                risk_level = str(item.get("risk_level", "N/A"))
                note = f"L{leak_level} | fail {fail_count} | avg {avg_score:g} | {risk_level}"
                ax.text(min(leak_level + 0.05, 4.05), index, note, va="center")

        fig.tight_layout()
        fig.savefig(output_path, dpi=160, bbox_inches="tight")
        plt.close(fig)
        output_paths.append(output_path)

    return output_paths
