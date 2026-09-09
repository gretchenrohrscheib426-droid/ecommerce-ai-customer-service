import pytest

from ecommerce_graph_agent.graph.queries import TEMPLATES
from ecommerce_graph_agent.security.cypher_guard import validate_query


@pytest.mark.parametrize(
    "suffix",
    [
        "CREATE (n)",
        "MERGE (n)",
        "SET n.x=1",
        "DELETE n",
        "DETACH DELETE n",
        "DROP INDEX x",
        "REMOVE n.x",
        'LOAD CSV FROM "file:///x" AS x RETURN x',
        "FOREACH(x IN []|CREATE())",
        "CALL dbms.components()",
        "RETURN 1; RETURN 2",
        "// comment",
        "UNION MATCH(n) RETURN n",
    ],
)
def test_every_nonapproved_clause_is_rejected(suffix):
    with pytest.raises(ValueError):
        validate_query(TEMPLATES["price:SPU"] + " " + suffix, {"entity_id": 1, "limit": 20})


def test_no_literal_unbounded_query_or_injected_value():
    for query, params in [
        ("MATCH(n) RETURN n", {}),
        (TEMPLATES["price:SPU"], {"entity_id": "1 DELETE n", "limit": 20}),
        (TEMPLATES["price:SPU"], {"entity_id": 1, "limit": 21}),
    ]:
        with pytest.raises(ValueError):
            validate_query(query, params)
