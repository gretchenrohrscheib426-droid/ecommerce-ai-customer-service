import pytest

from ecommerce_graph_agent.models.ner.data_validation import validate_dataset, validate_record
from ecommerce_graph_agent.models.ner.eval import evaluate_checkpoint


def test_quarantine_preserves_original_and_counts(tmp_path):
    row = {
        "text": "防水包",
        "label": [
            {"start": 0, "end": 2, "text": "防水", "labels": ["TAG"]},
            {"start": 1, "end": 3, "text": "水包", "labels": ["TAG"]},
        ],
    }
    report = validate_dataset([row], mode="quarantine", output=tmp_path / "quarantine.json")
    assert report["overlap_count"] == report["invalid_count"] == 1
    assert report["quarantine"][0]["record"] == row and report["valid"] == []
    with pytest.raises(ValueError):
        validate_dataset([row])


def test_duplicate_malformed_bool_and_length_are_not_accepted():
    span = {"start": 0, "end": 2, "text": "防水", "labels": ["TAG"]}
    report = validate_dataset([{"text": "防水", "label": [span, span]}], mode="quarantine")
    assert report["duplicate_count"] == 1
    for bad in [None, {}, {"start": False, "end": 2, "text": "防水", "labels": ["TAG"]}]:
        with pytest.raises(ValueError):
            validate_record({"text": "防水", "label": [bad]})
    with pytest.raises(ValueError):
        validate_record({"text": "a" * 4097, "label": []})


def test_untrained_evaluation_has_no_metrics(tmp_path):
    result = evaluate_checkpoint(tmp_path / "model", tmp_path / "test", tmp_path / "metrics.json")
    assert result["status"] == "BLOCKED_MODEL_NOT_TRAINED"
    assert all(result[k] is None for k in ["precision", "recall", "f1", "accuracy"])
    assert not (tmp_path / "metrics.json").exists()
