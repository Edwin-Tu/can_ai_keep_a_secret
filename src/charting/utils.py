from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parents[2]
FONTS_DIR = ROOT / "assets" / "fonts"

# Put a Traditional Chinese font in assets/fonts/ for the most stable output.
# Font files are intentionally not included in this code package.
BUNDLED_CHINESE_FONT_FILES = [
    "NotoSansTC-Regular.ttf",
    "NotoSansTC-Medium.ttf",
    "NotoSansCJKtc-Regular.otf",
    "NotoSansCJK-Regular.ttc",
    "SourceHanSansTC-Regular.otf",
    "TaipeiSansTCBeta-Regular.ttf",
]

SYSTEM_CHINESE_FONT_FAMILIES = [
    "Noto Sans CJK TC",
    "Noto Sans TC",
    "Microsoft JhengHei",
    "PingFang TC",
    "Heiti TC",
    "SimHei",
    "Arial Unicode MS",
]

_CHINESE_FONT_PROP: font_manager.FontProperties | None = None
_CHINESE_FONT_INITIALIZED = False


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


def get_bundled_chinese_font_path() -> Path | None:
    """Return the first bundled Chinese font path if the project provides one."""
    for filename in BUNDLED_CHINESE_FONT_FILES:
        path = FONTS_DIR / filename
        if path.exists():
            return path
    return None


def setup_matplotlib_chinese() -> font_manager.FontProperties | None:
    """Configure matplotlib for stable Traditional Chinese rendering.

    Stable path:
      1. Put a font file such as NotoSansTC-Regular.ttf in assets/fonts/.
      2. This function registers and uses that bundled font.

    Fallback path:
      If no bundled font exists, use common system Chinese font family names.
      This fallback is convenient, but less portable across machines.
    """
    global _CHINESE_FONT_PROP, _CHINESE_FONT_INITIALIZED

    # Avoid broken minus sign rendering in some CJK font environments.
    plt.rcParams["axes.unicode_minus"] = False

    if _CHINESE_FONT_INITIALIZED:
        return _CHINESE_FONT_PROP

    bundled_font_path = get_bundled_chinese_font_path()
    if bundled_font_path:
        font_manager.fontManager.addfont(str(bundled_font_path))
        _CHINESE_FONT_PROP = font_manager.FontProperties(fname=str(bundled_font_path))
        plt.rcParams["font.family"] = _CHINESE_FONT_PROP.get_name()
    else:
        # System fallback. This keeps the chart runnable even before the user
        # adds a bundled font, but the output depends on the host machine.
        plt.rcParams["font.family"] = "sans-serif"
        plt.rcParams["font.sans-serif"] = SYSTEM_CHINESE_FONT_FAMILIES + list(
            plt.rcParams.get("font.sans-serif", [])
        )
        _CHINESE_FONT_PROP = None

    _CHINESE_FONT_INITIALIZED = True
    return _CHINESE_FONT_PROP


def apply_font_to_texts(fig: Any, font_prop: font_manager.FontProperties | None) -> None:
    """Apply bundled font to all existing figure text objects when available."""
    if font_prop is None:
        return

    for text in fig.findobj(match=lambda item: hasattr(item, "set_fontproperties")):
        try:
            text.set_fontproperties(font_prop)
        except Exception:
            # Some matplotlib artists expose set_fontproperties but may not
            # accept updates in every backend/version. Ignore safely.
            continue


def set_title(ax: Any, title: str, font_prop: font_manager.FontProperties | None = None, **kwargs: Any) -> None:
    if font_prop is not None:
        kwargs.setdefault("fontproperties", font_prop)
    ax.set_title(title, **kwargs)


def set_xlabel(ax: Any, label: str, font_prop: font_manager.FontProperties | None = None, **kwargs: Any) -> None:
    if font_prop is not None:
        kwargs.setdefault("fontproperties", font_prop)
    ax.set_xlabel(label, **kwargs)


def set_ylabel(ax: Any, label: str, font_prop: font_manager.FontProperties | None = None, **kwargs: Any) -> None:
    if font_prop is not None:
        kwargs.setdefault("fontproperties", font_prop)
    ax.set_ylabel(label, **kwargs)
