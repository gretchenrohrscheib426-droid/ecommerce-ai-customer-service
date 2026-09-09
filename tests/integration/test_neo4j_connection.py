import pytest

pytestmark = pytest.mark.integration


def test_real_connection_and_namespace(real_graph):
    with real_graph.session(database="neo4j") as s:
        assert s.run("RETURN 1 AS n").single()["n"] == 1
        assert s.run("MATCH(n) RETURN count(n) AS n").single()["n"] == 25
