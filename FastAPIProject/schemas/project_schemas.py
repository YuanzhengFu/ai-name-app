from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field

from schemas.history_schemas import NameCompareRankOut, NameHistoryOut
from schemas.name_schemas import CategoryLiteral


class NamingProjectCreateIn(BaseModel):
    title: Annotated[str, Field(..., min_length=1, max_length=120)]
    category: CategoryLiteral
    description: str = ""


class NamingProjectUpdateIn(BaseModel):
    title: Annotated[str | None, Field(default=None, min_length=1, max_length=120)] = None
    description: str | None = None
    status: str | None = Field(default=None, pattern="^(active|archived)$")


class NamingProjectOut(BaseModel):
    id: int
    user_id: int
    title: str
    category: CategoryLiteral
    description: str = ""
    status: str = "active"
    history_count: int = 0
    favorite_count: int = 0
    knowledge_file_count: int = 0
    created_time: datetime
    updated_time: datetime

    model_config = {"from_attributes": True}


class NamingProjectListOut(BaseModel):
    items: list[NamingProjectOut]
    total: int
    limit: Annotated[int, Field(ge=1, le=100)]
    offset: Annotated[int, Field(ge=0)]


class ProjectKnowledgeTaskOut(BaseModel):
    id: int
    filename: str
    status: str
    status_label: str
    error_message: str | None = None
    is_active: bool = True
    created_time: datetime
    updated_time: datetime


class NamingProjectDetailOut(NamingProjectOut):
    recommendations: list[NameCompareRankOut] = Field(default_factory=list)
    histories: list[NameHistoryOut] = Field(default_factory=list)
    knowledge_files: list[ProjectKnowledgeTaskOut] = Field(default_factory=list)
