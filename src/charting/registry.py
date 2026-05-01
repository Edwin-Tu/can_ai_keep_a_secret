from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass
from types import ModuleType
from typing import Callable

from src.charting.context import ChartContext

RenderFn = Callable[[ChartContext], list]


@dataclass(frozen=True)
class ChartModule:
    chart_id: str
    name: str
    description: str
    module: ModuleType
    render: RenderFn


def module_to_chart(module: ModuleType) -> ChartModule | None:
    chart_id = getattr(module, "CHART_ID", None)
    render = getattr(module, "render", None)

    if not chart_id or not callable(render):
        return None

    return ChartModule(
        chart_id=str(chart_id),
        name=str(getattr(module, "CHART_NAME", chart_id)),
        description=str(getattr(module, "DESCRIPTION", "")),
        module=module,
        render=render,
    )


def discover_charts() -> list[ChartModule]:
    """Discover chart modules under src/charts without hard-coding filenames."""
    import src.charts as charts

    discovered: list[ChartModule] = []
    for module_info in pkgutil.iter_modules(charts.__path__):
        name = module_info.name
        if name.startswith("_"):
            continue
        module = importlib.import_module(f"charts.{name}")
        chart = module_to_chart(module)
        if chart:
            discovered.append(chart)

    return sorted(discovered, key=lambda item: item.chart_id)


def get_chart(chart_id: str) -> ChartModule | None:
    for chart in discover_charts():
        if chart.chart_id == chart_id:
            return chart
    return None
