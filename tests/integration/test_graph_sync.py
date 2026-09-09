import json
import os

import pytest

from ecommerce_graph_agent.datasync.neo4j_writer import write_nodes
from ecommerce_graph_agent.datasync.table_sync import sync_plan
from ecommerce_graph_agent.datasync.validate import graph_plan

pytestmark = pytest.mark.integration


def test_real_idempotence_rename_and_rollback(real_graph, repo_root):
    if os.environ.get("ECOMMERCE_GRAPH_WRITABLE") != "1":
        pytest.skip("Explicit build phase required for transactional writer test")
    plan = graph_plan(json.loads((repo_root / "data/sample/business.json").read_text(encoding="utf-8")))
    one = sync_plan(real_graph, plan, "independent-sample")
    two = sync_plan(real_graph, plan, "independent-sample")
    assert one["after"] == two["after"]
    assert two["counters"]["nodes_created"] == two["counters"]["relationships_created"] == 0
    with real_graph.session(database="neo4j") as s:
        tx = s.begin_transaction()
        try:
            write_nodes(tx, "SPU", [{"id": 1, "name": "事务内改名验证"}], "independent-sample")
            assert (
                tx.run("MATCH(n:SPU {id:1}) RETURN count(n) AS count,n.name AS name").single()["name"]
                == "事务内改名验证"
            )
        finally:
            tx.rollback()
        assert s.run("MATCH(n:SPU {id:1}) RETURN n.name AS name").single()["name"] == "轻旅背包"
