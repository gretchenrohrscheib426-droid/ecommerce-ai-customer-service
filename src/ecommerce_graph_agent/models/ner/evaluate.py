"""Fresh-process offline final test and descriptor extraction; no test-driven tuning."""

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from .predict import Predictor


def score_spans(gold, predicted):
    gold = {(x["start"], x["end"]) for x in gold}
    pred = {(x["start"], x["end"]) for x in predicted}
    return len(gold & pred), len(pred - gold), len(gold - pred)


def evaluate(root, run_name="ner-full"):
    root = Path(root)
    output = root / "artifacts/local" / run_name
    result_path = output / "test-evaluation.json"
    if result_path.exists():
        raise FileExistsError("Final test already evaluated; reuse recorded results")
    import torch

    torch.set_num_threads(6)
    predictor = Predictor(output / "best_model", device="cuda" if torch.cuda.is_available() else "cpu")
    split = root / "data/private/ner-v1"
    manifest = json.loads((split / "manifest.json").read_text(encoding="utf-8"))
    data = (split / "test.json").read_bytes()
    if hashlib.sha256(data).hexdigest() != manifest["splits"]["test"]["sha256"]:
        raise ValueError("Frozen test hash changed")
    rows = json.loads(data)
    counts = [0, 0, 0]
    errors = []
    predictions = []
    for row in rows:
        pred = predictor.predict(row["text"])
        scores = score_spans(row["label"], pred)
        counts = [a + b for a, b in zip(counts, scores, strict=True)]
        item = {"id": row["id"], "text": row["text"], "gold": row["label"], "predicted": pred}
        predictions.append(item)
        if scores[1] or scores[2]:
            errors.append(item)
    tp, fp, fn = counts
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    report = {
        "status": "passed",
        "scope": "frozen independent title test; not descriptor F1",
        "sys.executable": sys.executable,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "count": len(rows),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
        "metric": "micro exact original-character TAG spans, isolated I starts entity as in Predictor",
        "model_sha256": predictor.provenance["model_sha256"],
        "test_sha256": hashlib.sha256(data).hexdigest(),
        "offline_fresh_process": True,
        "error_samples": len(errors),
    }
    result_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "test-predictions.json").write_text(
        json.dumps(predictions, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output / "test-errors.json").write_text(
        json.dumps(errors, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    business = json.loads((root / "data/private/business.json").read_text(encoding="utf-8"))
    extracted = []
    for row in business["spu_info"]:
        text = row["description"]
        extracted.append(
            {
                "spu_id": row["id"],
                "text": text,
                "source_sha256": hashlib.sha256(text.encode()).hexdigest(),
                "spans": predictor.predict(text),
                "model_sha256": predictor.provenance["model_sha256"],
                "semantic_review": "pending" if row["id"] in [12, 13] else "not_human_gold",
                "cross_domain_gold": False,
            }
        )
    (output / "descriptor-predictions.json").write_text(
        json.dumps(extracted, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=Path.cwd())
    p.add_argument("--run-name", default="ner-full")
    a = p.parse_args()
    evaluate(a.root, a.run_name)
