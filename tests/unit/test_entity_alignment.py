from unittest.mock import MagicMock

from ecommerce_graph_agent.retrieval.entity_alignment import align_entity
from ecommerce_graph_agent.retrieval.hybrid import HybridRetriever
from ecommerce_graph_agent.retrieval.search import Retriever


def test_threshold_rejects_weak_match_and_never_assumes_top1():
    r = Retriever(None, None, min_cosine=0.85)
    r.catalog = lambda: []
    r.hybrid = lambda *args: [
        {
            "metadata": {"canonical_id": "SPU:1", "canonical_name": "示例", "label": "SPU"},
            "score": 0.016,
            "channels": {"vector": 0.84},
        }
    ]
    assert align_entity(r, "错字")["status"] == "not_found"
    r.min_cosine = 0.8
    assert align_entity(r, "错字")["status"] == "ambiguous"


def test_duplicate_names_require_confirmation():
    r = Retriever(None, None)
    r.catalog = lambda: [
        {"id": i, "canonical_id": f"SPU:{i}", "name": "同名", "label": "SPU"} for i in [1, 2]
    ]
    result = align_entity(r, "同名", "SPU")
    assert result["status"] == "ambiguous" and len(result["candidates"]) == 2


def test_candidate_uses_metadata_name_not_formatted_text():
    r = HybridRetriever(None, None)
    r.hybrid = MagicMock(
        return_value=[
            {
                "text": "name: wrong serialized content",
                "metadata": {"canonical_id": "SPU:1", "canonical_name": "数据库原名", "label": "SPU"},
                "score": 0.032,
                "channels": {"vector": 0.9, "fulltext": 1.2},
            }
        ]
    )
    candidate = r.candidates("输入")[0]
    assert candidate.canonical_name == "数据库原名" and candidate.source == "hybrid"
