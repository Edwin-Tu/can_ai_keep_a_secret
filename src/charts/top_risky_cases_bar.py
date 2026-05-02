from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.charting.context import ChartContext
from src.charting.utils import chart_output_path, model_label, require_models

CHART_ID = "top_risky_cases_bar"
CHART_NAME = "Top Risky Attack Cases Bar Chart"
DESCRIPTION = "Generate one chart showing the riskiest failed attack cases for each selected model."

MAX_CASES = 8


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


def _case_label(case: dict[str, Any], limit: int = 44) -> str:
    attack_id = str(case.get("attack_id", "unknown")) or "unknown"
    category = str(case.get("category", "unknown")) or "unknown"
    turn = _to_int(case.get("turn_index", 0))
    label = f"{attack_id} T{turn} | {category}" if turn else f"{attack_id} | {category}"
    return label if len(label) <= limit else label[: limit - 3] + "..."


def _risk_value(case: dict[str, Any]) -> float:
    """A visual ranking value. Higher means more urgent to inspect."""
    leak_level = _to_int(case.get("leak_level", 0))
    score = _to_float(case.get("score", 0))
    return leak_level * 10 + max(0.0, 5.0 - score)


def render(context: ChartContext) -> list[Path]:
    models = context.models()
    require_models(models)

    output_paths: list[Path] = []

    for model in models:
        label = model_label(model)
        failed_cases = list(model.get("failed_cases", []) or [])
        failed_cases.sort(
            key=lambda item: (
                _to_int(item.get("leak_level", 0)),
                -_to_float(item.get("score", 0)),
                _risk_value(item),
            ),
            reverse=True,
        )
        top_cases = failed_cases[:MAX_CASES]

        output_path = chart_output_path(context.visuals_dir, CHART_ID, label)
        fig_height = max(5.5, min(12, len(top_cases) * 0.65 + 2))
        fig, ax = plt.subplots(figsize=(11, fig_height))

        if not top_cases:
            ax.text(0.5, 0.5, "No high-risk failed cases found", ha="center", va="center")
            ax.axis("off")
        else:
            labels = [_case_label(case) for case in top_cases]
            values = [_risk_value(case) for case in top_cases]
            y_positions = range(len(top_cases))

            ax.barh(y_positions, values)
            ax.set_yticks(list(y_positions), labels)
            ax.invert_yaxis()
            ax.set_xlabel("Risk Priority Value")
            ax.set_title(f"Top Risky Attack Cases\n{label}")
            ax.grid(axis="x", linestyle="--", linewidth=0.6, alpha=0.6)

            for index, case in enumerate(top_cases):
                leak_level = _to_int(case.get("leak_level", 0))
                score = _to_float(case.get("score", 0))
                result = str(case.get("result", "")) or "N/A"
                note = f"L{leak_level} | score {score:g} | {result}"
                ax.text(values[index] + 0.2, index, note, va="center")

            ax.set_xlim(0, max(values) + 8)

        fig.tight_layout()
        fig.savefig(output_path, dpi=160, bbox_inches="tight")
        plt.close(fig)
        output_paths.append(output_path)

    return output_paths
