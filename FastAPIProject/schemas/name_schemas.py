from typing import Annotated, List, Literal

from pydantic import BaseModel, Field, model_validator


class NameSchema(BaseModel):
    name: Annotated[str, Field(..., description="The name")]
    reference: Annotated[str, Field(..., description="The name source")]
    moral: Annotated[str, Field(..., description="寓意")]
    category: str = Field(default="", description="起名分类")
    domain: str = Field("", description="为品牌设计的 .com 域名")
    domain_status: str = Field(default="", description="域名的注册状态")
    domain_checks: list[dict[str, str]] = Field(default_factory=list, description="Multi-suffix domain checks")
    brand_warning: str = Field(default="", description="Trademark or brand conflict warning")
    pinyin: str = Field(default="", description="Generated pinyin or romanized name")
    english_name: str = Field(default="", description="Generated English brand name")
    abbreviation: str = Field(default="", description="Generated abbreviation")
    score_total: int = Field(default=0, ge=0, le=100, description="名字综合评分")
    rhythm_score: int = Field(default=0, ge=0, le=100, description="音律评分")
    meaning_score: int = Field(default=0, ge=0, le=100, description="寓意评分")
    spread_score: int = Field(default=0, ge=0, le=100, description="传播性评分")
    domain_score: int = Field(default=0, ge=0, le=100, description="域名评分")
    score_explanation: str = Field(default="", description="评分解释")
    history_id: int | None = None
    project_id: int | None = None
    is_favorite: bool = False


class NameResultSchema(BaseModel):
    names: List[NameSchema]


CategoryLiteral = Literal["人名", "企业名", "宠物名"]


class NameIn(BaseModel):
    category: Annotated[CategoryLiteral, Field(..., description="起名分类")]
    surname: Annotated[str, Field("", description="The surname of the person")]
    gender: Annotated[Literal["不限", "男", "女"], Field("", description="The gender of the person")]
    length: Annotated[str, Field("", description="The length of the name")]
    other: Annotated[str | None, Field("", description="Other requirements")]
    exclude: Annotated[list[str], Field(default_factory=list, description="Excluded characters")]
    birth_datetime: Annotated[str | None, Field("", description="Birth date/time for human names")]
    wuxing: Annotated[str | None, Field("", description="Preferred or missing five-element attribute")]
    desired_meaning: Annotated[str | None, Field("", description="Expected meaning for human names")]
    industry: Annotated[str | None, Field("", description="Company industry")]
    style: Annotated[str | None, Field("", description="Company naming style")]
    region: Annotated[str | None, Field("", description="Company target region")]
    project_id: int | None = Field(default=None, description="Existing naming project id")
    project_title: str | None = Field(default=None, max_length=120, description="Title for a new naming project")
    project_description: str | None = Field(default="", description="Description for a new naming project")

    @model_validator(mode="after")
    def validate(self):
        if self.category == "人名" and not self.surname:
            raise ValueError("给人起名字时，必须给定姓氏")
        return self


class NameOutSchema(BaseModel):
    names: List[NameSchema]
    quota_remaining: int | None = None


class NameSchemaWithThreadOut(BaseModel):
    thread_id: str
    project_id: int | None = None
    names: List[NameSchema]
    quota_remaining: int | None = None


class FeedbackSchema(BaseModel):
    thread_id: str = Field(...)
    project_id: int | None = None
    category: CategoryLiteral = Field(..., description="路由依据")
    feedback: str = Field(..., description="用户的修改意见，例如：换成带水字旁的字")
