from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Label = Literal["SPU", "BaseTrademark", "Category3", "Category2", "Category1"]


class Plan(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    intent: Literal[
        "product_detail", "price", "products", "tags", "attributes", "category_path", "unsupported"
    ]
    entity: str = Field(min_length=1, max_length=120)
    label: Label | None = None

    @field_validator("entity")
    @classmethod
    def strip_entity(cls, value):
        if not value.strip():
            raise ValueError("Empty entity")
        return value.strip()


class Question(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    message: str = Field(min_length=1, max_length=500)
    clarification_token: str | None = Field(default=None, max_length=80)
    choice: str | None = Field(default=None, max_length=90)

    @field_validator("message")
    @classmethod
    def valid_message(cls, value):
        if not value.strip():
            raise ValueError("Empty message")
        return value.strip()


class Answer(BaseModel):
    message: str
    status: str
    trace_id: str
    grounded: bool = False
    evidence: list[dict] = Field(default_factory=list)
    candidates: list[dict] = Field(default_factory=list)
    clarification_token: str | None = None
    generation: str = "local-result-formatting"
    steps: list[str] = Field(default_factory=list)
