"""Strict validation or explicit whole-record quarantine; never overwrite spans."""

import hashlib
import json
from pathlib import Path


class AnnotationError(ValueError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


def validate_record(row, max_chars=4096):
    if not isinstance(row, dict) or not isinstance(row.get("text"), str) or not row["text"].strip():
        raise AnnotationError("invalid", "Nonempty text required")
    text = row["text"]
    if len(text) > max_chars:
        raise AnnotationError("too_long", "Text exceeds validated character limit")
    if not isinstance(row.get("label"), list):
        raise AnnotationError("invalid", "label must be a list")
    spans = row["label"]
    for span in spans:
        if not isinstance(span, dict):
            raise AnnotationError("invalid", "Each span must be an object")
        start, end = span.get("start"), span.get("end")
        if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(text):
            raise AnnotationError("invalid", "Invalid character span")
        if span.get("labels") != ["TAG"] or text[start:end] != span.get("text"):
            raise AnnotationError("invalid", "Span text/label mismatch")
    spans = sorted(spans, key=lambda s: (s["start"], s["end"]))
    seen, previous = set(), -1
    for span in spans:
        key = (span["start"], span["end"])
        if key in seen:
            raise AnnotationError("duplicate", "Duplicate TAG span")
        if span["start"] < previous:
            raise AnnotationError("overlap", "Overlapping TAG spans require manual review")
        seen.add(key)
        previous = span["end"]
    return spans


def validate_dataset(rows, mode="strict", output=None, max_chars=4096):
    if mode not in {"strict", "quarantine"} or not isinstance(rows, list):
        raise ValueError("Expected a list and strict/quarantine mode")
    valid, invalid = [], []
    counts = {"valid_count": 0, "invalid_count": 0, "overlap_count": 0, "duplicate_count": 0}
    for row in rows:
        try:
            validate_record(row, max_chars)
        except AnnotationError as error:
            if mode == "strict":
                raise
            invalid.append(
                {
                    "record": row,
                    "code": error.code,
                    "reason": str(error),
                    "resolution": "pending-human-review",
                }
            )
            counts["invalid_count"] += 1
            if error.code in {"overlap", "duplicate"}:
                counts[error.code + "_count"] += 1
        else:
            valid.append(row)
            counts["valid_count"] += 1
    report = {
        **counts,
        "mode": mode,
        "valid": valid,
        "quarantine": invalid,
        "source_sha256": hashlib.sha256(
            json.dumps(rows, ensure_ascii=False, sort_keys=True).encode()
        ).hexdigest(),
    }
    if output is not None:
        path = Path(output)
        if path.exists():
            raise FileExistsError("Choose a new derived validation report")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report
