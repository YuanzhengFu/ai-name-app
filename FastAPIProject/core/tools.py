import asyncio


WHOIS_SERVERS = {
    ".com": "whois.verisign-grs.com",
    ".net": "whois.verisign-grs.com",
    ".cn": "whois.cnnic.cn",
    ".com.cn": "whois.cnnic.cn",
}


def _normalize_domain(domain: str, default_suffix: str = ".com") -> str:
    value = str(domain or "").strip().lower()
    if not value:
        return ""
    if "://" in value:
        value = value.split("://", 1)[1]
    value = value.split("/", 1)[0].split("?", 1)[0].strip(".")
    if "." not in value:
        value = f"{value}{default_suffix}"
    return value


def _domain_suffix(domain: str) -> str:
    for suffix in sorted(WHOIS_SERVERS, key=len, reverse=True):
        if domain.endswith(suffix):
            return suffix
    return ""


def _is_available_response(result: str) -> bool:
    lowered = result.lower()
    return any(
        marker in lowered
        for marker in (
            "no match for",
            "no match",
            "not found",
            "no entries found",
            "the queried object does not exist",
            "no matching record",
        )
    )


async def check_domain(domain: str):
    domain = _normalize_domain(domain)
    if not domain:
        return "No domain provided"

    suffix = _domain_suffix(domain)
    server = WHOIS_SERVERS.get(suffix)
    if not server:
        return f"Unsupported suffix: {domain}"

    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(server, 43),
            timeout=3.0,
        )
        writer.write((domain + "\r\n").encode("utf-8"))
        await writer.drain()

        response = await asyncio.wait_for(reader.read(), timeout=10.0)
        writer.close()
        await writer.wait_closed()

        result = response.decode("utf-8", errors="ignore")
        return "available" if _is_available_response(result) else "registered"
    except asyncio.TimeoutError:
        return "query_timeout"
    except Exception as exc:
        return f"query_failed: {exc}"


async def check_com_domain(domain: str):
    domain = _normalize_domain(domain, ".com")
    if not domain.endswith(".com"):
        return "unsupported_com_only"
    return await check_domain(domain)
