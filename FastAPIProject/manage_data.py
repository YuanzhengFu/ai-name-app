import argparse
import asyncio
import json
import socket
from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy import text

from core import admin_data_service
from models import AsyncSessionFactory, engine
from settings import CHROMA_RAG_DB_PATH, LANGGRAPH_DB_URI, RABBITMQ_URL, REDIS_URL, UPLOAD_DIR


def print_json(data):
    print(json.dumps(data, ensure_ascii=False, indent=2, default=str))


def parse_data(raw_items: list[str]) -> dict:
    data = {}
    for item in raw_items:
        if "=" not in item:
            raise SystemExit(f"Invalid --set value: {item}. Use key=value.")
        key, value = item.split("=", 1)
        data[key] = parse_value(value)
    return data


def parse_value(value: str):
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "none"}:
        return None
    try:
        return int(value)
    except ValueError:
        return value


async def command_list(args):
    async with AsyncSessionFactory() as session:
        result = await admin_data_service.list_records(session, args.table, args.keyword, args.limit, args.offset)
        print_json(result)


async def command_get(args):
    async with AsyncSessionFactory() as session:
        result = await admin_data_service.get_record(session, args.table, args.id)
        print_json(result)


async def command_create(args):
    data = parse_data(args.set)
    if not args.apply:
        print_json({"dry_run": True, "action": "create", "table": args.table, "data": data})
        return
    async with AsyncSessionFactory() as session:
        result = await admin_data_service.create_record(session, args.table, data)
        print_json(result)


async def command_update(args):
    data = parse_data(args.set)
    if not args.apply:
        print_json({"dry_run": True, "action": "update", "table": args.table, "id": args.id, "data": data})
        return
    async with AsyncSessionFactory() as session:
        result = await admin_data_service.update_record(session, args.table, args.id, data)
        print_json(result)


async def command_delete(args):
    if not args.apply:
        print_json({"dry_run": True, "action": "delete", "table": args.table, "id": args.id})
        return
    async with AsyncSessionFactory() as session:
        result = await admin_data_service.delete_record(session, args.table, args.id)
        print_json(result)


def check_tcp(url: str, default_port: int) -> dict:
    parsed = urlparse(url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or default_port
    try:
        with socket.create_connection((host, port), timeout=2):
            return {"host": host, "port": port, "ok": True}
    except OSError as exc:
        return {"host": host, "port": port, "ok": False, "error": str(exc)}


async def command_health(args):
    checks = {}
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["mysql_business_db"] = {"ok": True}
    except Exception as exc:
        checks["mysql_business_db"] = {"ok": False, "error": str(exc)}

    checks["langgraph_postgres"] = check_tcp(LANGGRAPH_DB_URI, 5432)
    checks["redis"] = check_tcp(REDIS_URL, 6379)
    checks["rabbitmq"] = check_tcp(RABBITMQ_URL, 5672)
    checks["uploads_path"] = {"path": str(Path(UPLOAD_DIR)), "exists": Path(UPLOAD_DIR).exists()}
    checks["chroma_path"] = {"path": str(Path(CHROMA_RAG_DB_PATH)), "exists": Path(CHROMA_RAG_DB_PATH).exists()}
    print_json(checks)


def build_parser():
    parser = argparse.ArgumentParser(description="Admin data maintenance tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    tables = subparsers.add_parser("tables", help="List managed tables")
    tables.set_defaults(func=lambda args: print_json({"items": admin_data_service.table_configs()}))

    list_cmd = subparsers.add_parser("list", help="List records")
    list_cmd.add_argument("table")
    list_cmd.add_argument("--keyword", default=None)
    list_cmd.add_argument("--limit", type=int, default=20)
    list_cmd.add_argument("--offset", type=int, default=0)
    list_cmd.set_defaults(func=lambda args: asyncio.run(command_list(args)))

    get_cmd = subparsers.add_parser("get", help="Get one record")
    get_cmd.add_argument("table")
    get_cmd.add_argument("id", type=int)
    get_cmd.set_defaults(func=lambda args: asyncio.run(command_get(args)))

    create_cmd = subparsers.add_parser("create", help="Create a record")
    create_cmd.add_argument("table")
    create_cmd.add_argument("--set", action="append", default=[], required=True)
    create_cmd.add_argument("--apply", action="store_true")
    create_cmd.set_defaults(func=lambda args: asyncio.run(command_create(args)))

    update_cmd = subparsers.add_parser("update", help="Update a record")
    update_cmd.add_argument("table")
    update_cmd.add_argument("id", type=int)
    update_cmd.add_argument("--set", action="append", default=[], required=True)
    update_cmd.add_argument("--apply", action="store_true")
    update_cmd.set_defaults(func=lambda args: asyncio.run(command_update(args)))

    delete_cmd = subparsers.add_parser("delete", help="Delete a record")
    delete_cmd.add_argument("table")
    delete_cmd.add_argument("id", type=int)
    delete_cmd.add_argument("--apply", action="store_true")
    delete_cmd.set_defaults(func=lambda args: asyncio.run(command_delete(args)))

    health_cmd = subparsers.add_parser("health", help="Check runtime dependencies")
    health_cmd.set_defaults(func=lambda args: asyncio.run(command_health(args)))
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
