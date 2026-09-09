"""Validate original-character spans, freeze splits, align fast-tokenizer offsets."""

import hashlib
import json
import random
from pathlib import Path

from .data_validation import validate_record

LABELS = ["B-TAG", "I-TAG", "O"]


def from_utf16(text, offset):
    if type(offset) is not int or offset < 0:
        raise ValueError("Invalid UTF-16 offset")
    units = 0
    for index, char in enumerate(text):
        if units == offset:
            return index
        units += 2 if ord(char) > 0xFFFF else 1
    if units == offset:
        return len(text)
    raise ValueError("Offset splits a surrogate pair or exceeds text")


def to_utf16(text, offset):
    if type(offset) is not int or not 0 <= offset <= len(text):
        raise ValueError("Invalid Python offset")
    return len(text[:offset].encode("utf-16-le")) // 2


def align_labels(text, spans, offsets, special_mask):
    validate_record({"text": text, "label": spans})
    if len(offsets) != len(special_mask):
        raise ValueError("Tokenizer output shape mismatch")
    labels, seen = [], set()
    coverage: dict[int, list[tuple[int, int]]] = {i: [] for i in range(len(spans))}
    for (start, end), special in zip(offsets, special_mask, strict=True):
        if special or start == end:
            labels.append(-100)
            continue
        if not 0 <= start < end <= len(text):
            raise ValueError("Tokenizer returned invalid offsets")
        overlaps = [i for i, s in enumerate(spans) if start < s["end"] and s["start"] < end]
        if not overlaps:
            labels.append(2)
            continue
        if len(overlaps) != 1:
            raise ValueError("Token crosses multiple annotated entities")
        i = overlaps[0]
        span = spans[i]
        if start < span["start"] or end > span["end"]:
            raise ValueError("Annotation boundary falls inside tokenizer token")
        labels.append(1 if i in seen else 0)
        seen.add(i)
        coverage[i].append((start, end))
    for i, span in enumerate(spans):
        chunks = coverage[i]
        if not chunks or chunks[0][0] != span["start"] or chunks[-1][1] != span["end"]:
            raise ValueError("Annotation boundary is unrepresentable; never silently truncate")
        covered = set(j for start, end in chunks for j in range(start, end))
        if any(not text[j].isspace() for j in range(span["start"], span["end"]) if j not in covered):
            raise ValueError("Tokenizer dropped annotated non-whitespace characters")
    return labels


def tokenize_record(tokenizer, row, max_length=512):
    spans = validate_record(row)
    result = tokenize_with_offsets(tokenizer, row["text"], max_length)
    result["labels"] = align_labels(
        row["text"], spans, result.pop("offset_mapping"), result.pop("special_tokens_mask")
    )
    return result


def tokenize_with_offsets(tokenizer, text, max_length=512, return_tensors=None):
    """Character words + fast word_ids; map local token offsets back to original text."""
    if not getattr(tokenizer, "is_fast", False):
        raise ValueError("Fast tokenizer with word_ids required")
    result = tokenizer(
        list(text),
        is_split_into_words=True,
        return_offsets_mapping=True,
        return_special_tokens_mask=True,
        truncation=False,
        return_tensors=return_tensors,
    )
    word_ids = result.word_ids()
    if len(word_ids) > max_length:
        raise ValueError("Sequence exceeds max_length; explicit windowing required; truncation refused")
    local = result["offset_mapping"][0].tolist() if return_tensors else result["offset_mapping"]
    offsets = [
        (0, 0) if word is None else (word + start, word + end)
        for word, (start, end) in zip(word_ids, local, strict=True)
    ]
    result["offset_mapping"] = offsets
    return result


def prepare(path, output, seed=42):
    path, output = Path(path), Path(output)
    rows = json.loads(path.read_text(encoding="utf-8"))
    if len({r["id"] for r in rows}) != len(rows):
        raise ValueError("Duplicate record IDs")
    valid, quarantine = [], []
    for row in rows:
        try:
            validate_record(row)
        except ValueError as error:
            quarantine.append({"record": row, "reason": str(error), "resolution": "pending-human-review"})
        else:
            valid.append(row)
    # Group exact text to keep repeated product titles out of different splits.
    groups: dict[str, list[dict]] = {}
    for row in valid:
        key = hashlib.sha256(row["text"].encode()).hexdigest()
        groups.setdefault(key, []).append(row)
    hashes = sorted(groups)
    random.Random(seed).shuffle(hashes)
    ntest = round(len(hashes) * 0.1)
    nvalid = round(len(hashes) * 0.1)
    partitions = {
        "test": hashes[:ntest],
        "validation": hashes[ntest : ntest + nvalid],
        "train": hashes[ntest + nvalid :],
    }
    output.mkdir(parents=True, exist_ok=True)
    manifest = {
        "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "seed": seed,
        "offset_unit": "python-codepoint",
        "quarantined": len(quarantine),
        "splits": {},
    }
    for name, keys in partitions.items():
        subset = [row for key in keys for row in groups[key]]
        content = json.dumps(subset, ensure_ascii=False, indent=2)
        target = output / f"{name}.json"
        if target.exists() and target.read_text(encoding="utf-8") != content:
            raise ValueError("Frozen split differs; choose a new output directory")
        # A frozen manifest describes file bytes, including on Windows (no CRLF translation).
        target.write_bytes(content.encode("utf-8"))
        manifest["splits"][name] = {
            "count": len(subset),
            "ids": [r["id"] for r in subset],
            "text_hashes": keys,
            "sha256": hashlib.sha256(content.encode()).hexdigest(),
        }
    (output / "quarantine.json").write_text(
        json.dumps(quarantine, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return manifest
