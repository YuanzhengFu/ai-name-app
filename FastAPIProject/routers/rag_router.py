import json
import os
import shutil
import uuid
from pathlib import Path

import aio_pika
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from langchain_community.document_loaders import PyPDFLoader
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio.session import AsyncSession

from core.auth import AuthHandler
from dependencies import get_session
from models.knowledge_task import KnowledgeTask
from repository.project_repo import NamingProjectRepository
from settings import ALLOWED_KNOWLEDGE_EXTENSIONS, MAX_UPLOAD_BYTES, RABBITMQ_URL, RAG_QUEUE_NAME, UPLOAD_DIR
from core.rag_service import delete_task_vectors

auth_handler = AuthHandler()
router = APIRouter(prefix="/knowledge", tags=["knowledge"])

os.makedirs(UPLOAD_DIR, exist_ok=True)

TASK_STATUS_LABELS = {
    "queued": "queued",
    "processing": "processing",
    "done": "done",
    "failed": "failed",
}


class KnowledgeTaskActiveIn(BaseModel):
    is_active: bool


class KnowledgeTaskPreviewOut(BaseModel):
    id: int
    filename: str
    content: str
    truncated: bool
    max_chars: int


def task_to_dict(task: KnowledgeTask) -> dict:
    return {
        "id": task.id,
        "project_id": task.project_id,
        "filename": task.filename,
        "status": task.status,
        "status_label": TASK_STATUS_LABELS.get(task.status, task.status),
        "error_message": task.error_message,
        "is_active": task.is_active,
        "chunk_count": task.chunk_count,
        "parse_log": task.parse_log,
        "created_time": task.created_time,
        "updated_time": task.updated_time,
    }


async def send_to_queue(message_dict: dict):
    try:
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        async with connection:
            channel = await connection.channel()
            queue = await channel.declare_queue(RAG_QUEUE_NAME, durable=True)
            message_body = json.dumps(message_dict).encode("utf-8")
            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=message_body,
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                ),
                routing_key=queue.name,
            )
    except aio_pika.exceptions.AMQPError as exc:
        raise HTTPException(status_code=503, detail="RabbitMQ service is unavailable") from exc
    except OSError as exc:
        raise HTTPException(status_code=503, detail="RabbitMQ service is unavailable") from exc


async def enqueue_knowledge_task(task: KnowledgeTask, session: AsyncSession) -> KnowledgeTask:
    if not os.path.exists(task.file_path):
        task.status = "failed"
        task.error_message = "Uploaded file no longer exists"
        await session.commit()
        await session.refresh(task)
        raise HTTPException(status_code=404, detail="Uploaded file no longer exists")

    task.status = "queued"
    task.error_message = None
    task.chunk_count = 0
    task.parse_log = "Queued for parsing."
    await session.commit()
    await session.refresh(task)

    try:
        await send_to_queue(
            {
                "task_id": task.id,
                "user_id": task.user_id,
                "file_path": task.file_path,
                "project_id": task.project_id,
            }
        )
    except HTTPException as exc:
        task.status = "failed"
        task.error_message = str(exc.detail)
        await session.commit()
        await session.refresh(task)
        raise

    return task


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    project_id: int | None = Query(None),
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    if project_id:
        from models.naming_project import NamingProject

        project = await session.get(NamingProject, project_id)
        if not project or project.user_id != user_id:
            raise HTTPException(status_code=404, detail="Project not found")
    else:
        project = None

    original_name = Path(file.filename or "").name
    suffix = Path(original_name).suffix.lower()
    if suffix not in ALLOWED_KNOWLEDGE_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only TXT and PDF files are supported")

    safe_name = f"{user_id}_{uuid.uuid4().hex}{suffix}"
    upload_dir = Path(UPLOAD_DIR)
    absolute_path = str((upload_dir / safe_name).resolve())

    with open(absolute_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = os.path.getsize(absolute_path)
    if file_size <= 0:
        os.remove(absolute_path)
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    if file_size > MAX_UPLOAD_BYTES:
        os.remove(absolute_path)
        raise HTTPException(status_code=413, detail="Uploaded file is too large")

    task = KnowledgeTask(
        user_id=user_id,
        project_id=project_id,
        filename=original_name,
        file_path=absolute_path,
        parse_log="Uploaded and queued for parsing.",
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)
    if project:
        await NamingProjectRepository(session).touch(project)

    task_message = {
        "task_id": task.id,
        "user_id": user_id,
        "file_path": absolute_path,
        "project_id": project_id,
    }

    try:
        await send_to_queue(task_message)
    except HTTPException as exc:
        task.status = "failed"
        task.error_message = str(exc.detail)
        await session.commit()
        await session.refresh(task)
        raise

    return {
        "result": "success",
        "message": f"File {original_name} uploaded and queued.",
        "task": task_to_dict(task),
        "task_id": task.id,
        "status": task.status,
        "status_label": TASK_STATUS_LABELS[task.status],
    }


@router.get("/files")
async def list_files(
    status: str | None = Query(None),
    active_only: bool = Query(False),
    project_id: int | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    conditions = [KnowledgeTask.user_id == user_id]
    if status:
        conditions.append(KnowledgeTask.status == status)
    if active_only:
        conditions.append(KnowledgeTask.is_active.is_(True))
    if project_id:
        conditions.append(KnowledgeTask.project_id == project_id)

    total = await session.scalar(select(func.count()).select_from(KnowledgeTask).where(*conditions))
    result = await session.execute(
        select(KnowledgeTask)
        .where(*conditions)
        .order_by(KnowledgeTask.created_time.desc(), KnowledgeTask.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return {
        "items": [task_to_dict(task) for task in result.scalars().all()],
        "total": int(total or 0),
        "limit": limit,
        "offset": offset,
    }


@router.get("/tasks/{task_id}")
async def get_task_status(
    task_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    task = await session.get(KnowledgeTask, task_id)
    if not task or task.user_id != user_id:
        raise HTTPException(status_code=404, detail="Knowledge task not found")
    return task_to_dict(task)


def read_file_preview(task: KnowledgeTask, max_chars: int) -> tuple[str, bool]:
    file_path = Path(task.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Uploaded file no longer exists")

    suffix = file_path.suffix.lower()
    if suffix == ".txt":
        content = file_path.read_text(encoding="utf-8", errors="replace")
    elif suffix == ".pdf":
        pages = PyPDFLoader(str(file_path)).load()
        content = "\n\n".join(page.page_content for page in pages[:3])
    else:
        raise HTTPException(status_code=400, detail="Unsupported preview file format")

    truncated = len(content) > max_chars
    return content[:max_chars], truncated


@router.get("/tasks/{task_id}/preview", response_model=KnowledgeTaskPreviewOut)
async def preview_task_file(
    task_id: int,
    max_chars: int = Query(2000, ge=200, le=10000),
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    task = await session.get(KnowledgeTask, task_id)
    if not task or task.user_id != user_id:
        raise HTTPException(status_code=404, detail="Knowledge task not found")

    content, truncated = read_file_preview(task, max_chars)
    return {
        "id": task.id,
        "filename": task.filename,
        "content": content,
        "truncated": truncated,
        "max_chars": max_chars,
    }


@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    task = await session.get(KnowledgeTask, task_id)
    if not task or task.user_id != user_id:
        raise HTTPException(status_code=404, detail="Knowledge task not found")
    if task.status == "processing":
        raise HTTPException(status_code=409, detail="Task is processing")

    try:
        delete_task_vectors(task.user_id, task.id)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Failed to clean Chroma vectors: {exc}") from exc

    file_path = Path(task.file_path)
    if file_path.exists():
        file_path.unlink()

    await session.delete(task)
    await session.commit()
    return {"message": "Knowledge file deleted", "id": task_id}


@router.post("/tasks/{task_id}/reparse")
async def reparse_task(
    task_id: int,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    task = await session.get(KnowledgeTask, task_id)
    if not task or task.user_id != user_id:
        raise HTTPException(status_code=404, detail="Knowledge task not found")

    task = await enqueue_knowledge_task(task, session)
    return task_to_dict(task)


@router.patch("/tasks/{task_id}/active")
async def update_task_active(
    task_id: int,
    data: KnowledgeTaskActiveIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    task = await session.get(KnowledgeTask, task_id)
    if not task or task.user_id != user_id:
        raise HTTPException(status_code=404, detail="Knowledge task not found")

    task.is_active = data.is_active
    await session.commit()
    await session.refresh(task)
    return task_to_dict(task)
