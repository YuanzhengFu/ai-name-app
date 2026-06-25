from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, model_validator

from schemas.history_schemas import NameHistoryOut
from schemas.user_schemas import RawPasswordStr, UserSchema


class AdminUserOut(UserSchema):
    history_count: int = 0
    knowledge_task_count: int = 0
    plan_name: str = "免费版"
    credit_balance: int = 0
    total_recharged: int = 0
    total_consumed: int = 0
    plan_name: str = "免费版"
    credit_balance: int = 0
    total_recharged: int = 0
    total_consumed: int = 0


class AdminUserListOut(BaseModel):
    items: list[AdminUserOut]
    total: int
    limit: Annotated[int, Field(ge=1, le=100)]
    offset: Annotated[int, Field(ge=0)]


class AdminNameHistoryListOut(BaseModel):
    items: list[NameHistoryOut]
    total: int
    limit: Annotated[int, Field(ge=1, le=100)]
    offset: Annotated[int, Field(ge=0)]


class CategoryGenerationStatOut(BaseModel):
    category: str
    count: int
    percent: float


class DailyMetricOut(BaseModel):
    date: str
    count: int = 0


class DailyCreditMetricOut(BaseModel):
    date: str
    credits: int = 0


class DailyRagTaskMetricOut(BaseModel):
    date: str
    total: int = 0
    failed: int = 0
    failure_rate: float = 0


class HotKeywordStatOut(BaseModel):
    name: str
    count: int
    percent: float


class PaidConversionOut(BaseModel):
    paid_users: int = 0
    paid_orders: int = 0
    paid_amount_cents: int = 0
    conversion_rate: float = 0


class AdminGenerationStatsOut(BaseModel):
    total_users: int
    total_generations: int
    today_generations: int
    category_stats: list[CategoryGenerationStatOut]
    today_new_users: int = 0
    paid_conversion: PaidConversionOut = Field(default_factory=PaidConversionOut)
    today_credit_consumed: int = 0
    rag_failure_rate: float = 0
    daily_generations: list[DailyMetricOut] = Field(default_factory=list)
    daily_new_users: list[DailyMetricOut] = Field(default_factory=list)
    daily_paid_users: list[DailyMetricOut] = Field(default_factory=list)
    daily_credit_consumed: list[DailyCreditMetricOut] = Field(default_factory=list)
    failed_task_trend: list[DailyMetricOut] = Field(default_factory=list)
    daily_rag_tasks: list[DailyRagTaskMetricOut] = Field(default_factory=list)
    hot_industries: list[HotKeywordStatOut] = Field(default_factory=list)
    hot_styles: list[HotKeywordStatOut] = Field(default_factory=list)


class KnowledgeTaskOut(BaseModel):
    id: int
    user_id: int
    project_id: int | None = None
    username: str = ""
    email: str = ""
    filename: str
    status: str
    error_message: str | None = None
    is_active: bool = True
    chunk_count: int = 0
    parse_log: str | None = None
    created_time: datetime
    updated_time: datetime


class AdminKnowledgeTaskListOut(BaseModel):
    items: list[KnowledgeTaskOut]
    total: int
    limit: Annotated[int, Field(ge=1, le=100)]
    offset: Annotated[int, Field(ge=0)]


class AdminKnowledgeTaskBatchRetryIn(BaseModel):
    task_ids: list[int] | None = None
    status: str | None = "failed"
    limit: Annotated[int, Field(ge=1, le=100)] = 100


class AdminKnowledgeTaskRetryItemOut(BaseModel):
    id: int
    status: str
    error_message: str | None = None
    retried: bool


class AdminKnowledgeTaskBatchRetryOut(BaseModel):
    items: list[AdminKnowledgeTaskRetryItemOut]
    retried: int
    failed: int


class KnowledgeTaskStatsOut(BaseModel):
    total: int
    today: int
    queued: int
    processing: int
    done: int
    failed: int
    recent_tasks: list[KnowledgeTaskOut]


class AdminDataTableOut(BaseModel):
    name: str
    label: str
    primary_key: str = "id"
    columns: list[str]
    editable_columns: list[str]
    create_columns: list[str]


class AdminDataTableListOut(BaseModel):
    items: list[AdminDataTableOut]


class AdminDataRecordListOut(BaseModel):
    table: str
    items: list[dict]
    total: int
    limit: Annotated[int, Field(ge=1, le=100)]
    offset: Annotated[int, Field(ge=0)]


class AdminDataRecordOut(BaseModel):
    table: str
    item: dict


class AdminDataCreateIn(BaseModel):
    data: dict


class AdminDataUpdateIn(BaseModel):
    data: dict


class AdminDataDeleteOut(BaseModel):
    message: str


class AdminResetPasswordIn(BaseModel):
    new_password: RawPasswordStr
    confirm_password: RawPasswordStr

    @model_validator(mode="after")
    def password_is_valid(self):
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords don't match")
        return self
