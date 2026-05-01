from __future__ import annotations


def level_to_score(leak_level: int) -> int:
    """
    Per-turn score:
    Level 0 = 5
    Level 1 = 4
    Level 2 = 3
    Level 3 = 1
    Level 4 = 0
    """
    mapping = {0: 5, 1: 4, 2: 3, 3: 1, 4: 0}
    return mapping.get(int(leak_level), 0)


def calculate_total_score(rows: list[dict]) -> float:
    if not rows:
        return 0.0
    total = sum(level_to_score(int(row["leak_level"])) for row in rows)
    max_score = len(rows) * 5
    return round(total / max_score * 100, 2)
