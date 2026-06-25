from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy import String, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from models.knowledge_task import KnowledgeTask
from models.membership import CreditTransaction, MembershipPlan, RechargeOrder, UserMembership
from models.name_history import NameHistory
from models.naming_preference_template import NamingPreferenceTemplate
from models.naming_project import NamingProject
from models.user import EmailCode, User


@dataclass(frozen=True)
class TableConfig:
    name: str
    label: str
    model: type[DeclarativeBase]
    visible_columns: tuple[str, ...]
    editable_columns: tuple[str, ...]
    create_columns: tuple[str, ...]
    search_columns: tuple[str, ...] = ()


TABLES: dict[str, TableConfig] = {
    "user": TableConfig(
        name="user",
        label="用户",
        model=User,
        visible_columns=("id", "email", "username", "is_admin", "created_time"),
        editable_columns=("email", "username", "is_admin"),
        create_columns=("email", "username", "password", "is_admin"),
        search_columns=("email", "username"),
    ),
    "email_code": TableConfig(
        name="email_code",
        label="邮箱验证码",
        model=EmailCode,
        visible_columns=("id", "email", "code", "created_time"),
        editable_columns=("email", "code", "created_time"),
        create_columns=("email", "code", "created_time"),
        search_columns=("email", "code"),
    ),
    "naming_project": TableConfig(
        name="naming_project",
        label="命名项目",
        model=NamingProject,
        visible_columns=("id", "user_id", "title", "category", "description", "status", "created_time", "updated_time"),
        editable_columns=("title", "category", "description", "status"),
        create_columns=("user_id", "title", "category", "description", "status"),
        search_columns=("title", "category", "description", "status"),
    ),
    "name_history": TableConfig(
        name="name_history",
        label="起名历史",
        model=NameHistory,
        visible_columns=(
            "id",
            "user_id",
            "project_id",
            "thread_id",
            "category",
            "name",
            "reference",
            "moral",
            "domain",
            "domain_status",
            "domain_checks",
            "brand_warning",
            "pinyin",
            "english_name",
            "abbreviation",
            "score_total",
            "rhythm_score",
            "meaning_score",
            "spread_score",
            "domain_score",
            "score_explanation",
            "surname",
            "gender",
            "length",
            "other",
            "exclude",
            "is_favorite",
            "created_time",
            "updated_time",
        ),
        editable_columns=(
            "project_id",
            "category",
            "name",
            "reference",
            "moral",
            "domain",
            "domain_status",
            "domain_checks",
            "brand_warning",
            "pinyin",
            "english_name",
            "abbreviation",
            "score_total",
            "rhythm_score",
            "meaning_score",
            "spread_score",
            "domain_score",
            "score_explanation",
            "surname",
            "gender",
            "length",
            "other",
            "exclude",
            "is_favorite",
        ),
        create_columns=(
            "user_id",
            "project_id",
            "thread_id",
            "category",
            "name",
            "reference",
            "moral",
            "domain",
            "domain_status",
            "domain_checks",
            "brand_warning",
            "pinyin",
            "english_name",
            "abbreviation",
            "score_total",
            "rhythm_score",
            "meaning_score",
            "spread_score",
            "domain_score",
            "score_explanation",
            "surname",
            "gender",
            "length",
            "other",
            "exclude",
            "is_favorite",
        ),
        search_columns=("thread_id", "category", "name", "reference", "moral", "domain", "pinyin", "english_name", "abbreviation", "other"),
    ),
    "naming_preference_template": TableConfig(
        name="naming_preference_template",
        label="起名偏好模板",
        model=NamingPreferenceTemplate,
        visible_columns=("id", "user_id", "title", "category", "preferences", "is_default", "created_time", "updated_time"),
        editable_columns=("title", "category", "preferences", "is_default"),
        create_columns=("user_id", "title", "category", "preferences", "is_default"),
        search_columns=("title", "category"),
    ),
    "knowledge_task": TableConfig(
        name="knowledge_task",
        label="知识库任务",
        model=KnowledgeTask,
        visible_columns=("id", "user_id", "project_id", "filename", "file_path", "status", "error_message", "is_active", "chunk_count", "parse_log", "created_time", "updated_time"),
        editable_columns=("project_id", "filename", "file_path", "status", "error_message", "is_active", "chunk_count", "parse_log"),
        create_columns=("user_id", "project_id", "filename", "file_path", "status", "error_message", "is_active", "chunk_count", "parse_log"),
        search_columns=("filename", "file_path", "status", "error_message", "parse_log"),
    ),
    "membership_plan": TableConfig(
        name="membership_plan",
        label="会员套餐",
        model=MembershipPlan,
        visible_columns=("id", "name", "description", "price_cents", "credits", "validity_days", "is_active", "sort_order", "created_time", "updated_time"),
        editable_columns=("name", "description", "price_cents", "credits", "validity_days", "is_active", "sort_order"),
        create_columns=("name", "description", "price_cents", "credits", "validity_days", "is_active", "sort_order"),
        search_columns=("name", "description"),
    ),
    "user_membership": TableConfig(
        name="user_membership",
        label="用户会员",
        model=UserMembership,
        visible_columns=("id", "user_id", "plan_name", "credit_balance", "total_recharged", "total_consumed", "expires_at", "created_time", "updated_time"),
        editable_columns=("plan_name", "credit_balance", "total_recharged", "total_consumed", "expires_at"),
        create_columns=("user_id", "plan_name", "credit_balance", "total_recharged", "total_consumed", "expires_at"),
        search_columns=("plan_name",),
    ),
    "credit_transaction": TableConfig(
        name="credit_transaction",
        label="额度流水",
        model=CreditTransaction,
        visible_columns=("id", "user_id", "change_amount", "balance_after", "transaction_type", "source", "remark", "operator_id", "created_time"),
        editable_columns=("remark",),
        create_columns=("user_id", "change_amount", "balance_after", "transaction_type", "source", "remark", "operator_id"),
        search_columns=("transaction_type", "source", "remark"),
    ),
    "recharge_order": TableConfig(
        name="recharge_order",
        label="充值订单",
        model=RechargeOrder,
        visible_columns=(
            "id",
            "user_id",
            "plan_id",
            "plan_name",
            "amount_cents",
            "credits",
            "status",
            "provider",
            "provider_trade_no",
            "payment_payload",
            "failure_reason",
            "paid_time",
            "refunded_time",
            "created_time",
            "updated_time",
        ),
        editable_columns=("status", "provider_trade_no", "payment_payload", "failure_reason", "paid_time", "refunded_time"),
        create_columns=("user_id", "plan_id", "plan_name", "amount_cents", "credits", "status", "provider", "provider_trade_no", "payment_payload", "failure_reason"),
        search_columns=("plan_name", "status", "provider", "provider_trade_no", "failure_reason"),
    ),
}


def table_configs() -> list[dict[str, Any]]:
    return [
        {
            "name": config.name,
            "label": config.label,
            "primary_key": "id",
            "columns": list(config.visible_columns),
            "editable_columns": list(config.editable_columns),
            "create_columns": list(config.create_columns),
        }
        for config in TABLES.values()
    ]


def get_table_config(table: str) -> TableConfig:
    config = TABLES.get(table)
    if not config:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Data table not found")
    return config


def _serialize(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def serialize_record(record: Any, config: TableConfig) -> dict[str, Any]:
    return {column: _serialize(getattr(record, column)) for column in config.visible_columns}


def _coerce_value(model: type[DeclarativeBase], column: str, value: Any) -> Any:
    if value == "":
        nullable = getattr(model, column).property.columns[0].nullable
        return None if nullable else value

    column_type = getattr(model, column).property.columns[0].type
    if isinstance(column_type, String):
        return str(value) if value is not None else value
    try:
        python_type = getattr(column_type, "python_type", None)
    except NotImplementedError:
        return value
    if python_type is bool:
        if isinstance(value, bool):
            return value
        return str(value).lower() in {"1", "true", "yes", "on", "启用", "是"}
    if python_type is int and value is not None:
        return int(value)
    if python_type is datetime and isinstance(value, str) and value:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    return value


def filter_payload(config: TableConfig, payload: dict[str, Any], allowed_columns: tuple[str, ...]) -> dict[str, Any]:
    blocked = {"_password"}
    illegal = [key for key in payload if key not in allowed_columns or key in blocked]
    if illegal:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Fields are not allowed for {config.name}: {', '.join(sorted(illegal))}",
        )
    return {key: _coerce_value(config.model, key, value) for key, value in payload.items() if key != "password"}


async def list_records(
    session: AsyncSession,
    table: str,
    keyword: str | None,
    limit: int,
    offset: int,
) -> dict[str, Any]:
    config = get_table_config(table)
    conditions = []
    if keyword and config.search_columns:
        pattern = f"%{keyword}%"
        conditions.append(or_(*(getattr(config.model, column).like(pattern) for column in config.search_columns)))

    total = await session.scalar(select(func.count()).select_from(config.model).where(*conditions))
    result = await session.execute(
        select(config.model)
        .where(*conditions)
        .order_by(getattr(config.model, "id").desc())
        .limit(limit)
        .offset(offset)
    )
    return {
        "table": config.name,
        "items": [serialize_record(item, config) for item in result.scalars().all()],
        "total": int(total or 0),
        "limit": limit,
        "offset": offset,
    }


async def get_record(session: AsyncSession, table: str, record_id: int) -> dict[str, Any]:
    config = get_table_config(table)
    record = await session.get(config.model, record_id)
    if not record:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Record not found")
    return {"table": config.name, "item": serialize_record(record, config)}


async def create_record(session: AsyncSession, table: str, payload: dict[str, Any]) -> dict[str, Any]:
    config = get_table_config(table)
    values = filter_payload(config, payload, config.create_columns)
    if config.name == "user":
        if not payload.get("password"):
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="User password is required")
        record = User(**values, password=str(payload["password"]))
    else:
        record = config.model(**values)
    session.add(record)
    await session.commit()
    await session.refresh(record)
    return {"table": config.name, "item": serialize_record(record, config)}


async def update_record(session: AsyncSession, table: str, record_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    config = get_table_config(table)
    record = await session.get(config.model, record_id)
    if not record:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Record not found")

    values = filter_payload(config, payload, config.editable_columns)
    for key, value in values.items():
        setattr(record, key, value)
    await session.commit()
    await session.refresh(record)
    return {"table": config.name, "item": serialize_record(record, config)}


async def delete_record(session: AsyncSession, table: str, record_id: int, current_admin_id: int | None = None) -> dict[str, str]:
    config = get_table_config(table)
    record = await session.get(config.model, record_id)
    if not record:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Record not found")

    if config.name == "user":
        if current_admin_id == record_id:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Cannot delete the current administrator")
        related_checks = [
            (NameHistory, NameHistory.user_id == record_id, "name_history"),
            (NamingPreferenceTemplate, NamingPreferenceTemplate.user_id == record_id, "naming_preference_template"),
            (KnowledgeTask, KnowledgeTask.user_id == record_id, "knowledge_task"),
            (NamingProject, NamingProject.user_id == record_id, "naming_project"),
            (UserMembership, UserMembership.user_id == record_id, "user_membership"),
            (CreditTransaction, CreditTransaction.user_id == record_id, "credit_transaction"),
            (RechargeOrder, RechargeOrder.user_id == record_id, "recharge_order"),
        ]
        for model, condition, related_table in related_checks:
            count = await session.scalar(select(func.count()).select_from(model).where(condition))
            if count:
                raise HTTPException(
                    status_code=HTTP_400_BAD_REQUEST,
                    detail=f"Cannot delete user with related {related_table} records",
                )

    await session.delete(record)
    await session.commit()
    return {"message": "Record deleted"}
