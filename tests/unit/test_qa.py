import pytest
from pydantic import ValidationError

from ecommerce_graph_agent.agent.orchestrator import local_plan, render_rows
from ecommerce_graph_agent.qa.cypher import TEMPLATES, compile_plan, validate_query
from ecommerce_graph_agent.qa.schema import Plan, Question


@pytest.mark.parametrize(
    "query",
    [
        "MATCH(n) DETACH DELETE n",
        "CREATE (n)",
        "CALL dbms.listConfig()",
        "SHOW USERS",
        "USE system RETURN 1",
        'LOAD CSV FROM "file:///private" AS line RETURN line',
        "CALL apoc.cypher.run($q,{})",
        "MATCH (n)-[*]-(m) RETURN n",
        "RETURN 1; RETURN 2",
        "EXPLAIN MATCH(n) DELETE n",
        "MATCH (n) RETURN n LIMIT 20",
        "MATCH(n) CALL { WITH n RETURN n } RETURN n",
        "MATCH(n) SET n.name=$name RETURN n",
        "DROP INDEX spu_embedding_index",
        TEMPLATES["price:SPU"] + " // harmless?",
    ],
)
def test_query_acceptance_is_exact_subset(query):
    with pytest.raises(ValueError):
        validate_query(query, {"entity_id": 1, "limit": 20})


@pytest.mark.parametrize(
    "params",
    [
        {"entity_id": True, "limit": 2},
        {"entity_id": "1", "limit": 2},
        {"entity_id": 1, "limit": 21},
        {"entity_id": 1, "limit": 0},
        {"entity_id": 1, "limit": 2, "db": "system"},
    ],
)
def test_query_parameter_abuse(params):
    with pytest.raises(ValueError):
        validate_query(TEMPLATES["price:SPU"], params)


def test_wrong_type_and_extra_request_fields_rejected():
    with pytest.raises(ValidationError):
        Question(message="有效", query="DELETE")
    with pytest.raises(ValidationError):
        Plan(intent="price", entity="苹果", label="User")
    with pytest.raises(ValidationError):
        Question(message=" ")
    with pytest.raises(ValidationError):
        Question(message=17)


def test_local_planner_preserves_named_entity_and_marks_unsupported():
    catalog = [{"name": "苹果", "label": "BaseTrademark"}, {"name": "苹果手机示例", "label": "SPU"}]
    assert local_plan("苹果手机示例多少钱", catalog).entity == "苹果手机示例"
    assert local_plan("苹果品牌有哪些商品", catalog).label == "BaseTrademark"
    assert local_plan("实时库存还有多少", catalog).intent == "unsupported"


def test_fixed_template_parameterization():
    query, params = compile_plan(Plan(intent="price", entity="任意原始名"), {"label": "SPU", "id": 7})
    assert params == {"entity_id": 7, "limit": 20} and "任意原始名" not in query


def test_no_unprovided_price_or_claim():
    text = render_rows([{"source_id": "SPU:1", "product": "独立示例"}], "products")
    assert "独立示例" in text and "199" not in text and "SPU:1" in text
