import json

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio.session import AsyncSession

from models.name_history import NameHistory
from schemas.name_schemas import NameIn


def _decode_exclude(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        decoded = json.loads(value)
    except json.JSONDecodeError:
        return []
    return decoded if isinstance(decoded, list) else []


def _decode_domain_checks(value: str | None) -> list[dict[str, str]]:
    if not value:
        return []
    try:
        decoded = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(decoded, list):
        return []
    return [item for item in decoded if isinstance(item, dict)]


def _format_requirement_summary(name_info: NameIn) -> str | None:
    parts: list[str] = []

    if name_info.category == "人名":
        if name_info.birth_datetime:
            parts.append(f"生辰：{name_info.birth_datetime}")
        if name_info.wuxing and name_info.wuxing != "不限":
            parts.append(f"五行：{name_info.wuxing}")
        if name_info.desired_meaning:
            parts.append(f"期望寓意：{name_info.desired_meaning}")
    elif name_info.category == "企业名":
        if name_info.industry:
            parts.append(f"行业：{name_info.industry}")
        if name_info.style and name_info.style != "不限":
            parts.append(f"风格：{name_info.style}")
        if name_info.region:
            parts.append(f"地区：{name_info.region}")

    if name_info.other:
        parts.append(f"核心诉求：{name_info.other}")

    return "；".join(parts) if parts else name_info.other


def history_to_dict(item: NameHistory) -> dict:
    return {
        "id": item.id,
        "user_id": item.user_id,
        "project_id": item.project_id,
        "thread_id": item.thread_id,
        "category": item.category,
        "name": item.name,
        "reference": item.reference,
        "moral": item.moral,
        "domain": item.domain or "",
        "domain_status": item.domain_status or "",
        "domain_checks": _decode_domain_checks(item.domain_checks),
        "brand_warning": item.brand_warning or "",
        "pinyin": item.pinyin or "",
        "english_name": item.english_name or "",
        "abbreviation": item.abbreviation or "",
        "score_total": item.score_total or 0,
        "rhythm_score": item.rhythm_score or 0,
        "meaning_score": item.meaning_score or 0,
        "spread_score": item.spread_score or 0,
        "domain_score": item.domain_score or 0,
        "score_explanation": item.score_explanation or "",
        "surname": item.surname or "",
        "gender": item.gender or "",
        "length": item.length or "",
        "other": item.other,
        "exclude": _decode_exclude(item.exclude),
        "is_favorite": item.is_favorite,
        "created_time": item.created_time,
        "updated_time": item.updated_time,
    }


class NameHistoryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_many(
        self,
        user_id: int,
        thread_id: str,
        name_info: NameIn,
        names: list[dict],
        project_id: int | None = None,
    ) -> list[NameHistory]:
        requirement_summary = _format_requirement_summary(name_info)
        histories = [
            NameHistory(
                user_id=user_id,
                project_id=project_id,
                thread_id=thread_id,
                category=name_info.category,
                name=item.get("name", ""),
                reference=item.get("reference", ""),
                moral=item.get("moral", ""),
                domain=item.get("domain", "") or "",
                domain_status=item.get("domain_status", "") or "",
                domain_checks=json.dumps(item.get("domain_checks") or [], ensure_ascii=False),
                brand_warning=item.get("brand_warning", "") or "",
                pinyin=item.get("pinyin", "") or "",
                english_name=item.get("english_name", "") or "",
                abbreviation=item.get("abbreviation", "") or "",
                score_total=item.get("score_total", 0) or 0,
                rhythm_score=item.get("rhythm_score", 0) or 0,
                meaning_score=item.get("meaning_score", 0) or 0,
                spread_score=item.get("spread_score", 0) or 0,
                domain_score=item.get("domain_score", 0) or 0,
                score_explanation=item.get("score_explanation", "") or "",
                surname=name_info.surname or "",
                gender=name_info.gender or "",
                length=name_info.length or "",
                other=requirement_summary,
                exclude=json.dumps(name_info.exclude or [], ensure_ascii=False),
            )
            for item in names
        ]
        self.session.add_all(histories)
        await self.session.commit()
        return histories

    async def list_user_history(
        self,
        user_id: int,
        favorite_only: bool = False,
        category: str | None = None,
        keyword: str | None = None,
        project_id: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[NameHistory], int]:
        conditions = [NameHistory.user_id == user_id]
        if project_id:
            conditions.append(NameHistory.project_id == project_id)
        if favorite_only:
            conditions.append(NameHistory.is_favorite.is_(True))
        if category:
            conditions.append(NameHistory.category == category)
        if keyword:
            pattern = f"%{keyword}%"
            conditions.append(
                or_(
                    NameHistory.name.like(pattern),
                    NameHistory.reference.like(pattern),
                    NameHistory.moral.like(pattern),
                    NameHistory.other.like(pattern),
                )
            )

        total = await self.session.scalar(select(func.count()).select_from(NameHistory).where(*conditions))
        result = await self.session.execute(
            select(NameHistory)
            .where(*conditions)
            .order_by(NameHistory.created_time.desc(), NameHistory.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all()), int(total or 0)

    async def get_user_item(self, user_id: int, history_id: int) -> NameHistory | None:
        return await self.session.scalar(
            select(NameHistory).where(NameHistory.id == history_id, NameHistory.user_id == user_id)
        )

    async def get_user_items_by_ids(self, user_id: int, history_ids: list[int]) -> list[NameHistory]:
        if not history_ids:
            return []
        result = await self.session.execute(
            select(NameHistory).where(NameHistory.user_id == user_id, NameHistory.id.in_(history_ids))
        )
        items_by_id = {item.id: item for item in result.scalars().all()}
        return [items_by_id[history_id] for history_id in history_ids if history_id in items_by_id]

    async def set_favorite(self, item: NameHistory, is_favorite: bool) -> NameHistory:
        item.is_favorite = is_favorite
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def delete_user_item(self, user_id: int, history_id: int) -> bool:
        result = await self.session.execute(
            delete(NameHistory).where(NameHistory.id == history_id, NameHistory.user_id == user_id)
        )
        await self.session.commit()
        return bool(result.rowcount)
