import json

import pytest

from ecommerce_graph_agent.config import Settings


def test_environment_overrides_dotenv_and_runtime_without_exposing_secrets(tmp_path, monkeypatch):
    path = tmp_path / "artifacts/local"
    path.mkdir(parents=True)
    (path / "runtime.json").write_text(json.dumps({"api_port": 8123}))
    (tmp_path / ".env").write_text("API_PORT=8124\nNEO4J_PASSWORD=unit-test-secret\n")
    monkeypatch.setenv("API_PORT", "8125")
    settings = Settings.load(tmp_path)
    assert settings.api_port == 8125 and settings.secret("neo4j") == "unit-test-secret"
    assert "unit-test-secret" not in repr(settings)
    assert "unit-test-secret" not in json.dumps(settings.diagnostics())


@pytest.mark.parametrize(
    "uri",
    [
        "bolt://example.org:7687",
        "bolt://user:" + "secret" + "@localhost:7687",
        "bolt://localhost:7687/system",
        "http://localhost:7687",
    ],
)
def test_reject_external_or_embedded_credentials(uri, monkeypatch, tmp_path):
    monkeypatch.setenv("NEO4J_URI", uri)
    with pytest.raises(ValueError):
        Settings.load(tmp_path)


def test_invalid_limits_fail(monkeypatch, tmp_path):
    monkeypatch.setenv("QUERY_MAX_ROWS", "99999")
    with pytest.raises(ValueError):
        Settings.load(tmp_path)
