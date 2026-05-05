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
    FAILURE_TYPE_LABELS_ZH,
    NO_DATA_TEXT_ZH,
    model_display_name,
)
from src.charting.utils import (
    apply_font_to_texts,
    chart_output_path,
    model_label,
    require_models,
    set_ylabel,
    set_title,
    setup_matplotlib_chinese,
)

CHART_ID = "failure_type_count_bar"
CHART_NAME = CHART_TITLES_ZH[CHART_ID]
DESCRIPTION = CHART_DESCRIPTIONS_ZH[CHART_ID]


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def render(context: ChartContext) -> list[Path]:
    models = context.models()
    require_models(models)

    font_prop = setup_matplotlib_chinese()
    output_paths: list[Path] = []
    metric_keys = [
        "soft_disclosure_count",
        "format_leak_count",
        "partial_leak_count",
        "full_leak_count",
    ]

    for model in models:
        raw_model_name = model_label(model)
        display_name = model_display_name(raw_model_name)
        metrics = model.get("metrics", {}) or {}
        labels = [FAILURE_TYPE_LABELS_ZH[key] for key in metric_keys]
        counts = [_to_int(metrics.get(key, 0)) for key in metric_keys]

        output_path = chart_output_path(context.visuals_dir, CHART_ID, raw_model_name)
        fig, ax = plt.subplots(figsize=(9.5, 6.2))

        if sum(counts) <= 0:
            ax.text(0.5, 0.5, NO_DATA_TEXT_ZH["failure_type"], ha="center", va="center")
            ax.axis("off")
        else:
            x_positions = range(len(labels))
            ax.bar(x_positions, counts)
            ax.set_xticks(list(x_positions), labels, rotation=15, ha="right")
            set_ylabel(ax, "數量", font_prop=font_prop)
            ax.grid(axis="y", linestyle="--", linewidth=0.6, alpha=0.6)

            top = max(counts)
            ax.set_ylim(0, top + max(1, top * 0.22))
            for index, count in enumerate(counts):
                ax.text(index, count, str(count), ha="center", va="bottom")

            total_turns = _to_int(metrics.get("total_test_turns", 0))
            high_risk = _to_int(metrics.get("high_risk_failure_count", 0))
            critical = _to_int(metrics.get("critical_failure_count", 0))
            ax.text(
                0.99,
                0.98,
                f"總測試輪次：{total_turns}\n高風險失敗：{high_risk}\n嚴重失敗：{critical}",
                transform=ax.transAxes,
                ha="right",
                va="top",
            )

        set_title(ax, f"{CHART_NAME}\n{display_name}", font_prop=font_prop, fontsize=15, pad=16)
        apply_font_to_texts(fig, font_prop)
        fig.tight_layout()
        fig.savefig(output_path, dpi=160, bbox_inches="tight")
        plt.close(fig)
        output_paths.append(output_path)

    return output_paths
