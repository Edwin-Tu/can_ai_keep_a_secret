from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ChartContext:
    """Runtime context passed to each chart module."""

    report_json_path: Path
    visuals_dir: Path
    data: dict[str, Any]
    selected_model: str | None = None

    @classmethod
    def from_file(
        cls,
        report_json_path: Path,
        visuals_dir: Path,
        selected_model: str | None = None,
    ) -> "ChartContext":
        report_json_path = report_json_path.resolve()
        visuals_dir = visuals_dir.resolve()

        if not report_json_path.exists():
            raise FileNotFoundError(
                f"Structured report JSON not found: {report_json_path}. "
                "Run `python src/report_generator.py` first."
            )

        data = json.loads(report_json_path.read_text(encoding="utf-8"))
        visuals_dir.mkdir(parents=True, exist_ok=True)

        return cls(
            report_json_path=report_json_path,
            visuals_dir=visuals_dir,
            data=data,
            selected_model=selected_model,
        )

    def models(self) -> list[dict[str, Any]]:
        models = list(self.data.get("models", []))
        if not self.selected_model:
            return models
        return [model for model in models if model.get("model") == self.selected_model]
