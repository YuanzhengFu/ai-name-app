from io import BytesIO
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio.session import AsyncSession
from starlette.responses import StreamingResponse
from starlette.status import HTTP_404_NOT_FOUND

from core.auth import AuthHandler
from core.name_compare import build_compare_item, build_rankings
from core.report_service import REPORT_FORMATS, build_report_bytes, build_report_filename
from dependencies import get_session
from repository.history_repo import NameHistoryRepository, history_to_dict
from schemas.history_schemas import (
    HistoryFavoriteIn,
    NameCompareIn,
    NameCompareOut,
    NameHistoryListOut,
    NameHistoryOut,
)

auth_handler = AuthHandler()
router = APIRouter(prefix="/history", tags=["history"])


@router.get("", response_model=NameHistoryListOut)
async def list_history(
    favorite_only: bool = Query(False),
    category: str | None = Query(None),
    keyword: str | None = Query(None),
    project_id: int | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    repo = NameHistoryRepository(session)
    items, total = await repo.list_user_history(
        user_id=user_id,
        favorite_only=favorite_only,
        category=category,
        keyword=keyword,
        project_id=project_id,
        limit=limit,
        offset=offset,
    )
    return {
        "items": [history_to_dict(item) for item in items],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.post("/compare", response_model=NameCompareOut)
async def compare_histories(
    data: NameCompareIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    repo = NameHistoryRepository(session)
    items = await repo.get_user_items_by_ids(user_id, data.history_ids)
    if len(items) != len(data.history_ids):
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="部分历史记录不存在")

    compare_items = [build_compare_item(item) for item in items]
    ranking = build_rankings(compare_items)
    recommendation = f"优先推荐「{ranking[0].name}」，综合对比得分 {ranking[0].compare_score}，{ranking[0].reason}。"
    return NameCompareOut(items=compare_items, ranking=ranking, recommendation=recommendation)


@router.get("/{history_id}", response_model=NameHistoryOut)
async def get_history_detail(
    history_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    repo = NameHistoryRepository(session)
    item = await repo.get_user_item(user_id, history_id)
    if not item:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="历史记录不存在")
    return history_to_dict(item)


@router.get("/{history_id}/export")
async def export_history_report(
    history_id: int,
    format: str = Query("pdf", pattern="^(pdf|image|txt)$"),
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    repo = NameHistoryRepository(session)
    item = await repo.get_user_item(user_id, history_id)
    if not item:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="历史记录不存在")
    if format not in REPORT_FORMATS:
        raise HTTPException(status_code=400, detail="不支持的导出格式")

    content, media_type = build_report_bytes(item, format)
    filename = build_report_filename(item, format)
    encoded_filename = quote(filename)
    headers = {"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
    return StreamingResponse(BytesIO(content), media_type=media_type, headers=headers)


@router.patch("/{history_id}/favorite", response_model=NameHistoryOut)
async def set_history_favorite(
    history_id: int,
    data: HistoryFavoriteIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    repo = NameHistoryRepository(session)
    item = await repo.get_user_item(user_id, history_id)
    if not item:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="历史记录不存在")
    updated = await repo.set_favorite(item, data.is_favorite)
    return history_to_dict(updated)


@router.delete("/{history_id}")
async def delete_history(
    history_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    repo = NameHistoryRepository(session)
    deleted = await repo.delete_user_item(user_id, history_id)
    if not deleted:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="历史记录不存在")
    return {"message": "删除成功"}
