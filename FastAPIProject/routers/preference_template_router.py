from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio.session import AsyncSession
from starlette.status import HTTP_404_NOT_FOUND

from core.auth import AuthHandler
from dependencies import get_session
from models.naming_preference_template import NamingPreferenceTemplate
from schemas.preference_template_schemas import (
    NamingPreferenceTemplateCreateIn,
    NamingPreferenceTemplateListOut,
    NamingPreferenceTemplateOut,
    NamingPreferenceTemplateUpdateIn,
)

auth_handler = AuthHandler()
router = APIRouter(prefix="/preference-templates", tags=["preference-templates"])


async def get_user_template(session: AsyncSession, user_id: int, template_id: int) -> NamingPreferenceTemplate | None:
    return await session.scalar(
        select(NamingPreferenceTemplate).where(
            NamingPreferenceTemplate.id == template_id,
            NamingPreferenceTemplate.user_id == user_id,
        )
    )


async def clear_default_templates(session: AsyncSession, user_id: int, category: str, exclude_id: int | None = None) -> None:
    result = await session.execute(
        select(NamingPreferenceTemplate).where(
            NamingPreferenceTemplate.user_id == user_id,
            NamingPreferenceTemplate.category == category,
        )
    )
    for template in result.scalars().all():
        if exclude_id is not None and template.id == exclude_id:
            continue
        template.is_default = False


@router.post("", response_model=NamingPreferenceTemplateOut)
async def create_preference_template(
    data: NamingPreferenceTemplateCreateIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    preferences = dict(data.preferences)
    preferences["category"] = data.category
    if data.is_default:
        await clear_default_templates(session, user_id, data.category)

    template = NamingPreferenceTemplate(
        user_id=user_id,
        title=data.title,
        category=data.category,
        preferences=preferences,
        is_default=data.is_default,
    )
    session.add(template)
    await session.commit()
    await session.refresh(template)
    return template


@router.get("", response_model=NamingPreferenceTemplateListOut)
async def list_preference_templates(
    category: str | None = Query(None),
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    conditions = [NamingPreferenceTemplate.user_id == user_id]
    if category:
        conditions.append(NamingPreferenceTemplate.category == category)

    total = await session.scalar(select(func.count()).select_from(NamingPreferenceTemplate).where(*conditions))
    result = await session.execute(
        select(NamingPreferenceTemplate)
        .where(*conditions)
        .order_by(
            NamingPreferenceTemplate.is_default.desc(),
            NamingPreferenceTemplate.updated_time.desc(),
            NamingPreferenceTemplate.id.desc(),
        )
    )
    return {"items": list(result.scalars().all()), "total": int(total or 0)}


@router.patch("/{template_id}", response_model=NamingPreferenceTemplateOut)
async def update_preference_template(
    template_id: int,
    data: NamingPreferenceTemplateUpdateIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    template = await get_user_template(session, user_id, template_id)
    if not template:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Preference template not found")

    old_category = template.category
    if data.title is not None:
        template.title = data.title
    if data.category is not None:
        template.category = data.category
        preferences = dict(template.preferences or {})
        preferences["category"] = data.category
        template.preferences = preferences
    if data.preferences is not None:
        preferences = dict(data.preferences)
        preferences["category"] = data.category or template.category
        template.preferences = preferences
    if data.is_default is not None:
        template.is_default = data.is_default

    if template.is_default:
        await clear_default_templates(session, user_id, template.category, template.id)
    elif old_category != template.category:
        await clear_default_templates(session, user_id, old_category, template.id)

    await session.commit()
    await session.refresh(template)
    return template


@router.delete("/{template_id}")
async def delete_preference_template(
    template_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    template = await get_user_template(session, user_id, template_id)
    if not template:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Preference template not found")

    await session.delete(template)
    await session.commit()
    return {"message": "Preference template deleted"}
