from io import BytesIO
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import AsyncSession
from starlette.responses import StreamingResponse
from starlette.status import HTTP_404_NOT_FOUND

from core.auth import AuthHandler
from core.name_compare import build_project_recommendations
from core.report_service import REPORT_FORMATS, build_project_report_bytes, build_project_report_filename
from dependencies import get_session
from models.knowledge_task import KnowledgeTask
from models.name_history import NameHistory
from repository.history_repo import history_to_dict
from repository.project_repo import NamingProjectRepository
from routers.rag_router import task_to_dict
from schemas.project_schemas import (
    NamingProjectCreateIn,
    NamingProjectDetailOut,
    NamingProjectListOut,
    NamingProjectOut,
    NamingProjectUpdateIn,
)

auth_handler = AuthHandler()
router = APIRouter(prefix="/projects", tags=["projects"])


def project_to_dict(project, stats: dict[str, int] | None = None) -> dict:
    stats = stats or {}
    return {
        "id": project.id,
        "user_id": project.user_id,
        "title": project.title,
        "category": project.category,
        "description": project.description or "",
        "status": project.status,
        "history_count": stats.get("history_count", 0),
        "favorite_count": stats.get("favorite_count", 0),
        "knowledge_file_count": stats.get("knowledge_file_count", 0),
        "created_time": project.created_time,
        "updated_time": project.updated_time,
    }


@router.post("", response_model=NamingProjectOut)
async def create_project(
    data: NamingProjectCreateIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    repo = NamingProjectRepository(session)
    project = await repo.create(user_id, data.title, data.category, data.description)
    return project_to_dict(project)


@router.get("", response_model=NamingProjectListOut)
async def list_projects(
    status: str | None = Query("active"),
    category: str | None = Query(None),
    keyword: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    repo = NamingProjectRepository(session)
    projects, total = await repo.list_projects(user_id, status, category, keyword, limit, offset)
    stats = await repo.stats_for_project_ids([project.id for project in projects])
    return {
        "items": [project_to_dict(project, stats.get(project.id)) for project in projects],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{project_id}", response_model=NamingProjectDetailOut)
async def get_project_detail(
    project_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    repo = NamingProjectRepository(session)
    project = await repo.get_user_project(user_id, project_id)
    if not project:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Project not found")

    stats = await repo.stats_for_project_ids([project.id])
    history_result = await session.execute(
        select(NameHistory)
        .where(NameHistory.user_id == user_id, NameHistory.project_id == project_id)
        .order_by(NameHistory.created_time.desc(), NameHistory.id.desc())
    )
    knowledge_result = await session.execute(
        select(KnowledgeTask)
        .where(KnowledgeTask.user_id == user_id, KnowledgeTask.project_id == project_id)
        .order_by(KnowledgeTask.created_time.desc(), KnowledgeTask.id.desc())
    )
    history_items = list(history_result.scalars().all())
    data = project_to_dict(project, stats.get(project.id))
    data["recommendations"] = build_project_recommendations(history_items, limit=3)
    data["histories"] = [history_to_dict(item) for item in history_items]
    data["knowledge_files"] = [task_to_dict(item) for item in knowledge_result.scalars().all()]
    return data


@router.get("/{project_id}/export")
async def export_project_report(
    project_id: int,
    format: str = Query("pdf", pattern="^(pdf|image|txt)$"),
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    repo = NamingProjectRepository(session)
    project = await repo.get_user_project(user_id, project_id)
    if not project:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Project not found")
    if format not in REPORT_FORMATS:
        raise HTTPException(status_code=400, detail="不支持的导出格式")

    history_result = await session.execute(
        select(NameHistory)
        .where(NameHistory.user_id == user_id, NameHistory.project_id == project_id)
        .order_by(NameHistory.created_time.asc(), NameHistory.id.asc())
    )
    histories = list(history_result.scalars().all())
    content, media_type = build_project_report_bytes(project, histories, format)
    filename = build_project_report_filename(project, format)
    encoded_filename = quote(filename)
    headers = {"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
    return StreamingResponse(BytesIO(content), media_type=media_type, headers=headers)


@router.patch("/{project_id}", response_model=NamingProjectOut)
async def update_project(
    project_id: int,
    data: NamingProjectUpdateIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    repo = NamingProjectRepository(session)
    project = await repo.get_user_project(user_id, project_id)
    if not project:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Project not found")

    if data.title is not None:
        project.title = data.title.strip()[:120]
    if data.description is not None:
        project.description = data.description
    if data.status is not None:
        project.status = data.status

    await session.commit()
    await session.refresh(project)
    stats = await repo.stats_for_project_ids([project.id])
    return project_to_dict(project, stats.get(project.id))


@router.delete("/{project_id}")
async def archive_project(
    project_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    repo = NamingProjectRepository(session)
    project = await repo.get_user_project(user_id, project_id)
    if not project:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Project not found")

    project.status = "archived"
    await session.commit()
    return {"message": "Project archived"}
