"""API contract with an explicit fake workflow, distinct from real browser evidence."""

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from ecommerce_graph_agent.web.app import create_app
from ecommerce_graph_agent.web.schemas import Answer

pytestmark = pytest.mark.e2e


def test_http_contract_safe_rendering_and_status(tmp_path, monkeypatch):
    monkeypatch.setenv("ECOMMERCE_ROOT", str(tmp_path))
    service = SimpleNamespace(
        online=False,
        dataset="explicit-api-test-fake",
        chat=lambda q: Answer(message="<script>test</script>", status="ok", trace_id="api-test-fake"),
    )
    with TestClient(create_app(service)) as client:
        assert client.get("/").status_code == 200
        assert client.get("/health").json()["app"] == "ok"
        status = client.get("/api/status").json()
        assert status["mysql"] == "not_configured" and status["neo4j"] == "unavailable"
        assert status["llm"] == "not_enabled"
        assert client.post("/api/chat", json={"message": "合法问题"}).status_code == 200
        assert client.post("/api/chat", json={"message": ""}).status_code == 422
        assert (
            client.post(
                "/api/chat", json={"message": "x"}, headers={"Origin": "https://evil.invalid"}
            ).status_code
            == 403
        )
        assert client.post("/api/raw-cypher", json={"query": "DELETE"}).status_code == 404
