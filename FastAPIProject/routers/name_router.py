from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio.session import AsyncSession

from core.auth import AuthHandler
from core.membership_service import MembershipService
from core.name_scoring import attach_name_scores
from core.workflow import AINameGenerationError, feedback_names, generate_naming, generate_naming_v2
from dependencies import get_session
from repository.history_repo import NameHistoryRepository
from repository.project_repo import NamingProjectRepository
from schemas.name_schemas import FeedbackSchema, NameIn, NameOutSchema, NameSchemaWithThreadOut

auth_handler = AuthHandler()
router = APIRouter(prefix="/names", tags=["names"])


@router.post("/get_names", response_model=NameOutSchema)
async def get_legacy_names(
    name_info: NameIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    membership = MembershipService(session)
    await membership.consume(user_id, remark="旧版起名接口")
    try:
        result = await generate_naming(name_info, user_id)
        attach_name_scores(result["names"])
    except AINameGenerationError as exc:
        await membership.refund(user_id, remark="旧版起名失败退回额度")
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception:
        await membership.refund(user_id, remark="旧版起名失败退回额度")
        raise

    account = await membership.get_or_create_account(user_id)
    return NameOutSchema(names=result["names"], quota_remaining=account.credit_balance)


@router.post("/generate", response_model=NameSchemaWithThreadOut)
async def generate_names(
    name_info: NameIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    project_repo = NamingProjectRepository(session)
    project = await project_repo.get_or_create_for_generation(user_id, name_info)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    name_info.project_id = project.id

    membership = MembershipService(session)
    await membership.consume(user_id, remark="首次起名生成")
    try:
        result = await generate_naming_v2(name_info, user_id)
        names = result["names"]["names"]
        attach_name_scores(names)
        histories = await NameHistoryRepository(session).create_many(
            user_id, result["thread_id"], name_info, names, project_id=project.id
        )
        await project_repo.touch(project)
        for name, history in zip(names, histories):
            name["category"] = name_info.category
            name["history_id"] = history.id
            name["project_id"] = history.project_id
            name["is_favorite"] = history.is_favorite
    except AINameGenerationError as exc:
        await session.rollback()
        await membership.refund(user_id, remark="首次起名失败退回额度")
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception:
        await session.rollback()
        await membership.refund(user_id, remark="首次起名失败退回额度")
        raise

    account = await membership.get_or_create_account(user_id)
    return NameSchemaWithThreadOut(
        thread_id=result["thread_id"],
        project_id=project.id,
        names=names,
        quota_remaining=account.credit_balance,
    )


@router.post("/feedback", response_model=NameSchemaWithThreadOut)
async def feedback(
    data: FeedbackSchema,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    project_repo = NamingProjectRepository(session)
    if data.project_id:
        project = await project_repo.get_user_project(user_id, data.project_id)
        if project is None:
            raise HTTPException(status_code=404, detail="Project not found")
    else:
        project = await project_repo.find_by_thread_id(user_id, data.thread_id)

    effective_category = project.category if project else data.category
    effective_project_id = project.id if project else data.project_id
    feedback_data = data.model_copy(
        update={"category": effective_category, "project_id": effective_project_id}
    )

    membership = MembershipService(session)
    await membership.consume(user_id, remark="多轮反馈生成")
    try:
        result = await feedback_names(feedback_data, user_id)
        names = result["names"]["names"]
        attach_name_scores(names)
        name_info = NameIn(
            category=effective_category,
            surname="反馈记录" if effective_category == "人名" else "",
            gender="不限",
            length="",
            other=feedback_data.feedback,
            exclude=[],
        )
        histories = await NameHistoryRepository(session).create_many(
            user_id, result["thread_id"], name_info, names, project_id=project.id if project else None
        )
        if project:
            await project_repo.touch(project)
        for name, history in zip(names, histories):
            name["category"] = effective_category
            name["history_id"] = history.id
            name["project_id"] = history.project_id
            name["is_favorite"] = history.is_favorite
    except AINameGenerationError as exc:
        await session.rollback()
        await membership.refund(user_id, remark="反馈生成失败退回额度")
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception:
        await session.rollback()
        await membership.refund(user_id, remark="反馈生成失败退回额度")
        raise

    account = await membership.get_or_create_account(user_id)
    return NameSchemaWithThreadOut(
        thread_id=result["thread_id"],
        project_id=project.id if project else None,
        names=names,
        quota_remaining=account.credit_balance,
    )


@router.get("/quota")
async def get_generation_quota(
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    account = await MembershipService(session).get_or_create_account(user_id)
    return {
        "total_quota": account.total_recharged,
        "used_quota": account.total_consumed,
        "remaining_quota": account.credit_balance,
    }
