from tests.conftest import auth_headers, create_user


async def test_preference_template_crud_is_scoped_to_current_user(client, session_maker):
    user = await create_user(session_maker, email="template-owner@example.com")
    other = await create_user(session_maker, email="template-other@example.com")

    payload = {
        "title": "国风水意象",
        "category": "人名",
        "preferences": {
            "category": "人名",
            "gender": "不限",
            "length": "两字",
            "style": "国风",
            "desired_meaning": "带水意象",
            "other": "国风、双字、带水意象",
            "exclude": ["强", "刚"],
        },
    }
    create_response = await client.post("/preference-templates", json=payload, headers=auth_headers(user.id))
    assert create_response.status_code == 200
    created = create_response.json()
    assert created["title"] == "国风水意象"
    assert created["preferences"]["category"] == "人名"
    assert created["preferences"]["exclude"] == ["强", "刚"]
    assert created["is_default"] is False

    list_response = await client.get("/preference-templates?category=人名", headers=auth_headers(user.id))
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1

    other_list_response = await client.get("/preference-templates", headers=auth_headers(other.id))
    assert other_list_response.status_code == 200
    assert other_list_response.json()["total"] == 0

    update_response = await client.patch(
        f"/preference-templates/{created['id']}",
        json={"title": "新版国风", "preferences": {**created["preferences"], "wuxing": "水"}},
        headers=auth_headers(user.id),
    )
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "新版国风"
    assert update_response.json()["preferences"]["wuxing"] == "水"

    other_delete_response = await client.delete(f"/preference-templates/{created['id']}", headers=auth_headers(other.id))
    assert other_delete_response.status_code == 404

    delete_response = await client.delete(f"/preference-templates/{created['id']}", headers=auth_headers(user.id))
    assert delete_response.status_code == 200

    empty_response = await client.get("/preference-templates", headers=auth_headers(user.id))
    assert empty_response.status_code == 200
    assert empty_response.json()["total"] == 0


async def test_preference_template_rejects_unknown_fields(client, session_maker):
    user = await create_user(session_maker, email="template-validation@example.com")

    response = await client.post(
        "/preference-templates",
        json={"title": "bad", "category": "人名", "preferences": {"token": "secret"}},
        headers=auth_headers(user.id),
    )
    assert response.status_code == 422


async def test_preference_template_default_is_unique_per_category(client, session_maker):
    user = await create_user(session_maker, email="template-default@example.com")
    base_preferences = {"category": "人名", "gender": "不限", "length": "两字"}

    first_response = await client.post(
        "/preference-templates",
        json={"title": "默认一", "category": "人名", "preferences": base_preferences, "is_default": True},
        headers=auth_headers(user.id),
    )
    assert first_response.status_code == 200
    first = first_response.json()
    assert first["is_default"] is True

    second_response = await client.post(
        "/preference-templates",
        json={"title": "默认二", "category": "人名", "preferences": {**base_preferences, "wuxing": "水"}, "is_default": True},
        headers=auth_headers(user.id),
    )
    assert second_response.status_code == 200
    second = second_response.json()
    assert second["is_default"] is True

    list_response = await client.get("/preference-templates?category=人名", headers=auth_headers(user.id))
    assert list_response.status_code == 200
    items = list_response.json()["items"]
    assert items[0]["id"] == second["id"]
    assert [item["is_default"] for item in items] == [True, False]

    update_response = await client.patch(
        f"/preference-templates/{first['id']}",
        json={"is_default": True},
        headers=auth_headers(user.id),
    )
    assert update_response.status_code == 200
    assert update_response.json()["is_default"] is True

    list_response = await client.get("/preference-templates?category=人名", headers=auth_headers(user.id))
    items = list_response.json()["items"]
    defaults = [item for item in items if item["is_default"]]
    assert len(defaults) == 1
    assert defaults[0]["id"] == first["id"]
