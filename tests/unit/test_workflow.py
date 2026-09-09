from concurrent.futures import ThreadPoolExecutor

import ecommerce_graph_agent.agent.orchestrator as module
from ecommerce_graph_agent.agent.orchestrator import ChatService
from ecommerce_graph_agent.qa.schema import Question


class MockRetriever:
    def catalog(self):
        return [{"name": "同名包", "label": "SPU"}]

    def align(self, text, label):
        return {
            "status": "clarify",
            "candidates": [
                {"id": 1, "label": "SPU", "canonical_id": "SPU:1", "canonical_name": "同名包"},
                {"id": 2, "label": "SPU", "canonical_id": "SPU:2", "canonical_name": "同名包"},
            ],
        }


def test_clarification_is_bound_to_question_candidate_and_consumed_once(tmp_path, monkeypatch):
    monkeypatch.setattr(module, "execute", lambda *args: [{"product": "同名包", "source_id": "SPU:1"}])
    service = ChatService(tmp_path, MockRetriever(), None)
    first = service.chat(Question(message="同名包"))
    assert first.status == "clarify"
    token = first.clarification_token
    assert (
        service.chat(Question(message="别的商品", choice="SPU:1", clarification_token=token)).status
        == "invalid_request"
    )
    assert (
        service.chat(Question(message="同名包", choice="SPU:999", clarification_token=token)).status
        == "invalid_request"
    )
    follow = Question(message="同名包", choice="SPU:1", clarification_token=token)
    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(lambda _: service.chat(follow), range(2)))
    assert sorted(r.status for r in results) == ["invalid_request", "ok"]
    assert all(len(r.steps) <= 6 for r in results)


def test_expired_clarification_and_new_topic_do_not_reuse_entity(tmp_path):
    service = ChatService(tmp_path, MockRetriever(), None)
    first = service.chat(Question(message="同名包"))
    service.pending[first.clarification_token]["expires"] = 0
    assert (
        service.chat(
            Question(message="同名包", choice="SPU:1", clarification_token=first.clarification_token)
        ).status
        == "invalid_request"
    )
    assert service.chat(Question(message="另一个商品")).status == "clarify"


def test_course_generated_query_cannot_replace_resolved_entity(tmp_path, monkeypatch):
    from unittest.mock import MagicMock

    from ecommerce_graph_agent.qa.cypher import TEMPLATES
    from ecommerce_graph_agent.qa.schema import Plan

    monkeypatch.setenv("ECOMMERCE_PROFILE", "course-reference")
    retriever = MagicMock()
    retriever.align.return_value = {"status": "aligned", "entity": {"label": "SPU", "id": 1}}
    service = ChatService(tmp_path, retriever, None, online=True)
    service.provider = MagicMock()
    service.provider.plan.return_value = Plan(intent="price", entity="示例包", label="SPU")
    service.provider.course_query.return_value = (TEMPLATES["price:SPU"], {"entity_id": 2, "limit": 20})
    execute = MagicMock()
    monkeypatch.setattr(module, "execute", execute)
    assert service.chat(Question(message="示例包价格")).status == "invalid_request"
    execute.assert_not_called()
    service.provider.course_query.return_value = (TEMPLATES["price:SPU"], {"entity_id": 1, "limit": 20})
    execute.return_value = [{"product": "示例包", "source_id": "SPU:1"}]
    service.provider.answer.return_value = execute.return_value
    result = service.chat(Question(message="示例包价格"))
    assert result.status == "ok" and len(result.steps) <= 6
