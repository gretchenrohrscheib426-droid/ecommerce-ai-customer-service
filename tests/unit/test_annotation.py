"""Run with the isolated ml-backend interpreter; provider is explicitly mocked."""

import importlib.util
from pathlib import Path

import pytest

pytest.importorskip("label_studio_ml")
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("tag_backend", ROOT / "annotation/ml_backend/model.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def backend(monkeypatch, result):
    obj = module.TagBackend(
        project_id="mock-unit", label_config=(ROOT / "configs/label_studio.xml").read_text()
    )
    monkeypatch.setattr(obj, "_extract", lambda tasks: result)
    return obj


def test_prediction_protocol_repeated_text_and_surrogates(monkeypatch):
    text = "😀防水 防水"
    obj = backend(
        monkeypatch,
        [
            {
                "id": 1,
                "spans": [
                    {"start": 1, "end": 3, "text": "防水", "labels": ["TAG"]},
                    {"start": 4, "end": 6, "text": "防水", "labels": ["TAG"]},
                ],
            }
        ],
    )
    response = obj.predict([{"id": 1, "data": {"text": text}}]).model_dump()
    results = response["predictions"][0]["result"]
    assert [r["value"]["start"] for r in results] == [2, 5]
    assert results[0]["id"] != results[1]["id"]


def test_provider_count_mismatch_is_not_silently_zipped(monkeypatch):
    obj = backend(monkeypatch, [])
    with pytest.raises(ValueError, match="count/identity"):
        obj.predict([{"id": 1, "data": {"text": "防水"}}])


def test_empty_prediction_valid_and_batch_bound(monkeypatch):
    obj = backend(monkeypatch, [{"id": 1, "spans": []}])
    assert obj.predict([{"id": 1, "data": {"text": "商品"}}]).predictions[0].result == []
    with pytest.raises(ValueError, match="1–8"):
        obj.predict([])
