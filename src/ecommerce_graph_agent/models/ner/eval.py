"""Explicit test-only checkpoint evaluation; missing training produces no scores."""

import argparse
import hashlib
import json
from pathlib import Path

from .data_validation import validate_record
from .evaluate import score_spans
from .predict import Predictor


def character_labels(text, spans):
    labels = ["O"] * len(text)
    for span in spans:
        labels[span["start"]] = "B-TAG"
        for index in range(span["start"] + 1, span["end"]):
            labels[index] = "I-TAG"
    return labels


def evaluate_checkpoint(model, split_dir, output):
    model, split_dir, output = Path(model), Path(split_dir), Path(output)
    if not (model / "training_provenance.json").is_file():
        return {
            "status": "BLOCKED_MODEL_NOT_TRAINED",
            "precision": None,
            "recall": None,
            "f1": None,
            "accuracy": None,
        }
    if output.exists():
        raise FileExistsError("Final test already recorded; choose a new experiment only after review")
    manifest = json.loads((split_dir / "manifest.json").read_text(encoding="utf-8"))
    blob = (split_dir / "test.json").read_bytes()
    if hashlib.sha256(blob).hexdigest() != manifest["splits"]["test"]["sha256"]:
        raise ValueError("Frozen test split changed")
    predictor = Predictor(model)
    tp = fp = fn = correct = characters = 0
    predictions = []
    for row in json.loads(blob):
        gold = validate_record(row)
        inferred = predictor.predict_details(row["text"])
        a, b, c = score_spans(gold, inferred["entities"])
        tp += a
        fp += b
        fn += c
        expected = character_labels(row["text"], gold)
        actual = character_labels(row["text"], inferred["entities"])
        correct += sum(a == b for a, b in zip(expected, actual, strict=True))
        characters += len(expected)
        predictions.append({"id": row["id"], **inferred})
    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0
    report = {
        "status": "PASS",
        "split": "test",
        "count": len(predictions),
        "precision": precision,
        "recall": recall,
        "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0,
        "accuracy": correct / characters if characters else 0,
        "accuracy_unit": "original codepoint BIO; not token accuracy",
        "test_sha256": hashlib.sha256(blob).hexdigest(),
        "model_sha256": predictor.provenance["model_sha256"],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    output.with_name(output.stem + "-predictions.json").write_text(
        json.dumps(predictions, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, default=Path("artifacts/local/ner-full/best_model"))
    parser.add_argument("--split-dir", type=Path, default=Path("data/private/ner-v1"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/metrics/ner_test_metrics.json"))
    args = parser.parse_args()
    report = evaluate_checkpoint(args.model, args.split_dir, args.output)
    print(json.dumps(report))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
