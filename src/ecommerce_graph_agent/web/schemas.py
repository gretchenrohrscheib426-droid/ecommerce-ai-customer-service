"""Public API contracts. Evidence contains actual database fields."""

from pydantic import BaseModel

from ..qa.schema import Answer as Answer
from ..qa.schema import Question as Question


class EntitySource(BaseModel):
    canonical_id: str
    canonical_name: str
    label: str


class StatusResponse(BaseModel):
    app: str
    mysql: str
    neo4j: str
    llm: str
    ner_model: str
    embedding: str
    demo_mode: bool
    dataset: str
    generation: str
    raw_cypher: bool
