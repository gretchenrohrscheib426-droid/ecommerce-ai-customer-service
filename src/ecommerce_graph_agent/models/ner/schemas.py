"""Original codepoint span contract; validation against the source is separate."""

from pydantic import BaseModel, ConfigDict, Field


class EntitySpan(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    text: str = Field(min_length=1)


class Prediction(BaseModel):
    original_text: str
    token_offsets: list[tuple[int, int]]
    entities: list[EntitySpan]
    model_sha256: str
