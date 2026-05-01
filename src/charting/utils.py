from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def safe_filename(value: str) -> str:
    text = value.strip() or "unknown"
    text = re.sub(r"[^A-Za-z0-9._-]+", "_", text)
    return text.strip("_") or "unknown"


def chart_output_path(visuals_dir: Path, chart_id: str, suffix: str | None = None) -> Path:
    if suffix:
        return visuals_dir / f"{chart_id}_{safe_filename(suffix)}.png"
    return visuals_dir / f"{chart_id}.png"


def model_label(model: dict[str, Any]) -> str:
    return str(model.get("model", "unknown"))


def require_models(models: list[dict[str, Any]]) -> None:
    if not models:
        raise ValueError("No matching model data found in results/report.json.")
