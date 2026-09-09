"""Optional isolated CI service only; never targets the user's existing database."""

import json
import os
import time
from pathlib import Path

import pytest
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable

from ecommerce_graph_agent.datasync.sync import sync_plan
from ecommerce_graph_agent.datasync.validate import graph_plan

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.environ.get("ECOMMERCE_CI_DB") != "1", reason="Optional isolated CI Neo4j service not enabled"
    ),
]


def test_independent_tables_idempotence_in_isolated_ci_service():
    root = Path(__file__).resolve().parents[2]
    plan = graph_plan(json.loads((root / "data/sample/business.json").read_text(encoding="utf-8")))
    with GraphDatabase.driver(
        "bolt://127.0.0.1:7687", auth=("neo4j", "ci-ephemeral-only-password"), connection_timeout=2
    ) as d:
        deadline = time.monotonic() + 60
        while True:
            try:
                d.verify_connectivity()
                break
            except ServiceUnavailable:
                if time.monotonic() >= deadline:
                    raise
                time.sleep(1)
        with d.session(database="neo4j") as s:
            assert s.run("MATCH(n) RETURN count(n) AS n").single()["n"] == 0, "Refuse nonempty instance"
        first = sync_plan(d, plan, "independent-ci")
        second = sync_plan(d, plan, "independent-ci")
        assert first["after"]["node_total"] == 21
        assert first["after"]["relationship_total"] == 27
        assert second["counters"]["nodes_created"] == 0 and second["counters"]["relationships_created"] == 0
