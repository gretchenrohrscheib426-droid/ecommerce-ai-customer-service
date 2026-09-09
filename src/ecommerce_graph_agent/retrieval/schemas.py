"""Canonical names come from database properties; rank scores are not probabilities."""

from typing import Literal

from pydantic import BaseModel, Field


class CandidateEntity(BaseModel):
    label: str
    canonical_id: str
    canonical_name: str
    score: float
    source: Literal["vector", "fulltext", "hybrid"]
    raw_metadata: dict = Field(default_factory=dict)
