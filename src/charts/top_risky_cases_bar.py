from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.charting.context import ChartContext
from src.charting.labels_zh import (
    CHART_DESCRIPTIONS_ZH,
    CHART_TITLES_ZH,
    NO_DATA_TEXT_ZH,
    category_label,
    model_display_name,
    result_label,
)
from src.charting.utils import (
    apply_font_to_texts,
    chart_output_path,
    model_label,
    require_models,
    set_xlabel,
    set_title,
    setup_matplotlib_chinese,
)

CHART_ID = "top_risky_cases_bar"
CHART_NAME = CHART_TITLES_ZH[CHART_ID]
DESCRIPTION = CHART_DESCRIPTIONS_ZH[CHART_ID]
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


def _case_label(case: dict[str, Any], limit: int = 34) -> str:
    attack_id = str(case.get("attack_id", "unknown")) or "unknown"
    category = category_label(case.get("category", "unknown"))
    turn = _to_int(case.get("turn_index", 0))
    label = f"{attack_id} 第{turn}輪｜{category}" if turn else f"{attack_id}｜{category}"
    return label if len(label) <= limit else label[: limit - 3] + "..."


def _risk_value(case: dict[str, Any]) -> float:
    """Higher means more urgent to inspect."""
    leak_level = _to_int(case.get("leak_level", 0))
    score = _to_float(case.get("score", 0))
    return leak_level * 10 + max(0.0, 5.0 - score)


def render(context: ChartContext) -> list[Path]:
    models = context.models()
    require_models(models)

    font_prop = setup_matplotlib_chinese()
    output_paths: list[Path] = []

    for model in models:
        raw_model_name = model_label(model)
        display_name = model_display_name(raw_model_name)
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

        output_path = chart_output_path(context.visuals_dir, CHART_ID, raw_model_name)
        fig_height = max(5.8, min(12, len(top_cases) * 0.72 + 2.2))
        fig, ax = plt.subplots(figsize=(11.5, fig_height))

        if not top_cases:
            ax.text(0.5, 0.5, NO_DATA_TEXT_ZH["top_risky_cases"], ha="center", va="center")
            ax.axis("off")
        else:
            labels = [_case_label(case) for case in top_cases]
            values = [_risk_value(case) for case in top_cases]
            y_positions = range(len(top_cases))

            ax.barh(y_positions, values)
            ax.set_yticks(list(y_positions), labels)
            ax.invert_yaxis()
            set_xlabel(ax, "風險優先值（越高越需要優先檢查）", font_prop=font_prop)
            ax.grid(axis="x", linestyle="--", linewidth=0.6, alpha=0.6)

            for index, case in enumerate(top_cases):
                leak_level = _to_int(case.get("leak_level", 0))
                score = _to_float(case.get("score", 0))
                result = result_label(case.get("result", "N/A"))
                note = f"L{leak_level}｜分數 {score:g}｜{result}"
                ax.text(values[index] + 0.2, index, note, va="center")

            ax.set_xlim(0, max(values) + 9)

        set_title(ax, f"{CHART_NAME}\n{display_name}", font_prop=font_prop, fontsize=15, pad=16)
        apply_font_to_texts(fig, font_prop)
        fig.tight_layout()
        fig.savefig(output_path, dpi=160, bbox_inches="tight")
        plt.close(fig)
        output_paths.append(output_path)

    return output_paths
