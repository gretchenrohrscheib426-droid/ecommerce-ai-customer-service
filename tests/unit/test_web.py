from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from neo4j.exceptions import ServiceUnavailable

from ecommerce_graph_agent.qa.schema import Answer
from ecommerce_graph_agent.web.app import create_app, wait_for_database


def test_delayed_database_start_and_fail_closed():
    driver = MagicMock()
    driver.verify_connectivity.side_effect = [
        ServiceUnavailable("starting"),
        ServiceUnavailable("starting"),
        None,
    ]
    pauses = []
    wait_for_database(driver, pause=pauses.append)
    assert driver.verify_connectivity.call_count == 3 and pauses == [0.5, 0.5]
    driver.verify_connectivity.side_effect = ServiceUnavailable("still down")
    with pytest.raises(ServiceUnavailable):
        wait_for_database(driver, timeout=0, pause=pauses.append)
    driver.verify_connectivity.side_effect = ValueError("misconfigured")
    with pytest.raises(ValueError):
        wait_for_database(driver, pause=pauses.append)


class MockService:
    def chat(self, question):
        return Answer(message="explicit mock protocol only", status="ok", trace_id="unit-mock")


def test_api_contract_limits_and_xss_surface():
    with TestClient(create_app(MockService())) as c:
        assert c.get("/health/live").status_code == 200
        assert c.get("/health/ready").json()["raw_cypher"] is False
        for body in [{}, {"message": ""}, {"message": "x" * 501}, {"message": "x", "query": "DELETE"}]:
            assert c.post("/api/chat", json=body).status_code == 422
        assert (
            c.post("/api/chat", json={"message": "正常"}).json()["message"] == "explicit mock protocol only"
        )
        assert (
            c.post(
                "/api/chat", json={"message": "正常"}, headers={"Origin": "https://untrusted.invalid"}
            ).status_code
            == 403
        )
        assert c.post("/api/chat", content="x" * 9000).status_code == 413
        assert c.post("/api/cypher", json={"query": "DELETE"}).status_code == 404
        page = c.get("/")
        assert page.status_code == 200 and "frame-src 'none'" in page.headers["Content-Security-Policy"]
        js = c.get("/static/app.js").text
        assert "innerHTML" not in js and "textContent" in js
