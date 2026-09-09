"""Unit tests are offline. Real database access requires explicit opt-in."""

import os
from pathlib import Path

import pytest


@pytest.fixture
def repo_root():
    return Path(__file__).resolve().parents[1]


@pytest.fixture
def real_graph(repo_root):
    if os.environ.get("ECOMMERCE_PUBLIC_INTEGRATION") != "1":
        pytest.skip("Real public database integration was not enabled")
    from ecommerce_graph_agent.datasync.neo4j_writer import driver

    with driver(repo_root) as instance:
        with instance.session(database="neo4j") as session:
            scopes = [r["scope"] for r in session.run("MATCH(n) RETURN DISTINCT n.dataset AS scope")]
            assert scopes == ["independent-sample"], "Only the owned synthetic graph is permitted"
        yield instance


@pytest.fixture
def real_mysql(repo_root):
    if os.environ.get("ECOMMERCE_PUBLIC_INTEGRATION") != "1":
        pytest.skip("Real public MySQL integration was not enabled")
    from ecommerce_graph_agent.config import Settings
    from ecommerce_graph_agent.datasync.mysql_reader import connect

    assert Settings.load(repo_root).mysql_database in {"ecommerce_demo", "ecommerce_public_demo"}
    with connect(repo_root) as connection:
        yield connection
