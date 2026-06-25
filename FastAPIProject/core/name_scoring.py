from __future__ import annotations

from typing import Any


def _clamp_score(value: int) -> int:
    return max(0, min(100, value))


def _text_len(value: str | None) -> int:
    return len((value or "").strip())


def score_name(item: dict[str, Any]) -> dict[str, Any]:
    name = str(item.get("name") or "").strip()
    reference = str(item.get("reference") or "").strip()
    moral = str(item.get("moral") or "").strip()
    domain = str(item.get("domain") or "").strip()
    domain_status = str(item.get("domain_status") or "").strip()

    name_len = _text_len(name)
    rhythm_score = 82
    if 2 <= name_len <= 4:
        rhythm_score += 10
    elif name_len == 1 or 5 <= name_len <= 6:
        rhythm_score += 4
    else:
        rhythm_score -= 8
    if len(set(name)) < name_len:
        rhythm_score -= 6

    meaning_score = 72
    meaning_len = _text_len(moral) + _text_len(reference)
    if meaning_len >= 80:
        meaning_score += 18
    elif meaning_len >= 40:
        meaning_score += 12
    elif meaning_len >= 16:
        meaning_score += 6
    else:
        meaning_score -= 8

    spread_score = 82
    if 2 <= name_len <= 4:
        spread_score += 10
    elif name_len > 6:
        spread_score -= 12
    if any(char in name for char in ("·", " ", "-", "_")):
        spread_score -= 8

    domain_score = 60
    lower_status = domain_status.lower()
    if domain:
        if any(key in domain_status for key in ("可", "未注册", "✅")) or "available" in lower_status:
            domain_score = 92
        elif any(key in domain_status for key in ("已", "抢注", "不可", "❌")) or "taken" in lower_status:
            domain_score = 48
        elif "error" in lower_status or "fail" in lower_status:
            domain_score = 55
        else:
            domain_score = 70

        domain_body = domain.lower().removesuffix(".com")
        if len(domain_body) <= 10:
            domain_score += 4
        elif len(domain_body) >= 16:
            domain_score -= 6

    rhythm_score = _clamp_score(rhythm_score)
    meaning_score = _clamp_score(meaning_score)
    spread_score = _clamp_score(spread_score)
    domain_score = _clamp_score(domain_score)
    score_total = round((rhythm_score + meaning_score + spread_score + domain_score) / 4)

    explanation_parts = [
        f"音律{rhythm_score}分：{_rhythm_reason(name_len)}",
        f"寓意{meaning_score}分：{_meaning_reason(meaning_len)}",
        f"传播性{spread_score}分：{_spread_reason(name_len)}",
        f"域名{domain_score}分：{_domain_reason(domain, domain_status)}",
    ]

    return {
        "score_total": score_total,
        "rhythm_score": rhythm_score,
        "meaning_score": meaning_score,
        "spread_score": spread_score,
        "domain_score": domain_score,
        "score_explanation": "；".join(explanation_parts),
    }


def attach_name_scores(names: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for item in names:
        item.update(score_name(item))
    return names


def _rhythm_reason(name_len: int) -> str:
    if 2 <= name_len <= 4:
        return "字数紧凑，读起来更利落。"
    if name_len == 1:
        return "单字记忆点强，但表达空间有限。"
    return "字数略长，口播时需要更多记忆成本。"


def _meaning_reason(meaning_len: int) -> str:
    if meaning_len >= 80:
        return "解释充分，文化或品牌联想较完整。"
    if meaning_len >= 40:
        return "寓意清晰，有一定延展空间。"
    if meaning_len >= 16:
        return "含义可理解，但还可以补充更具体的意象。"
    return "解释偏短，建议补强来源和寓意。"


def _spread_reason(name_len: int) -> str:
    if 2 <= name_len <= 4:
        return "长度适合搜索、口播和视觉露出。"
    if name_len > 6:
        return "长度偏长，传播时可能不够轻便。"
    return "识别成本较低，适合日常称呼。"


def _domain_reason(domain: str, domain_status: str) -> str:
    if not domain:
        return "未提供域名，按中性分处理。"
    if any(key in domain_status for key in ("可", "未注册", "✅")) or "available" in domain_status.lower():
        return "候选 .com 域名可用性较好。"
    if any(key in domain_status for key in ("已", "抢注", "不可", "❌")) or "taken" in domain_status.lower():
        return "对应 .com 域名可用性偏弱。"
    return "域名状态不明确，建议人工复核。"
