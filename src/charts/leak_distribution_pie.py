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
    leak_level_label,
    model_display_name,
)
from src.charting.utils import (
    apply_font_to_texts,
    chart_output_path,
    model_label,
    require_models,
    set_title,
    setup_matplotlib_chinese,
)

CHART_ID = "leak_distribution_pie"
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
        distribution = model.get("leak_distribution", []) or []

        labels = [
            leak_level_label(item.get("leak_level"), str(item.get("label", "未知")))
            for item in distribution
        ]
        counts = [_to_int(item.get("count", 0)) for item in distribution]

        output_path = chart_output_path(context.visuals_dir, CHART_ID, raw_model_name)
        fig, ax = plt.subplots(figsize=(8.5, 6.5))

        if sum(counts) <= 0:
            ax.text(0.5, 0.5, NO_DATA_TEXT_ZH["leak_distribution"], ha="center", va="center")
            ax.axis("off")
        else:
            visible = [(name, count) for name, count in zip(labels, counts) if count > 0]
            visible_labels = [name for name, _ in visible]
            visible_counts = [count for _, count in visible]

            wedges, text_items, autotexts = ax.pie(
                visible_counts,
                labels=visible_labels,
                autopct="%1.1f%%",
                startangle=90,
                pctdistance=0.78,
                wedgeprops={"width": 0.42, "edgecolor": "white"},
            )
            ax.text(0, 0, f"總數\n{sum(visible_counts)}", ha="center", va="center", fontsize=13)
            ax.axis("equal")

            for item in [*text_items, *autotexts]:
                if font_prop is not None:
                    item.set_fontproperties(font_prop)

        set_title(ax, f"{CHART_NAME}\n{display_name}", font_prop=font_prop, fontsize=15, pad=18)
        apply_font_to_texts(fig, font_prop)
        fig.tight_layout()
        fig.savefig(output_path, dpi=160, bbox_inches="tight")
        plt.close(fig)
        output_paths.append(output_path)

    return output_paths
