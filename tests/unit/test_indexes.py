import copy

import pytest

from ecommerce_graph_agent.retrieval.indexes import check_index


def test_actual_neo4j_uppercase_cosine_accepted_but_schema_change_rejected():
    row = {
        "type": "VECTOR",
        "entityType": "NODE",
        "labelsOrTypes": ["SPU"],
        "properties": ["embedding"],
        "options": {
            "indexProvider": "vector-2.0",
            "indexConfig": {"vector.dimensions": 512, "vector.similarity_function": "COSINE"},
        },
    }
    check_index(row, "SPU", "VECTOR")
    wrong = copy.deepcopy(row)
    wrong["options"]["indexConfig"]["vector.dimensions"] = 384
    with pytest.raises(ValueError):
        check_index(wrong, "SPU", "VECTOR")
    wrong = copy.deepcopy(row)
    wrong["labelsOrTypes"] = ["SKU"]
    with pytest.raises(ValueError):
        check_index(wrong, "SPU", "VECTOR")
