import pytest

from ecommerce_graph_agent.agent.orchestrator import ChatService
from ecommerce_graph_agent.graph.indexes import Embedder
from ecommerce_graph_agent.retrieval.hybrid import HybridRetriever
from ecommerce_graph_agent.web.schemas import Question

pytestmark = pytest.mark.integration


def test_real_graph_facts_and_clarification(real_graph, repo_root):
    service = ChatService(
        repo_root, HybridRetriever(real_graph, Embedder(repo_root)), real_graph, dataset="independent-sample"
    )
    answer = service.chat(Question(message="随行水杯价格"))
    assert answer.grounded and answer.status == "ok" and answer.evidence[0]["price"] == "59"
    assert answer.generation == "local-result-formatting"
    assert service.chat(Question(message="轻旅背包价格")).status == "clarify"
