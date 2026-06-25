from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, Field, field_validator

from schemas.name_schemas import CategoryLiteral


ALLOWED_PREFERENCE_FIELDS = {
    "category",
    "surname",
    "gender",
    "length",
    "other",
    "exclude",
    "birth_datetime",
    "wuxing",
    "desired_meaning",
    "industry",
    "style",
    "region",
    "target_user",
    "pet_type",
    "pet_style",
}


class NamingPreferenceTemplateBase(BaseModel):
    title: Annotated[str, Field(..., min_length=1, max_length=120)]
    category: CategoryLiteral
    preferences: dict[str, Any] = Field(default_factory=dict)
    is_default: bool = False

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Template title cannot be empty")
        return value

    @field_validator("preferences")
    @classmethod
    def validate_preferences(cls, value: dict[str, Any]) -> dict[str, Any]:
        illegal = [key for key in value if key not in ALLOWED_PREFERENCE_FIELDS]
        if illegal:
            raise ValueError(f"Unsupported preference fields: {', '.join(sorted(illegal))}")
        return value


class NamingPreferenceTemplateCreateIn(NamingPreferenceTemplateBase):
    pass


class NamingPreferenceTemplateUpdateIn(BaseModel):
    title: Annotated[str | None, Field(default=None, min_length=1, max_length=120)] = None
    category: CategoryLiteral | None = None
    preferences: dict[str, Any] | None = None
    is_default: bool | None = None

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Template title cannot be empty")
        return value

    @field_validator("preferences")
    @classmethod
    def validate_preferences(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        if value is None:
            return value
        illegal = [key for key in value if key not in ALLOWED_PREFERENCE_FIELDS]
        if illegal:
            raise ValueError(f"Unsupported preference fields: {', '.join(sorted(illegal))}")
        return value


class NamingPreferenceTemplateOut(BaseModel):
    id: int
    user_id: int
    title: str
    category: CategoryLiteral
    preferences: dict[str, Any]
    is_default: bool
    created_time: datetime
    updated_time: datetime

    model_config = {"from_attributes": True}


class NamingPreferenceTemplateListOut(BaseModel):
    items: list[NamingPreferenceTemplateOut]
    total: int
