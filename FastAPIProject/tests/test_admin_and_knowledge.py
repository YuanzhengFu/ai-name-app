from datetime import datetime, timedelta
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import select

from routers import rag_router
from models.knowledge_task import KnowledgeTask
from models.membership import CreditTransaction, RechargeOrder
from models.name_history import NameHistory
from models.naming_project import NamingProject
from tests.conftest import auth_headers, create_plan, create_user


async def test_admin_routes_require_admin_user(client, session_maker):
    user = await create_user(session_maker, email="member@example.com")
    admin = await create_user(session_maker, email="admin@example.com", is_admin=True)

    denied_response = await client.get("/admin/me", headers=auth_headers(user.id))
    assert denied_response.status_code == 403

    allowed_response = await client.get("/admin/me", headers=auth_headers(admin.id))
    assert allowed_response.status_code == 200
    assert allowed_response.json()["email"] == "admin@example.com"

    create_plan_response = await client.post(
        "/admin/membership/plans",
        json={
            "name": "Pro",
            "description": "Admin created plan",
            "price_cents": 1990,
            "credits": 50,
            "validity_days": 60,
            "is_active": True,
            "sort_order": 1,
        },
        headers=auth_headers(admin.id),
    )
    assert create_plan_response.status_code == 200
    assert create_plan_response.json()["credits"] == 50


async def test_admin_data_routes_are_whitelisted_and_hide_password(client, session_maker):
    user = await create_user(session_maker, email="data-user@example.com")
    admin = await create_user(session_maker, email="data-admin@example.com", is_admin=True)

    denied_response = await client.get("/admin/data/tables", headers=auth_headers(user.id))
    assert denied_response.status_code == 403

    table_response = await client.get("/admin/data/tables", headers=auth_headers(admin.id))
    assert table_response.status_code == 200
    table_names = {item["name"] for item in table_response.json()["items"]}
    assert {"user", "name_history", "membership_plan"} <= table_names

    list_response = await client.get("/admin/data/user", headers=auth_headers(admin.id))
    assert list_response.status_code == 200
    first_user = list_response.json()["items"][0]
    assert "_password" not in first_user
    assert "password" not in first_user

    get_response = await client.get(f"/admin/data/user/{user.id}", headers=auth_headers(admin.id))
    assert get_response.status_code == 200
    assert "_password" not in get_response.json()["item"]


async def test_admin_data_rejects_password_update_and_current_admin_delete(client, session_maker):
    admin = await create_user(session_maker, email="self-admin@example.com", is_admin=True)

    update_response = await client.patch(
        f"/admin/data/user/{admin.id}",
        json={"data": {"_password": "plain-text"}},
        headers=auth_headers(admin.id),
    )
    assert update_response.status_code == 400
    assert "_password" in update_response.json()["detail"]

    delete_response = await client.delete(f"/admin/data/user/{admin.id}", headers=auth_headers(admin.id))
    assert delete_response.status_code == 400
    assert "current administrator" in delete_response.json()["detail"]


async def test_admin_data_create_update_delete_membership_plan(client, session_maker):
    admin = await create_user(session_maker, email="data-plan-admin@example.com", is_admin=True)

    create_response = await client.post(
        "/admin/data/membership_plan",
        json={
            "data": {
                "name": "Data Plan",
                "description": "Created from data maintenance",
                "price_cents": 6600,
                "credits": 88,
                "validity_days": 30,
                "is_active": True,
                "sort_order": 9,
            }
        },
        headers=auth_headers(admin.id),
    )
    assert create_response.status_code == 200
    plan_id = create_response.json()["item"]["id"]

    update_response = await client.patch(
        f"/admin/data/membership_plan/{plan_id}",
        json={"data": {"name": "Updated Data Plan", "credits": 99}},
        headers=auth_headers(admin.id),
    )
    assert update_response.status_code == 200
    assert update_response.json()["item"]["name"] == "Updated Data Plan"
    assert update_response.json()["item"]["credits"] == 99

    delete_response = await client.delete(
        f"/admin/data/membership_plan/{plan_id}",
        headers=auth_headers(admin.id),
    )
    assert delete_response.status_code == 200


async def test_admin_generation_stats_include_operation_dashboard_metrics(client, session_maker):
    user = await create_user(session_maker, email="dashboard-user@example.com")
    admin = await create_user(session_maker, email="dashboard-admin@example.com", is_admin=True)
    plan = await create_plan(session_maker, name="Dashboard Pro", price_cents=1990, credits=30)
    now = datetime.now()
    yesterday = now - timedelta(days=1)

    async with session_maker() as session:
        session.add_all(
            [
                NameHistory(
                    user_id=user.id,
                    thread_id="thread-human",
                    category="人名",
                    name="林清安",
                    reference="诗词",
                    moral="清雅安定",
                    created_time=now,
                    updated_time=now,
                ),
                NameHistory(
                    user_id=user.id,
                    thread_id="thread-company",
                    category="企业名",
                    name="云智科技",
                    reference="行业词",
                    moral="智能科技品牌",
                    other="科技 AI 简约 高端",
                    created_time=yesterday,
                    updated_time=yesterday,
                ),
                CreditTransaction(
                    user_id=user.id,
                    change_amount=-2,
                    balance_after=8,
                    transaction_type="consume",
                    source="generate",
                    created_time=now,
                ),
                RechargeOrder(
                    user_id=user.id,
                    plan_id=plan.id,
                    plan_name=plan.name,
                    amount_cents=plan.price_cents,
                    credits=plan.credits,
                    status="paid",
                    paid_time=now,
                    created_time=now,
                    updated_time=now,
                ),
                KnowledgeTask(
                    user_id=user.id,
                    filename="ok.txt",
                    file_path="ok.txt",
                    status="done",
                    created_time=now,
                    updated_time=now,
                ),
                KnowledgeTask(
                    user_id=user.id,
                    filename="bad.txt",
                    file_path="bad.txt",
                    status="failed",
                    error_message="parse failed",
                    created_time=now,
                    updated_time=now,
                ),
            ]
        )
        await session.commit()

    response = await client.get("/admin/generation-stats", headers=auth_headers(admin.id))

    assert response.status_code == 200
    body = response.json()
    assert body["total_generations"] == 2
    assert body["today_generations"] == 1
    assert body["today_credit_consumed"] == 2
    assert body["paid_conversion"]["paid_users"] == 1
    assert body["paid_conversion"]["paid_orders"] == 1
    assert body["paid_conversion"]["paid_amount_cents"] == 1990
    assert body["rag_failure_rate"] == 50
    assert body["daily_generations"][-1]["count"] == 1
    assert body["daily_credit_consumed"][-1]["credits"] == 2
    assert body["daily_rag_tasks"][-1] == {
        "date": now.date().isoformat(),
        "total": 2,
        "failed": 1,
        "failure_rate": 50,
    }
    category_counts = {item["category"]: item["count"] for item in body["category_stats"]}
    assert category_counts["人名"] == 1
    assert category_counts["企业名"] == 1
    assert body["hot_industries"][0]["name"] == "科技互联网"
    assert body["hot_styles"][0]["name"] in {"简约现代", "高端专业"}


async def test_knowledge_upload_uses_mocked_queue(client, session_maker, tmp_path, monkeypatch):
    user = await create_user(session_maker)
    queued_messages = []

    async def fake_send_to_queue(message):
        queued_messages.append(message)

    monkeypatch.setattr(rag_router, "UPLOAD_DIR", str(tmp_path))
    monkeypatch.setattr(rag_router, "send_to_queue", fake_send_to_queue)

    response = await client.post(
        "/knowledge/upload",
        files={"file": ("rules.txt", b"brand naming rules", "text/plain")},
        headers=auth_headers(user.id),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "queued"
    assert len(queued_messages) == 1
    assert queued_messages[0]["task_id"] == body["task_id"]
    assert queued_messages[0]["user_id"] == user.id
    assert queued_messages[0]["project_id"] is None
    queued_path = Path(queued_messages[0]["file_path"])
    assert queued_path.parent == tmp_path
    assert queued_path.suffix == ".txt"
    assert body["task"]["filename"] == "rules.txt"
    assert body["task"]["chunk_count"] == 0

    files_response = await client.get("/knowledge/files", headers=auth_headers(user.id))
    assert files_response.status_code == 200
    assert files_response.json()["total"] == 1


async def test_knowledge_upload_is_scoped_to_project(client, session_maker, tmp_path, monkeypatch):
    user = await create_user(session_maker)
    queued_messages = []

    async def fake_send_to_queue(message):
        queued_messages.append(message)

    async with session_maker() as session:
        project = NamingProject(user_id=user.id, title="Brand Project", category="企业名")
        session.add(project)
        await session.commit()
        await session.refresh(project)
        project_id = project.id

    monkeypatch.setattr(rag_router, "UPLOAD_DIR", str(tmp_path))
    monkeypatch.setattr(rag_router, "send_to_queue", fake_send_to_queue)

    response = await client.post(
        f"/knowledge/upload?project_id={project_id}",
        files={"file": ("rules.txt", b"project brand rules", "text/plain")},
        headers=auth_headers(user.id),
    )

    assert response.status_code == 200
    assert response.json()["task"]["project_id"] == project_id
    assert queued_messages[0]["project_id"] == project_id

    scoped_files = await client.get(f"/knowledge/files?project_id={project_id}", headers=auth_headers(user.id))
    assert scoped_files.json()["total"] == 1

    other_project_files = await client.get("/knowledge/files?project_id=9999", headers=auth_headers(user.id))
    assert other_project_files.json()["total"] == 0


async def test_knowledge_upload_marks_task_failed_when_queue_unavailable(
    client,
    session_maker,
    tmp_path,
    monkeypatch,
):
    user = await create_user(session_maker)

    async def failing_send_to_queue(message):
        raise HTTPException(status_code=503, detail="RabbitMQ service is unavailable")

    monkeypatch.setattr(rag_router, "UPLOAD_DIR", str(tmp_path))
    monkeypatch.setattr(rag_router, "send_to_queue", failing_send_to_queue)

    response = await client.post(
        "/knowledge/upload",
        files={"file": ("rules.txt", b"brand naming rules", "text/plain")},
        headers=auth_headers(user.id),
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "RabbitMQ service is unavailable"

    async with session_maker() as session:
        task = await session.scalar(select(KnowledgeTask).where(KnowledgeTask.user_id == user.id))
        assert task is not None
        assert task.status == "failed"
        assert task.error_message == "RabbitMQ service is unavailable"


async def test_admin_can_retry_failed_knowledge_task(client, session_maker, tmp_path, monkeypatch):
    user = await create_user(session_maker)
    admin = await create_user(session_maker, email="retry-admin@example.com", is_admin=True)
    file_path = tmp_path / "rules.txt"
    file_path.write_text("brand rules", encoding="utf-8")
    queued_messages = []

    async def fake_send_to_queue(message):
        queued_messages.append(message)

    async with session_maker() as session:
        task = KnowledgeTask(
            user_id=user.id,
            filename="rules.txt",
            file_path=str(file_path),
            status="failed",
            error_message="PDF parser crashed",
        )
        session.add(task)
        await session.commit()
        await session.refresh(task)
        task_id = task.id

    monkeypatch.setattr(rag_router, "send_to_queue", fake_send_to_queue)

    response = await client.post(
        f"/admin/knowledge-tasks/{task_id}/reparse",
        headers=auth_headers(admin.id),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "queued"
    assert body["error_message"] is None
    assert len(queued_messages) == 1
    assert queued_messages[0]["task_id"] == task_id


async def test_knowledge_preview_and_delete_file(client, session_maker, tmp_path, monkeypatch):
    user = await create_user(session_maker)
    file_path = tmp_path / "rules.txt"
    file_path.write_text("brand rules preview content", encoding="utf-8")
    deleted_vectors = []

    def fake_delete_task_vectors(user_id, task_id):
        deleted_vectors.append((user_id, task_id))

    async with session_maker() as session:
        task = KnowledgeTask(
            user_id=user.id,
            filename="rules.txt",
            file_path=str(file_path),
            status="done",
            chunk_count=3,
            parse_log="Parsed 1 document page(s) into 3 chunk(s).",
        )
        session.add(task)
        await session.commit()
        await session.refresh(task)
        task_id = task.id

    preview_response = await client.get(
        f"/knowledge/tasks/{task_id}/preview?max_chars=200",
        headers=auth_headers(user.id),
    )
    assert preview_response.status_code == 200
    assert preview_response.json()["content"] == "brand rules preview content"

    monkeypatch.setattr(rag_router, "delete_task_vectors", fake_delete_task_vectors)
    delete_response = await client.delete(f"/knowledge/tasks/{task_id}", headers=auth_headers(user.id))
    assert delete_response.status_code == 200
    assert deleted_vectors == [(user.id, task_id)]
    assert not file_path.exists()

    async with session_maker() as session:
        assert await session.get(KnowledgeTask, task_id) is None


async def test_admin_can_batch_retry_failed_knowledge_tasks(client, session_maker, tmp_path, monkeypatch):
    user = await create_user(session_maker)
    admin = await create_user(session_maker, email="batch-admin@example.com", is_admin=True)
    queued_messages = []

    async def fake_send_to_queue(message):
        queued_messages.append(message)

    async with session_maker() as session:
        for index in range(2):
            file_path = tmp_path / f"rules-{index}.txt"
            file_path.write_text(f"brand rules {index}", encoding="utf-8")
            session.add(
                KnowledgeTask(
                    user_id=user.id,
                    filename=file_path.name,
                    file_path=str(file_path),
                    status="failed",
                    error_message="embedding failed",
                )
            )
        await session.commit()

    monkeypatch.setattr(rag_router, "send_to_queue", fake_send_to_queue)

    response = await client.post(
        "/admin/knowledge-tasks/reparse",
        json={"status": "failed", "limit": 100},
        headers=auth_headers(admin.id),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["retried"] == 2
    assert body["failed"] == 0
    assert len(queued_messages) == 2
