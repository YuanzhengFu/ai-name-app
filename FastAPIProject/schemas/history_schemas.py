from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, field_validator

from schemas.name_schemas import CategoryLiteral


class HistoryFavoriteIn(BaseModel):
    is_favorite: bool


class NameCompareIn(BaseModel):
    history_ids: list[int] = Field(..., min_length=2, max_length=5)

    @field_validator("history_ids")
    @classmethod
    def validate_unique_ids(cls, value: list[int]) -> list[int]:
        if len(set(value)) != len(value):
            raise ValueError("不能重复选择同一个名字")
        return value


class NameHistoryOut(BaseModel):
    id: int
    user_id: int
    project_id: int | None = None
    thread_id: str
    category: CategoryLiteral
    name: str
    reference: str
    moral: str
    domain: str = ""
    domain_status: str = ""
    domain_checks: list[dict[str, str]] = Field(default_factory=list)
    brand_warning: str = ""
    pinyin: str = ""
    english_name: str = ""
    abbreviation: str = ""
    score_total: int = Field(default=0, ge=0, le=100)
    rhythm_score: int = Field(default=0, ge=0, le=100)
    meaning_score: int = Field(default=0, ge=0, le=100)
    spread_score: int = Field(default=0, ge=0, le=100)
    domain_score: int = Field(default=0, ge=0, le=100)
    score_explanation: str = ""
    surname: str = ""
    gender: str = ""
    length: str = ""
    other: str | None = None
    exclude: list[str] = Field(default_factory=list)
    is_favorite: bool = False
    created_time: datetime
    updated_time: datetime

    model_config = {"from_attributes": True}


class NameHistoryListOut(BaseModel):
    items: list[NameHistoryOut]
    total: int
    limit: Annotated[int, Field(ge=1, le=100)]
    offset: Annotated[int, Field(ge=0)]


class NameCompareItemOut(BaseModel):
    history_id: int
    name: str
    category: CategoryLiteral
    moral: str
    rhythm_score: int = Field(default=0, ge=0, le=100)
    meaning_score: int = Field(default=0, ge=0, le=100)
    spread_score: int = Field(default=0, ge=0, le=100)
    domain: str = ""
    domain_status: str = ""
    domain_checks: list[dict[str, str]] = Field(default_factory=list)
    brand_warning: str = ""
    pinyin: str = ""
    english_name: str = ""
    abbreviation: str = ""
    domain_score: int = Field(default=0, ge=0, le=100)
    score_total: int = Field(default=0, ge=0, le=100)
    compare_score: int = Field(default=0, ge=0, le=100)
    suitable_scenes: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    tradeoffs: list[str] = Field(default_factory=list)


class NameCompareRankOut(BaseModel):
    rank: int
    history_id: int
    name: str
    compare_score: int = Field(default=0, ge=0, le=100)
    reason: str


class NameCompareOut(BaseModel):
    items: list[NameCompareItemOut]
    ranking: list[NameCompareRankOut]
    recommendation: str
