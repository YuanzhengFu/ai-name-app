from sqlalchemy import select

from core.company_enrichment import build_brand_warning, build_company_aliases, build_domain_candidates
from models.name_history import NameHistory
from routers import name_router
from tests.conftest import auth_headers, create_user


def test_company_aliases_use_domain_root_without_optional_pinyin_dependency():
    aliases = build_company_aliases("星澜科技", "xinglan.com")

    assert aliases["pinyin"] == "xinglan"
    assert aliases["english_name"] == "xinglan"
    assert aliases["abbreviation"] == "X"


def test_company_domain_candidates_cover_common_suffixes():
    item = {"name": "星澜科技", "domain": "xinglan.com"}

    assert build_domain_candidates(item) == [
        "xinglan.com",
        "xinglan.cn",
        "xinglan.com.cn",
        "xinglan.net",
    ]


def test_brand_warning_flags_known_brand_terms():
    warning = build_brand_warning({"name": "Apple智能", "domain": "appleai.com"})

    assert "知名品牌词" in warning


async def test_company_generation_persists_enrichment_fields(client, session_maker, monkeypatch):
    user = await create_user(session_maker)

    async def fake_generate_naming_v2(name_info, user_id):
        return {
            "thread_id": "thread-company",
            "names": {
                "names": [
                    {
                        "name": "星澜科技",
                        "reference": "星河与波澜",
                        "moral": "有科技感和开拓感",
                        "domain": "xinglan.com",
                        "domain_status": "available",
                        "domain_checks": [
                            {"domain": "xinglan.com", "suffix": ".com", "status": "available"},
                            {"domain": "xinglan.cn", "suffix": ".cn", "status": "registered"},
                        ],
                        "brand_warning": "本地规则未发现明显冲突；正式使用前仍建议查询商标库和工商核名。",
                        "pinyin": "xinglan",
                        "english_name": "xinglan",
                        "abbreviation": "X",
                    }
                ]
            },
        }

    monkeypatch.setattr(name_router, "generate_naming_v2", fake_generate_naming_v2)

    payload = {
        "category": "企业名",
        "surname": "",
        "gender": "不限",
        "length": "不限",
        "other": "科技品牌",
        "exclude": [],
        "industry": "科技",
        "style": "现代",
    }
    response = await client.post("/names/generate", json=payload, headers=auth_headers(user.id))

    assert response.status_code == 200
    body = response.json()
    item = body["names"][0]
    assert item["domain_checks"][0]["domain"] == "xinglan.com"
    assert item["pinyin"] == "xinglan"
    assert item["english_name"] == "xinglan"
    assert item["abbreviation"] == "X"
    assert item["brand_warning"]

    async with session_maker() as session:
        history = await session.scalar(select(NameHistory).where(NameHistory.user_id == user.id))
        assert history is not None
        assert "xinglan.cn" in history.domain_checks
        assert history.pinyin == "xinglan"
