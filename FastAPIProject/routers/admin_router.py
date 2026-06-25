from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio.session import AsyncSession

from dependencies import get_session, require_admin
from core import admin_data_service
from models.knowledge_task import KnowledgeTask
from models.membership import CreditTransaction, RechargeOrder, UserMembership
from models.name_history import NameHistory
from models.user import User
from core.membership_service import MembershipService, account_to_dict
from repository.history_repo import history_to_dict
from routers import rag_router
from schemas.admin_schemas import (
    AdminGenerationStatsOut,
    AdminDataCreateIn,
    AdminDataDeleteOut,
    AdminDataRecordListOut,
    AdminDataRecordOut,
    AdminDataTableListOut,
    AdminDataUpdateIn,
    AdminKnowledgeTaskBatchRetryIn,
    AdminKnowledgeTaskBatchRetryOut,
    AdminKnowledgeTaskListOut,
    AdminNameHistoryListOut,
    AdminResetPasswordIn,
    AdminUserListOut,
    KnowledgeTaskOut,
    KnowledgeTaskStatsOut,
)
from schemas.membership_schemas import (
    AdminCreditAdjustIn,
    AdminCreditAdjustOut,
    MembershipPlanCreateIn,
    MembershipPlanOut,
    MembershipPlanUpdateIn,
    PaymentRefundIn,
    RechargeOrderOut,
)
from schemas.user_schemas import UserSchema
from starlette.status import HTTP_404_NOT_FOUND

router = APIRouter(prefix="/admin", tags=["admin"])


INDUSTRY_KEYWORDS = {
    "科技互联网": ["科技", "互联网", "软件", "ai", "人工智能", "智能", "数据", "云", "saas"],
    "餐饮食品": ["餐饮", "食品", "咖啡", "茶", "奶茶", "烘焙", "火锅", "料理"],
    "教育培训": ["教育", "培训", "学校", "课程", "学习", "儿童", "留学"],
    "美妆服饰": ["美妆", "护肤", "服装", "女装", "男装", "穿搭", "时尚"],
    "健康医疗": ["健康", "医疗", "医美", "养生", "药", "诊所", "康复"],
    "文化创意": ["文化", "文创", "设计", "艺术", "摄影", "传媒", "音乐"],
    "家居生活": ["家居", "家具", "生活", "母婴", "宠物", "日用"],
    "金融商务": ["金融", "投资", "咨询", "财税", "商务", "管理", "法律"],
}

STYLE_KEYWORDS = {
    "简约现代": ["简约", "现代", "极简", "清爽", "高级", "大气"],
    "国风古典": ["国风", "古风", "古典", "诗词", "传统", "雅致"],
    "可爱治愈": ["可爱", "治愈", "萌", "温暖", "亲切", "甜"],
    "高端专业": ["高端", "专业", "稳重", "可信", "品质", "精英"],
    "年轻潮流": ["年轻", "潮流", "个性", "酷", "活力", "新锐"],
    "自然清新": ["自然", "清新", "绿色", "环保", "森系", "植物"],
}


def date_key(value) -> str:
    return value.isoformat() if hasattr(value, "isoformat") else str(value)[:10]


def empty_daily_counts(days: int) -> dict[str, int]:
    first_day = datetime.now().date() - timedelta(days=days - 1)
    return {(first_day + timedelta(days=index)).isoformat(): 0 for index in range(days)}


def build_daily_items(counts: dict[str, int], value_key: str = "count") -> list[dict]:
    return [{"date": day, value_key: value} for day, value in counts.items()]


def build_daily_rag_items(total_counts: dict[str, int], failed_counts: dict[str, int]) -> list[dict]:
    return [
        {
            "date": day,
            "total": total,
            "failed": failed_counts.get(day, 0),
            "failure_rate": round(failed_counts.get(day, 0) * 100 / total, 2) if total else 0,
        }
        for day, total in total_counts.items()
    ]


def keyword_stats(rows: list[str | None], keyword_map: dict[str, list[str]], limit: int = 8) -> list[dict]:
    counts = {name: 0 for name in keyword_map}
    matched_total = 0
    for row in rows:
        text = (row or "").lower()
        if not text:
            continue
        matched_names = [
            name
            for name, keywords in keyword_map.items()
            if any(keyword.lower() in text for keyword in keywords)
        ]
        for name in matched_names:
            counts[name] += 1
        matched_total += len(matched_names)

    items = [
        {
            "name": name,
            "count": count,
            "percent": round(count * 100 / matched_total, 2) if matched_total else 0,
        }
        for name, count in counts.items()
        if count > 0
    ]
    return sorted(items, key=lambda item: item["count"], reverse=True)[:limit]


def admin_knowledge_task_to_dict(task: KnowledgeTask, user: User | None = None) -> dict:
    return {
        "id": task.id,
        "user_id": task.user_id,
        "project_id": task.project_id,
        "username": user.username if user else "",
        "email": user.email if user else "",
        "filename": task.filename,
        "status": task.status,
        "error_message": task.error_message,
        "is_active": task.is_active,
        "chunk_count": task.chunk_count,
        "parse_log": task.parse_log,
        "created_time": task.created_time,
        "updated_time": task.updated_time,
    }


@router.get("/me", response_model=UserSchema)
async def admin_me(current_admin: User = Depends(require_admin)):
    return current_admin


@router.get("/data/tables", response_model=AdminDataTableListOut)
async def admin_data_tables(current_admin: User = Depends(require_admin)):
    return {"items": admin_data_service.table_configs()}


@router.get("/data/{table}", response_model=AdminDataRecordListOut)
async def admin_data_list_records(
    table: str,
    keyword: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    return await admin_data_service.list_records(session, table, keyword, limit, offset)


@router.get("/data/{table}/{record_id}", response_model=AdminDataRecordOut)
async def admin_data_get_record(
    table: str,
    record_id: int,
    current_admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    return await admin_data_service.get_record(session, table, record_id)


@router.post("/data/{table}", response_model=AdminDataRecordOut)
async def admin_data_create_record(
    table: str,
    data: AdminDataCreateIn,
    current_admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    return await admin_data_service.create_record(session, table, data.data)


@router.patch("/data/{table}/{record_id}", response_model=AdminDataRecordOut)
async def admin_data_update_record(
    table: str,
    record_id: int,
    data: AdminDataUpdateIn,
    current_admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    return await admin_data_service.update_record(session, table, record_id, data.data)


@router.delete("/data/{table}/{record_id}", response_model=AdminDataDeleteOut)
async def admin_data_delete_record(
    table: str,
    record_id: int,
    current_admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    return await admin_data_service.delete_record(session, table, record_id, current_admin.id)


@router.get("/users", response_model=AdminUserListOut)
async def list_users(
    keyword: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    conditions = []
    if keyword:
        pattern = f"%{keyword}%"
        conditions.append(or_(User.email.like(pattern), User.username.like(pattern)))

    total = await session.scalar(select(func.count()).select_from(User).where(*conditions))
    result = await session.execute(
        select(User)
        .where(*conditions)
        .order_by(User.id.desc())
        .limit(limit)
        .offset(offset)
    )
    users = list(result.scalars().all())
    user_ids = [user.id for user in users]

    history_counts: dict[int, int] = {}
    knowledge_task_counts: dict[int, int] = {}
    membership_map: dict[int, UserMembership] = {}
    if user_ids:
        history_rows = await session.execute(
            select(NameHistory.user_id, func.count()).where(NameHistory.user_id.in_(user_ids)).group_by(NameHistory.user_id)
        )
        history_counts = {user_id: int(count or 0) for user_id, count in history_rows.all()}

        task_rows = await session.execute(
            select(KnowledgeTask.user_id, func.count())
            .where(KnowledgeTask.user_id.in_(user_ids))
            .group_by(KnowledgeTask.user_id)
        )
        knowledge_task_counts = {user_id: int(count or 0) for user_id, count in task_rows.all()}

        membership_rows = await session.execute(
            select(UserMembership).where(UserMembership.user_id.in_(user_ids))
        )
        membership_map = {item.user_id: item for item in membership_rows.scalars().all()}

    items = [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_admin": user.is_admin,
            "history_count": history_counts.get(user.id, 0),
            "knowledge_task_count": knowledge_task_counts.get(user.id, 0),
            "plan_name": membership_map[user.id].plan_name if user.id in membership_map else "免费版",
            "credit_balance": membership_map[user.id].credit_balance if user.id in membership_map else 0,
            "total_recharged": membership_map[user.id].total_recharged if user.id in membership_map else 0,
            "total_consumed": membership_map[user.id].total_consumed if user.id in membership_map else 0,
        }
        for user in users
    ]
    return {"items": items, "total": int(total or 0), "limit": limit, "offset": offset}


@router.get("/membership/plans", response_model=list[MembershipPlanOut])
async def admin_list_membership_plans(
    include_inactive: bool = Query(True),
    current_admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    return await MembershipService(session).list_plans(include_inactive=include_inactive)


@router.post("/membership/plans", response_model=MembershipPlanOut)
async def admin_create_membership_plan(
    data: MembershipPlanCreateIn,
    current_admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    return await MembershipService(session).create_plan(data)


@router.patch("/membership/plans/{plan_id}", response_model=MembershipPlanOut)
async def admin_update_membership_plan(
    plan_id: int,
    data: MembershipPlanUpdateIn,
    current_admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    return await MembershipService(session).update_plan(plan_id, data)


@router.post("/users/{user_id}/credits", response_model=AdminCreditAdjustOut)
async def admin_adjust_user_credits(
    user_id: int,
    data: AdminCreditAdjustIn,
    current_admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    target_user = await session.get(User, user_id)
    if not target_user:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="用户不存在")

    account, transaction = await MembershipService(session).admin_adjust(
        user_id=user_id,
        amount=data.amount,
        reason=data.reason,
        operator_id=current_admin.id,
    )
    return {"account": account_to_dict(account), "transaction": transaction}


@router.post("/users/{user_id}/password")
async def admin_reset_user_password(
    user_id: int,
    data: AdminResetPasswordIn,
    current_admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    target_user = await session.get(User, user_id)
    if not target_user:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="User not found")
    target_user.password = data.new_password
    session.add(target_user)
    await session.commit()
    return {"message": "Password reset successfully"}


@router.post("/membership/orders/{order_id}/refund", response_model=RechargeOrderOut)
async def admin_refund_recharge_order(
    order_id: int,
    data: PaymentRefundIn,
    current_admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    order, _ = await MembershipService(session).refund_order(order_id, data.reason)
    return order


@router.get("/name-histories", response_model=AdminNameHistoryListOut)
async def list_name_histories(
    user_id: int | None = Query(None),
    category: str | None = Query(None),
    keyword: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    conditions = []
    if user_id is not None:
        conditions.append(NameHistory.user_id == user_id)
    if category:
        conditions.append(NameHistory.category == category)
    if keyword:
        pattern = f"%{keyword}%"
        conditions.append(
            or_(
                NameHistory.name.like(pattern),
                NameHistory.reference.like(pattern),
                NameHistory.moral.like(pattern),
                NameHistory.other.like(pattern),
            )
        )

    total = await session.scalar(select(func.count()).select_from(NameHistory).where(*conditions))
    result = await session.execute(
        select(NameHistory)
        .where(*conditions)
        .order_by(NameHistory.created_time.desc(), NameHistory.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return {
        "items": [history_to_dict(item) for item in result.scalars().all()],
        "total": int(total or 0),
        "limit": limit,
        "offset": offset,
    }


@router.get("/generation-stats", response_model=AdminGenerationStatsOut)
async def generation_stats(
    current_admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    days = 7
    first_day = today_start - timedelta(days=days - 1)

    total_users = await session.scalar(select(func.count()).select_from(User))
    total_generations = await session.scalar(select(func.count()).select_from(NameHistory))
    total_rag_tasks = await session.scalar(select(func.count()).select_from(KnowledgeTask))
    total_failed_rag_tasks = await session.scalar(
        select(func.count()).select_from(KnowledgeTask).where(KnowledgeTask.status == "failed")
    )
    today_generations = await session.scalar(
        select(func.count()).select_from(NameHistory).where(NameHistory.created_time >= today_start)
    )
    today_new_users = await session.scalar(
        select(func.count()).select_from(User).where(User.created_time >= today_start)
    )
    today_credit_consumed = await session.scalar(
        select(func.sum(-CreditTransaction.change_amount))
        .where(
            CreditTransaction.transaction_type == "consume",
            CreditTransaction.created_time >= today_start,
        )
    )

    paid_users = await session.scalar(
        select(func.count(func.distinct(RechargeOrder.user_id))).where(RechargeOrder.status == "paid")
    )
    paid_orders = await session.scalar(
        select(func.count()).select_from(RechargeOrder).where(RechargeOrder.status == "paid")
    )
    paid_amount_cents = await session.scalar(
        select(func.sum(RechargeOrder.amount_cents)).where(RechargeOrder.status == "paid")
    )
    user_count = int(total_users or 0)
    paid_conversion = {
        "paid_users": int(paid_users or 0),
        "paid_orders": int(paid_orders or 0),
        "paid_amount_cents": int(paid_amount_cents or 0),
        "conversion_rate": round(int(paid_users or 0) * 100 / user_count, 2) if user_count else 0,
    }

    category_rows = await session.execute(
        select(NameHistory.category, func.count()).group_by(NameHistory.category)
    )
    category_counts = {category: int(count or 0) for category, count in category_rows.all()}

    ordered_categories = ["人名", "企业名", "宠物名"]
    extra_categories = sorted(category for category in category_counts if category not in ordered_categories)
    total_count = int(total_generations or 0)
    category_stats = []
    for category in [*ordered_categories, *extra_categories]:
        count = category_counts.get(category, 0)
        percent = round(count * 100 / total_count, 2) if total_count else 0
        category_stats.append({"category": category, "count": count, "percent": percent})

    daily_generation_counts = empty_daily_counts(days)
    daily_generation_rows = await session.execute(
        select(func.date(NameHistory.created_time), func.count())
        .where(NameHistory.created_time >= first_day)
        .group_by(func.date(NameHistory.created_time))
    )
    for day, count in daily_generation_rows.all():
        daily_generation_counts[date_key(day)] = int(count or 0)

    daily_new_user_counts = empty_daily_counts(days)
    daily_new_user_rows = await session.execute(
        select(func.date(User.created_time), func.count())
        .where(User.created_time >= first_day)
        .group_by(func.date(User.created_time))
    )
    for day, count in daily_new_user_rows.all():
        daily_new_user_counts[date_key(day)] = int(count or 0)

    daily_paid_user_counts = empty_daily_counts(days)
    daily_paid_user_rows = await session.execute(
        select(func.date(RechargeOrder.paid_time), func.count(func.distinct(RechargeOrder.user_id)))
        .where(RechargeOrder.status == "paid", RechargeOrder.paid_time >= first_day)
        .group_by(func.date(RechargeOrder.paid_time))
    )
    for day, count in daily_paid_user_rows.all():
        daily_paid_user_counts[date_key(day)] = int(count or 0)

    daily_credit_counts = empty_daily_counts(days)
    daily_credit_rows = await session.execute(
        select(func.date(CreditTransaction.created_time), func.sum(-CreditTransaction.change_amount))
        .where(
            CreditTransaction.transaction_type == "consume",
            CreditTransaction.created_time >= first_day,
        )
        .group_by(func.date(CreditTransaction.created_time))
    )
    for day, credits in daily_credit_rows.all():
        daily_credit_counts[date_key(day)] = int(credits or 0)

    failed_task_counts = empty_daily_counts(days)
    failed_task_rows = await session.execute(
        select(func.date(KnowledgeTask.updated_time), func.count())
        .where(KnowledgeTask.status == "failed", KnowledgeTask.updated_time >= first_day)
        .group_by(func.date(KnowledgeTask.updated_time))
    )
    for day, count in failed_task_rows.all():
        failed_task_counts[date_key(day)] = int(count or 0)

    daily_rag_task_counts = empty_daily_counts(days)
    daily_rag_task_rows = await session.execute(
        select(func.date(KnowledgeTask.updated_time), func.count())
        .where(KnowledgeTask.updated_time >= first_day)
        .group_by(func.date(KnowledgeTask.updated_time))
    )
    for day, count in daily_rag_task_rows.all():
        daily_rag_task_counts[date_key(day)] = int(count or 0)

    company_text_rows = await session.execute(
        select(NameHistory.other)
        .where(NameHistory.category == "企业名")
        .order_by(NameHistory.created_time.desc())
        .limit(500)
    )
    company_texts = list(company_text_rows.scalars().all())

    return {
        "total_users": int(total_users or 0),
        "total_generations": total_count,
        "today_generations": int(today_generations or 0),
        "category_stats": category_stats,
        "today_new_users": int(today_new_users or 0),
        "paid_conversion": paid_conversion,
        "today_credit_consumed": int(today_credit_consumed or 0),
        "rag_failure_rate": round(int(total_failed_rag_tasks or 0) * 100 / int(total_rag_tasks or 0), 2)
        if total_rag_tasks
        else 0,
        "daily_generations": build_daily_items(daily_generation_counts),
        "daily_new_users": build_daily_items(daily_new_user_counts),
        "daily_paid_users": build_daily_items(daily_paid_user_counts),
        "daily_credit_consumed": build_daily_items(daily_credit_counts, "credits"),
        "failed_task_trend": build_daily_items(failed_task_counts),
        "daily_rag_tasks": build_daily_rag_items(daily_rag_task_counts, failed_task_counts),
        "hot_industries": keyword_stats(company_texts, INDUSTRY_KEYWORDS),
        "hot_styles": keyword_stats(company_texts, STYLE_KEYWORDS),
    }


@router.get("/knowledge-tasks/stats", response_model=KnowledgeTaskStatsOut)
async def knowledge_task_stats(
    current_admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    total = await session.scalar(select(func.count()).select_from(KnowledgeTask))
    today = await session.scalar(
        select(func.count()).select_from(KnowledgeTask).where(KnowledgeTask.created_time >= today_start)
    )

    status_rows = await session.execute(
        select(KnowledgeTask.status, func.count()).group_by(KnowledgeTask.status)
    )
    status_counts = {status: int(count or 0) for status, count in status_rows.all()}

    recent_rows = await session.execute(
        select(KnowledgeTask, User)
        .join(User, User.id == KnowledgeTask.user_id)
        .order_by(KnowledgeTask.created_time.desc(), KnowledgeTask.id.desc())
        .limit(10)
    )
    recent_tasks = [
        admin_knowledge_task_to_dict(task, user)
        for task, user in recent_rows.all()
    ]

    return {
        "total": int(total or 0),
        "today": int(today or 0),
        "queued": status_counts.get("queued", 0),
        "processing": status_counts.get("processing", 0),
        "done": status_counts.get("done", 0),
        "failed": status_counts.get("failed", 0),
        "recent_tasks": recent_tasks,
    }


@router.get("/knowledge-tasks", response_model=AdminKnowledgeTaskListOut)
async def list_knowledge_tasks(
    status: str | None = Query(None),
    keyword: str | None = Query(None),
    failed_only: bool = Query(False),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    conditions = []
    if failed_only:
        conditions.append(KnowledgeTask.status == "failed")
    elif status:
        conditions.append(KnowledgeTask.status == status)
    if keyword:
        pattern = f"%{keyword}%"
        conditions.append(
            or_(
                KnowledgeTask.filename.like(pattern),
                KnowledgeTask.error_message.like(pattern),
                User.email.like(pattern),
                User.username.like(pattern),
            )
        )

    total = await session.scalar(
        select(func.count()).select_from(KnowledgeTask).join(User, User.id == KnowledgeTask.user_id).where(*conditions)
    )
    rows = await session.execute(
        select(KnowledgeTask, User)
        .join(User, User.id == KnowledgeTask.user_id)
        .where(*conditions)
        .order_by(KnowledgeTask.created_time.desc(), KnowledgeTask.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return {
        "items": [admin_knowledge_task_to_dict(task, user) for task, user in rows.all()],
        "total": int(total or 0),
        "limit": limit,
        "offset": offset,
    }


@router.post("/knowledge-tasks/{task_id}/reparse", response_model=KnowledgeTaskOut)
async def admin_reparse_knowledge_task(
    task_id: int,
    current_admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    task = await session.get(KnowledgeTask, task_id)
    if not task:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Knowledge task not found")
    if task.status == "processing":
        raise HTTPException(status_code=409, detail="Task is processing")

    task = await rag_router.enqueue_knowledge_task(task, session)
    user = await session.get(User, task.user_id)
    return admin_knowledge_task_to_dict(task, user)


@router.post("/knowledge-tasks/reparse", response_model=AdminKnowledgeTaskBatchRetryOut)
async def admin_reparse_knowledge_tasks(
    data: AdminKnowledgeTaskBatchRetryIn,
    current_admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    conditions = []
    if data.task_ids:
        conditions.append(KnowledgeTask.id.in_(data.task_ids))
    elif data.status:
        conditions.append(KnowledgeTask.status == data.status)

    rows = await session.execute(
        select(KnowledgeTask)
        .where(*conditions)
        .order_by(KnowledgeTask.created_time.desc(), KnowledgeTask.id.desc())
        .limit(data.limit)
    )

    items = []
    for task in rows.scalars().all():
        if task.status == "processing":
            items.append(
                {
                    "id": task.id,
                    "status": task.status,
                    "error_message": "Task is processing",
                    "retried": False,
                }
            )
            continue

        try:
            queued_task = await rag_router.enqueue_knowledge_task(task, session)
            items.append(
                {
                    "id": queued_task.id,
                    "status": queued_task.status,
                    "error_message": queued_task.error_message,
                    "retried": True,
                }
            )
        except HTTPException:
            await session.refresh(task)
            items.append(
                {
                    "id": task.id,
                    "status": task.status,
                    "error_message": task.error_message,
                    "retried": False,
                }
            )

    return {
        "items": items,
        "retried": sum(1 for item in items if item["retried"]),
        "failed": sum(1 for item in items if not item["retried"]),
    }
