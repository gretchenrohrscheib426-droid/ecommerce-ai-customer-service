"""Check tracked candidate hashes without rewriting the approved manifest."""

import hashlib
import json
from pathlib import Path

from check_public_boundary import CONTROL, candidates

ROOT = Path(__file__).resolve().parents[1]


def verify(root=ROOT):
    report = json.loads((root / "publish_manifest.json").read_text(encoding="utf-8"))
    records = {r["path"]: r for r in report["files"]}
    names = set(candidates(root))
    missing = sorted(set(records) - names)
    extra = sorted(names - set(records))
    changed = [
        name
        for name in sorted(names & set(records) - CONTROL)
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != records[name]["sha256"]
    ]
    result = {
        "status": "PASS" if not (missing or extra or changed) else "FAIL",
        "missing": missing,
        "extra": extra,
        "changed": changed,
    }
    print(json.dumps(result))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(verify())
