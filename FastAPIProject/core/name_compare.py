from models.name_history import NameHistory
from schemas.history_schemas import NameCompareItemOut, NameCompareRankOut
from repository.history_repo import _decode_domain_checks


def clamp_score(value: int | None) -> int:
    return max(0, min(100, int(value or 0)))


def build_compare_score(item: NameHistory) -> int:
    if item.score_total:
        return clamp_score(item.score_total)

    weighted_score = (
        clamp_score(item.rhythm_score) * 0.25
        + clamp_score(item.meaning_score) * 0.35
        + clamp_score(item.spread_score) * 0.25
        + clamp_score(item.domain_score) * 0.15
    )
    return round(weighted_score)


def _is_domain_available(domain_status: str | None) -> bool:
    status = (domain_status or "").lower()
    available_keywords = ["available", "可注册", "未注册", "可以注册"]
    return any(keyword in status for keyword in available_keywords)


def _build_suitable_scenes(item: NameHistory) -> list[str]:
    scenes: list[str] = []
    requirement = item.other or ""

    if item.category == "人名":
        scenes.append("适合重视寓意、音律和日常称呼自然度的个人起名场景")
        if item.gender and item.gender != "不限":
            scenes.append(f"适合偏{item.gender}气质的姓名选择")
    elif item.category == "企业名":
        scenes.append("适合品牌命名、工商核名初筛和传播素材延展")
        if item.domain:
            scenes.append("适合需要同步评估 .com 域名的品牌方案")
    else:
        scenes.append("适合宠物呼唤、社交分享和家庭成员共同使用")

    if requirement:
        scenes.append(f"贴合原始诉求：{requirement}")
    if _is_domain_available(item.domain_status):
        scenes.append("域名状态更利于后续线上品牌落地")

    return scenes[:4]


def _build_strengths(item: NameHistory) -> list[str]:
    metrics = [
        ("音律", clamp_score(item.rhythm_score)),
        ("寓意", clamp_score(item.meaning_score)),
        ("传播性", clamp_score(item.spread_score)),
        ("域名", clamp_score(item.domain_score)),
    ]
    strengths = [f"{label}表现突出" for label, score in metrics if score >= 85]
    if item.score_total and item.score_total >= 85:
        strengths.insert(0, "综合评分领先")
    return strengths[:3] or ["各项表现较均衡"]


def _build_tradeoffs(item: NameHistory) -> list[str]:
    tradeoffs: list[str] = []
    metrics = [
        ("音律", clamp_score(item.rhythm_score)),
        ("寓意", clamp_score(item.meaning_score)),
        ("传播性", clamp_score(item.spread_score)),
        ("域名", clamp_score(item.domain_score)),
    ]
    tradeoffs.extend(f"{label}仍有优化空间" for label, score in metrics if 0 < score < 70)
    if item.category == "企业名" and item.domain and not _is_domain_available(item.domain_status):
        tradeoffs.append("域名可用性需要进一步确认")
    if not item.score_total and not any(score for _, score in metrics):
        tradeoffs.append("缺少评分数据，建议结合人工偏好复核")
    return tradeoffs[:3] or ["暂无明显短板"]


def build_compare_item(item: NameHistory) -> NameCompareItemOut:
    return NameCompareItemOut(
        history_id=item.id,
        name=item.name,
        category=item.category,
        moral=item.moral,
        rhythm_score=clamp_score(item.rhythm_score),
        meaning_score=clamp_score(item.meaning_score),
        spread_score=clamp_score(item.spread_score),
        domain=item.domain or "",
        domain_status=item.domain_status or "",
        domain_checks=_decode_domain_checks(item.domain_checks),
        brand_warning=item.brand_warning or "",
        pinyin=item.pinyin or "",
        english_name=item.english_name or "",
        abbreviation=item.abbreviation or "",
        domain_score=clamp_score(item.domain_score),
        score_total=clamp_score(item.score_total),
        compare_score=build_compare_score(item),
        suitable_scenes=_build_suitable_scenes(item),
        strengths=_build_strengths(item),
        tradeoffs=_build_tradeoffs(item),
    )


def build_rank_reason(item: NameCompareItemOut) -> str:
    strengths = "、".join(item.strengths[:2])
    scenes = item.suitable_scenes[0] if item.suitable_scenes else "适用场景明确"
    return f"{strengths}，{scenes}"


def rank_compare_items(items: list[NameCompareItemOut]) -> list[NameCompareItemOut]:
    return sorted(
        items,
        key=lambda item: (
            item.compare_score,
            item.meaning_score,
            item.rhythm_score,
            item.spread_score,
            item.domain_score,
        ),
        reverse=True,
    )


def build_rankings(items: list[NameCompareItemOut], limit: int | None = None) -> list[NameCompareRankOut]:
    ranked_items = rank_compare_items(items)
    if limit is not None:
        ranked_items = ranked_items[:limit]
    return [
        NameCompareRankOut(
            rank=index + 1,
            history_id=item.history_id,
            name=item.name,
            compare_score=item.compare_score,
            reason=build_rank_reason(item),
        )
        for index, item in enumerate(ranked_items)
    ]


def build_project_recommendations(items: list[NameHistory], limit: int = 3) -> list[NameCompareRankOut]:
    compare_items = [build_compare_item(item) for item in items]
    return build_rankings(compare_items, limit=limit)
