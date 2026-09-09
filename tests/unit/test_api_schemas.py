import pytest
from pydantic import ValidationError

from ecommerce_graph_agent.web.schemas import Answer, Question


@pytest.mark.parametrize(
    "payload",
    [
        {"message": ""},
        {"message": " " * 3},
        {"message": "x" * 501},
        {"message": "ok", "query": "MATCH(n) DELETE n"},
        {"message": 7},
    ],
)
def test_question_boundary(payload):
    with pytest.raises(ValidationError):
        Question(**payload)


def test_answer_does_not_claim_grounding_by_default():
    assert not Answer(message="unavailable", status="error", trace_id="test").grounded
