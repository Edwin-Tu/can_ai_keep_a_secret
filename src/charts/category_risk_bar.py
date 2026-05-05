from __future__ import annotations

from pathlib import Path

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

CHART_ID = "category_risk_bar"
CHART_NAME = CHART_TITLES_ZH[CHART_ID]
DESCRIPTION = CHART_DESCRIPTIONS_ZH[CHART_ID]


def _to_int(value: object, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def render(context: ChartContext) -> list[Path]:
    models = context.models()
    require_models(models)

    font_prop = setup_matplotlib_chinese()
    output_paths: list[Path] = []

    for model in models:
        raw_model_name = model_label(model)
        display_name = model_display_name(raw_model_name)
        category_rows = list(model.get("category_performance", []) or [])
        category_rows.sort(
            key=lambda item: (
                _to_int(item.get("highest_leak_level", 0)),
                _to_int(item.get("fail_count", 0)),
                _to_int(item.get("test_count", 0)),
            ),
            reverse=True,
        )

        categories = [category_label(item.get("category", "unknown")) for item in category_rows]
        leak_levels = [_to_int(item.get("highest_leak_level", 0)) for item in category_rows]

        output_path = chart_output_path(context.visuals_dir, CHART_ID, raw_model_name)
        fig_height = max(6, min(18, len(categories) * 0.45 + 2.5))
        fig, ax = plt.subplots(figsize=(10.5, fig_height))

        if not categories:
            ax.text(0.5, 0.5, NO_DATA_TEXT_ZH["category_performance"], ha="center", va="center")
            ax.axis("off")
        else:
            y_positions = range(len(categories))
            ax.barh(y_positions, leak_levels)
            ax.set_yticks(list(y_positions), categories)
            ax.invert_yaxis()
            ax.set_xlim(0, 4)
            set_xlabel(ax, "最高洩漏等級（0=安全，4=完整洩漏）", font_prop=font_prop)
            ax.grid(axis="x", linestyle="--", linewidth=0.6, alpha=0.6)

            for index, item in enumerate(category_rows):
                level = _to_int(item.get("highest_leak_level", 0))
                fail_count = _to_int(item.get("fail_count", 0))
                test_count = _to_int(item.get("test_count", 0))
                note = f"L{level}｜失敗 {fail_count}/{test_count}"
                ax.text(level + 0.05, index, note, va="center")

        set_title(ax, f"{CHART_NAME}\n{display_name}", font_prop=font_prop, fontsize=15, pad=16)
        apply_font_to_texts(fig, font_prop)
        fig.tight_layout()
        fig.savefig(output_path, dpi=160, bbox_inches="tight")
        plt.close(fig)
        output_paths.append(output_path)

    return output_paths
