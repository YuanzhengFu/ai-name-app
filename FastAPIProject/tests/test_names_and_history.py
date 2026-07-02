from sqlalchemy import select
from models.membership import UserMembership
from models.name_history import NameHistory
from models.naming_project import NamingProject
from routers import name_router
from tests.conftest import auth_headers, create_user


def _name_payload():
    return {
        "category": "人名",
        "surname": "林",
        "gender": "不限",
        "length": "2",
        "other": "清爽自然",
        "exclude": [],
    }


async def test_generate_names_uses_mocked_workflow_and_persists_history(client, session_maker, monkeypatch):
    user = await create_user(session_maker)

    async def fake_generate_naming_v2(name_info, user_id):
        return {
            "thread_id": "thread-test",
            "names": {
                "names": [
                    {"name": "林知夏", "reference": "mock", "moral": "clear and warm"},
                    {"name": "林闻溪", "reference": "mock", "moral": "calm and bright"},
                ]
            },
        }

    monkeypatch.setattr(name_router, "generate_naming_v2", fake_generate_naming_v2)

    response = await client.post("/names/generate", json=_name_payload(), headers=auth_headers(user.id))
    assert response.status_code == 200
    body = response.json()
    assert body["thread_id"] == "thread-test"
    assert body["project_id"]
    assert body["quota_remaining"] == 9
    assert [item["name"] for item in body["names"]] == ["林知夏", "林闻溪"]
    assert all(item["history_id"] for item in body["names"])

    history_response = await client.get("/history", headers=auth_headers(user.id))
    assert history_response.status_code == 200
    assert history_response.json()["total"] == 2
    assert all(item["project_id"] == body["project_id"] for item in history_response.json()["items"])

    project_response = await client.get(f"/projects/{body['project_id']}", headers=auth_headers(user.id))
    assert project_response.status_code == 200
    project_body = project_response.json()
    assert project_body["history_count"] == 2
    assert len(project_body["histories"]) == 2
    assert len(project_body["recommendations"]) == 2


async def test_generation_failure_refunds_consumed_credit(client, session_maker, monkeypatch):
    user = await create_user(session_maker)

    async def failing_generate_naming_v2(name_info, user_id):
        raise RuntimeError("mock workflow failure")

    monkeypatch.setattr(name_router, "generate_naming_v2", failing_generate_naming_v2)

    response = await client.post("/names/generate", json=_name_payload(), headers=auth_headers(user.id))
    assert response.status_code == 500

    async with session_maker() as session:
        account = await session.scalar(select(UserMembership).where(UserMembership.user_id == user.id))
        histories = (await session.execute(select(NameHistory))).scalars().all()
        projects = (await session.execute(select(NamingProject))).scalars().all()
        assert account.credit_balance == 10
        assert account.total_consumed == 0
        assert histories == []
        assert len(projects) == 1


async def test_existing_project_can_collect_generation_and_feedback(client, session_maker, monkeypatch):
    user = await create_user(session_maker)
    category = _name_payload()["category"]

    project_response = await client.post(
        "/projects",
        json={"title": "Brand Sprint", "category": category, "description": "Long running naming work"},
        headers=auth_headers(user.id),
    )
    assert project_response.status_code == 200
    project_id = project_response.json()["id"]

    async def fake_generate_naming_v2(name_info, user_id):
        return {
            "thread_id": "thread-project",
            "names": {"names": [{"name": "ProjectNameA", "reference": "mock", "moral": "bright"}]},
        }

    async def fake_feedback_names(data, user_id):
        return {
            "thread_id": data.thread_id,
            "names": {"names": [{"name": "ProjectNameB", "reference": "mock", "moral": "hope"}]},
        }

    monkeypatch.setattr(name_router, "generate_naming_v2", fake_generate_naming_v2)
    monkeypatch.setattr(name_router, "feedback_names", fake_feedback_names)

    payload = _name_payload()
    payload["project_id"] = project_id
    generate_response = await client.post("/names/generate", json=payload, headers=auth_headers(user.id))
    assert generate_response.status_code == 200
    assert generate_response.json()["project_id"] == project_id

    feedback_response = await client.post(
        "/names/feedback",
        json={"thread_id": "thread-project", "project_id": project_id, "category": category, "feedback": "more gentle"},
        headers=auth_headers(user.id),
    )
    assert feedback_response.status_code == 200
    assert feedback_response.json()["project_id"] == project_id

    history_response = await client.get(f"/history?project_id={project_id}", headers=auth_headers(user.id))
    assert history_response.status_code == 200
    assert history_response.json()["total"] == 2


async def test_feedback_uses_project_category_when_client_category_is_stale(client, session_maker, monkeypatch):
    user = await create_user(session_maker)
    seen = {}

    project_response = await client.post(
        "/projects",
        json={"title": "Brand Sprint", "category": "企业名", "description": "Company naming work"},
        headers=auth_headers(user.id),
    )
    assert project_response.status_code == 200
    project_id = project_response.json()["id"]

    async def fake_feedback_names(data, user_id):
        seen["category"] = data.category
        seen["project_id"] = data.project_id
        return {
            "thread_id": data.thread_id,
            "names": {"names": [{"name": "云栖科技", "reference": "mock", "moral": "科技品牌感"}]},
        }

    monkeypatch.setattr(name_router, "feedback_names", fake_feedback_names)

    feedback_response = await client.post(
        "/names/feedback",
        json={"thread_id": "thread-company", "project_id": project_id, "category": "人名", "feedback": "保留用字"},
        headers=auth_headers(user.id),
    )
    assert feedback_response.status_code == 200
    body = feedback_response.json()
    assert seen == {"category": "企业名", "project_id": project_id}
    assert body["names"][0]["category"] == "企业名"

    history_response = await client.get(f"/history?project_id={project_id}", headers=auth_headers(user.id))
    assert history_response.status_code == 200
    assert history_response.json()["items"][0]["category"] == "企业名"


async def test_compare_histories_returns_ranked_recommendation(client, session_maker):
    user = await create_user(session_maker)
    async with session_maker() as session:
        histories = [
            NameHistory(
                user_id=user.id,
                thread_id="thread-compare",
                category="企业名",
                name="星澜科技",
                reference="星河与波澜",
                moral="有科技感和开拓感",
                domain="xinglan.com",
                domain_status="available",
                score_total=92,
                rhythm_score=88,
                meaning_score=90,
                spread_score=91,
                domain_score=94,
                other="行业：科技；风格：现代",
            ),
            NameHistory(
                user_id=user.id,
                thread_id="thread-compare",
                category="企业名",
                name="云栖智能",
                reference="云端栖居",
                moral="轻盈稳定",
                domain="yunqi.com",
                domain_status="registered",
                score_total=84,
                rhythm_score=86,
                meaning_score=82,
                spread_score=83,
                domain_score=60,
                other="行业：科技；风格：现代",
            ),
        ]
        session.add_all(histories)
        await session.commit()
        history_ids = [item.id for item in histories]

    response = await client.post("/history/compare", json={"history_ids": history_ids}, headers=auth_headers(user.id))
    assert response.status_code == 200
    body = response.json()
    assert [item["name"] for item in body["ranking"]] == ["星澜科技", "云栖智能"]
    assert body["ranking"][0]["compare_score"] == 92
    assert "优先推荐" in body["recommendation"]
    assert body["items"][0]["domain_status"] == "available"
    assert body["items"][0]["suitable_scenes"]


async def test_project_detail_returns_top_three_recommendations(client, session_maker):
    user = await create_user(session_maker)
    async with session_maker() as session:
        project = NamingProject(user_id=user.id, title="企业命名", category="企业名", description="科技品牌")
        session.add(project)
        await session.flush()
        histories = [
            NameHistory(
                user_id=user.id,
                project_id=project.id,
                thread_id="thread-project-top",
                category="企业名",
                name="星澜科技",
                reference="星河与波澜",
                moral="有科技感和开拓感",
                domain="xinglan.com",
                domain_status="available",
                score_total=92,
                rhythm_score=88,
                meaning_score=90,
                spread_score=91,
                domain_score=94,
                other="行业：科技；风格：现代",
            ),
            NameHistory(
                user_id=user.id,
                project_id=project.id,
                thread_id="thread-project-top",
                category="企业名",
                name="云栖智能",
                reference="云端栖居",
                moral="轻盈稳定",
                domain="yunqi.com",
                domain_status="registered",
                score_total=84,
                rhythm_score=86,
                meaning_score=82,
                spread_score=83,
                domain_score=60,
                other="行业：科技；风格：现代",
            ),
            NameHistory(
                user_id=user.id,
                project_id=project.id,
                thread_id="thread-project-top",
                category="企业名",
                name="明启数科",
                reference="明亮启程",
                moral="清晰、可靠",
                score_total=89,
                rhythm_score=84,
                meaning_score=92,
                spread_score=86,
                domain_score=80,
                other="行业：科技；风格：现代",
            ),
            NameHistory(
                user_id=user.id,
                project_id=project.id,
                thread_id="thread-project-top",
                category="企业名",
                name="蓝栈未来",
                reference="技术栈",
                moral="偏技术向",
                score_total=77,
                rhythm_score=74,
                meaning_score=78,
                spread_score=76,
                domain_score=72,
                other="行业：科技；风格：现代",
            ),
        ]
        session.add_all(histories)
        await session.commit()
        project_id = project.id

    response = await client.get(f"/projects/{project_id}", headers=auth_headers(user.id))
    assert response.status_code == 200
    body = response.json()
    assert [item["name"] for item in body["recommendations"]] == ["星澜科技", "明启数科", "云栖智能"]
    assert [item["rank"] for item in body["recommendations"]] == [1, 2, 3]
    assert body["recommendations"][0]["compare_score"] == 92
    assert "综合评分领先" in body["recommendations"][0]["reason"]
    assert len(body["histories"]) == 4


async def test_project_export_txt_contains_project_candidates_and_iterations(client, session_maker):
    user = await create_user(session_maker)
    async with session_maker() as session:
        project = NamingProject(user_id=user.id, title="企业命名交付", category="企业名", description="科技品牌")
        session.add(project)
        await session.flush()
        histories = [
            NameHistory(
                user_id=user.id,
                project_id=project.id,
                thread_id="thread-export-a",
                category="企业名",
                name="星澜科技",
                reference="星河与波澜",
                moral="有科技感和开拓感",
                domain="xinglan.com",
                domain_status="available",
                score_total=92,
                rhythm_score=88,
                meaning_score=90,
                spread_score=91,
                domain_score=94,
                is_favorite=True,
                other="行业：科技；风格：现代",
            ),
            NameHistory(
                user_id=user.id,
                project_id=project.id,
                thread_id="thread-export-b",
                category="企业名",
                name="云栖智能",
                reference="云端栖居",
                moral="轻盈稳定",
                score_total=84,
                rhythm_score=86,
                meaning_score=82,
                spread_score=83,
                domain_score=60,
                other="反馈：更柔和",
            ),
        ]
        session.add_all(histories)
        await session.commit()
        project_id = project.id

    response = await client.get(f"/projects/{project_id}/export?format=txt", headers=auth_headers(user.id))
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    body = response.text
    assert "企业命名交付 项目命名方案" in body
    assert "项目描述：科技品牌" in body
    assert "No.1 星澜科技" in body
    assert "已收藏" in body
    assert "四、反馈迭代记录" in body
    assert "thread-export-a" in body
    assert "thread-export-b" in body


async def test_compare_histories_validates_selection_count(client, session_maker):
    user = await create_user(session_maker)

    response = await client.post("/history/compare", json={"history_ids": [1]}, headers=auth_headers(user.id))
    assert response.status_code == 422


async def test_compare_histories_rejects_other_users_history(client, session_maker):
    user = await create_user(session_maker, email="owner@example.com")
    other = await create_user(session_maker, email="other@example.com")
    async with session_maker() as session:
        own_item = NameHistory(
            user_id=user.id,
            thread_id="own-thread",
            category="人名",
            name="林知夏",
            reference="知夏",
            moral="清朗明亮",
            score_total=90,
        )
        other_item = NameHistory(
            user_id=other.id,
            thread_id="other-thread",
            category="人名",
            name="陈望舒",
            reference="望舒",
            moral="温润从容",
            score_total=91,
        )
        session.add_all([own_item, other_item])
        await session.commit()
        history_ids = [own_item.id, other_item.id]

    response = await client.post("/history/compare", json={"history_ids": history_ids}, headers=auth_headers(user.id))
    assert response.status_code == 404


