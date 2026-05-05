from __future__ import annotations

from typing import Any

CHART_TITLES_ZH = {
    "leak_distribution_pie": "洩漏等級分布圖",
    "category_risk_bar": "攻擊類型風險圖",
    "failure_type_count_bar": "失敗類型數量圖",
    "top_risky_cases_bar": "高風險案例圖",
}

CHART_DESCRIPTIONS_ZH = {
    "leak_distribution_pie": "以甜甜圈圖顯示模型在各洩漏等級的分布。",
    "category_risk_bar": "以橫向長條圖顯示各攻擊類型的最高洩漏等級。",
    "failure_type_count_bar": "以長條圖顯示各類洩漏與失敗類型的數量。",
    "top_risky_cases_bar": "以橫向長條圖列出最需要優先檢查的高風險攻擊案例。",
}

LEAK_LEVEL_LABELS_ZH = {
    0: "安全拒絕 / 無洩漏",
    1: "輕微揭露",
    2: "格式洩漏",
    3: "部分洩漏",
    4: "完整洩漏",
}

FAILURE_TYPE_LABELS_ZH = {
    "soft_disclosure_count": "輕微揭露",
    "format_leak_count": "格式洩漏",
    "partial_leak_count": "部分洩漏",
    "full_leak_count": "完整洩漏",
}

CATEGORY_LABELS_ZH = {
    "direct_request": "直接要求",
    "role_play": "角色扮演",
    "instruction_override": "指令覆蓋",
    "system_prompt_extraction": "系統提示詞抽取",
    "encoding_bypass": "編碼繞過",
    "partial_disclosure": "片段誘導揭露",
    "translation_bypass": "翻譯繞過",
    "structured_output": "結構化輸出誘導",
    "log_access": "日誌存取誘導",
    "multi_turn_probe": "多輪探測",
    "policy_confusion": "規則混淆",
    "indirect_prompt_injection": "間接提示注入",
    "format_smuggling": "格式走私",
    "output_constraint_bypass": "輸出限制繞過",
    "reasoning_trap": "推理陷阱",
    "refusal_suppression": "拒絕抑制",
    "persona_override": "人格覆寫",
    "data_reconstruction": "資料重建",
    "cross_language_injection": "跨語言注入",
    "homoglyph_obfuscation": "同形字混淆",
}

RESULT_LABELS_ZH = {
    "pass": "通過",
    "passed": "通過",
    "fail": "失敗",
    "failed": "失敗",
    "clean_refusal": "安全拒絕",
    "soft_disclosure": "輕微揭露",
    "format_leak": "格式洩漏",
    "partial_leak": "部分洩漏",
    "full_leak": "完整洩漏",
}

NO_DATA_TEXT_ZH = {
    "leak_distribution": "沒有洩漏分布資料",
    "category_performance": "沒有攻擊類型資料",
    "failure_type": "未偵測到洩漏或失敗類型",
    "top_risky_cases": "沒有高風險失敗案例",
}


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def leak_level_label(value: Any, fallback: str = "未知") -> str:
    level = _to_int(value, default=-1)
    if level in LEAK_LEVEL_LABELS_ZH:
        return LEAK_LEVEL_LABELS_ZH[level]
    return fallback or "未知"


def category_label(value: Any) -> str:
    raw = str(value or "unknown")
    return CATEGORY_LABELS_ZH.get(raw, raw.replace("_", " "))


def result_label(value: Any) -> str:
    raw = str(value or "N/A")
    key = raw.strip().lower().replace(" ", "_")
    return RESULT_LABELS_ZH.get(key, raw)


def model_display_name(model_name: str) -> str:
    return model_name.replace("ollama:", "Ollama：")
