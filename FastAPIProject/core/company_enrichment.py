from __future__ import annotations

import asyncio
import re
from typing import Any

from core.tools import check_domain


DOMAIN_SUFFIXES = (".com", ".cn", ".com.cn", ".net")

BRAND_RISK_TERMS = {
    "alibaba": "包含知名品牌词，建议上线前人工核验商标和品牌冲突风险。",
    "tencent": "包含知名品牌词，建议上线前人工核验商标和品牌冲突风险。",
    "baidu": "包含知名品牌词，建议上线前人工核验商标和品牌冲突风险。",
    "huawei": "包含知名品牌词，建议上线前人工核验商标和品牌冲突风险。",
    "xiaomi": "包含知名品牌词，建议上线前人工核验商标和品牌冲突风险。",
    "jd": "包含知名品牌词，建议上线前人工核验商标和品牌冲突风险。",
    "bytedance": "包含知名品牌词，建议上线前人工核验商标和品牌冲突风险。",
    "apple": "包含知名品牌词，建议上线前人工核验商标和品牌冲突风险。",
    "google": "包含知名品牌词，建议上线前人工核验商标和品牌冲突风险。",
    "microsoft": "包含知名品牌词，建议上线前人工核验商标和品牌冲突风险。",
    "meta": "包含知名品牌词，建议上线前人工核验商标和品牌冲突风险。",
    "tesla": "包含知名品牌词，建议上线前人工核验商标和品牌冲突风险。",
}


def _domain_root(domain: str | None) -> str:
    value = str(domain or "").strip().lower()
    if not value:
        return ""
    if "://" in value:
        value = value.split("://", 1)[1]
    value = value.split("/", 1)[0].split("?", 1)[0]
    for suffix in sorted(DOMAIN_SUFFIXES, key=len, reverse=True):
        if value.endswith(suffix):
            return value[: -len(suffix)].strip(".")
    return value.split(".", 1)[0]


def _slug(value: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "", value.lower())
    return text[:32]


def _fallback_romanize(name: str) -> str:
    ascii_text = _slug(name)
    if ascii_text:
        return ascii_text
    return "".join(f"u{ord(char):x}" for char in name if char.strip())[:32]


def build_company_aliases(name: str, domain: str | None = None) -> dict[str, str]:
    root = _domain_root(domain)
    pinyin = ""
    try:
        from pypinyin import Style, lazy_pinyin  # type: ignore

        pinyin = "".join(lazy_pinyin(name, style=Style.NORMAL, errors="ignore"))
    except Exception:
        pinyin = root or _fallback_romanize(name)

    pinyin = _slug(pinyin) or root or _fallback_romanize(name)
    english_name = root or pinyin
    abbreviation = "".join(part[0] for part in re.findall(r"[a-z0-9]+", english_name.lower()))[:8]
    if not abbreviation:
        abbreviation = english_name[:6].upper()

    return {
        "pinyin": pinyin,
        "english_name": english_name,
        "abbreviation": abbreviation.upper(),
    }


def build_domain_candidates(item: dict[str, Any]) -> list[str]:
    root = _domain_root(item.get("domain"))
    if not root:
        aliases = build_company_aliases(str(item.get("name") or ""), "")
        root = aliases["english_name"]
    if not root:
        return []
    return [f"{root}{suffix}" for suffix in DOMAIN_SUFFIXES]


async def enrich_company_name(item: dict[str, Any]) -> dict[str, Any]:
    aliases = build_company_aliases(str(item.get("name") or ""), str(item.get("domain") or ""))
    item.update(aliases)

    domains = build_domain_candidates(item)
    statuses = await asyncio.gather(*(check_domain(domain) for domain in domains)) if domains else []
    item["domain_checks"] = [
        {"domain": domain, "suffix": domain.replace(_domain_root(domain), "", 1), "status": status}
        for domain, status in zip(domains, statuses)
    ]

    if not item.get("domain") and domains:
        item["domain"] = domains[0]
    if not item.get("domain_status") and item["domain_checks"]:
        item["domain_status"] = item["domain_checks"][0]["status"]

    item["brand_warning"] = build_brand_warning(item)
    return item


async def enrich_company_names(names: list[dict[str, Any]]) -> list[dict[str, Any]]:
    await asyncio.gather(*(enrich_company_name(item) for item in names))
    return names


def build_brand_warning(item: dict[str, Any]) -> str:
    haystack = " ".join(
        str(item.get(key) or "").lower()
        for key in ("name", "domain", "pinyin", "english_name", "abbreviation")
    )
    for term, warning in BRAND_RISK_TERMS.items():
        if term in haystack:
            return warning
    return "本地规则未发现明显冲突；正式使用前仍建议查询商标库和工商核名。"
