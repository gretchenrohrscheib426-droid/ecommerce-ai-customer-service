import importlib
import json
import sys
from pathlib import Path

import pytest

pytest.importorskip("label_studio_ml")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "annotation/ml_backend"))
model = importlib.import_module("model")
InferenceUnavailable = model.InferenceUnavailable
TagBackend = model.TagBackend

CONFIG = (ROOT / "configs/label_studio.xml").read_text(encoding="utf-8")


@pytest.mark.parametrize("scenario", ["429", "timeout", "malformed"])
def test_online_failure_never_becomes_success(monkeypatch, tmp_path, scenario):
    import httpx

    task = {"id": 1, "data": {"text": "独立防水示例"}}
    (tmp_path / "artifacts/local/ml-backend").mkdir(parents=True)
    (tmp_path / "data/sample").mkdir(parents=True)
    (tmp_path / "artifacts/local/online_authorization.json").write_text(
        json.dumps(
            {
                "annotation_enabled": True,
                "allowed_dataset": "independent-sample",
                "model": "explicit-mock",
                "max_annotation_calls": 1,
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "data/sample/annotation_tasks.json").write_text(json.dumps([task]), encoding="utf-8")
    monkeypatch.setattr(model, "ROOT", tmp_path)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "unit-test-placeholder-not-a-secret")

    class MockClient:
        def __init__(self, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def post(self, *args, **kwargs):
            if scenario == "timeout":
                raise httpx.ReadTimeout("explicit timeout mock")
            return httpx.Response(
                429 if scenario == "429" else 200, json={"choices": [{"message": {"content": "not JSON"}}]}
            )

    monkeypatch.setattr(httpx, "Client", MockClient)
    backend = TagBackend(project_id="http-unit", label_config=CONFIG)
    with pytest.raises((InferenceUnavailable, ValueError)):
        backend.predict([task])
    with pytest.raises(InferenceUnavailable, match="budget exhausted"):
        backend.predict([task])


def test_real_sdk_http_wrapper_hides_tracebacks():
    import _wsgi

    c = _wsgi.app.test_client()
    response = c.post(
        "/predict",
        json={"tasks": [{"id": 1, "data": {"text": "独立示例"}}], "project": "unit", "label_config": CONFIG},
    )
    assert response.status_code == 503
    assert "traceback" not in response.get_data(as_text=True)
    response = c.post("/predict", json={"tasks": [], "project": "unit", "label_config": CONFIG})
    assert response.status_code == 400
