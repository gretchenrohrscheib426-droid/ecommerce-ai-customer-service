"""Request-local visible workflow state; never hidden model reasoning."""

from dataclasses import dataclass, field


@dataclass
class AgentState:
    question: str
    trace_id: str
    intent: str | None = None
    entities: list[dict] = field(default_factory=list)
    aligned_entities: list[dict] = field(default_factory=list)
    query_plan: dict | None = None
    query_result: list[dict] = field(default_factory=list)
    answer: str = ""
    errors: list[str] = field(default_factory=list)
