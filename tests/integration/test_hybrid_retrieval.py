import pytest

from ecommerce_graph_agent.graph.indexes import Embedder
from ecommerce_graph_agent.retrieval.hybrid import HybridRetriever

pytestmark = pytest.mark.integration


def test_real_vector_fulltext_metadata(real_graph, repo_root):
    retrieval = HybridRetriever(real_graph, Embedder(repo_root))
    candidates = retrieval.candidates("青岚示例", "BaseTrademark")
    assert candidates[0].canonical_id == "BaseTrademark:1"
    assert candidates[0].canonical_name == "青岚示例" and candidates[0].source == "hybrid"
