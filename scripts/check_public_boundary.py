"""Inspect candidate files, index and reachable Git blobs without revealing matched secrets."""

import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_BYTES = 5 * 1024 * 1024
CONTROL = {"publish_manifest.json", "release_validation.json"}
FORBIDDEN_PARTS = {
    "build",
    "dist",
    "materials_private",
    ".runtime",
    ".cache",
    ".conda",
    ".venv-public",
    ".venv-clean",
    "artifacts",
    "logs",
    "checkpoints",
    "__pycache__",
}
FORBIDDEN_SUFFIXES = {
    ".sql",
    ".zip",
    ".docx",
    ".exe",
    ".msi",
    ".safetensors",
    ".pt",
    ".pth",
    ".bin",
    ".ckpt",
    ".pyc",
    ".pkl",
    ".db",
    ".sqlite",
    ".sqlite3",
}
PATTERNS = {
    "personal_absolute_directory": re.compile(rb"[A-Za-z]:[\\/](?:Projects|OneDrive|Desktop)[\\/]", re.I),
    "personal_unix_home": re.compile(rb"/(?:home|Users)/[A-Za-z0-9_.-]+/"),
    "private_key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "provider_key": re.compile(
        rb"\b(?:sk-[A-Za-z0-9]{20,}|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})\b"
    ),
    "credential_uri": re.compile(rb"(?:mysql|bolt|neo4j)(?:\+s)?://[^\s:/]+:[^\s@]{4,}@"),
    "personal_windows_home": re.compile(
        rb"[A-Za-z]:[\\/]Users[\\/](?!Public|YOUR_NAME|<)[A-Za-z0-9_.-]+", re.I
    ),
    "assigned_secret": re.compile(
        rb"(?im)^[ \t]*(?:DEEPSEEK_API_KEY|MYSQL_PASSWORD|MYSQL_ROOT_PASSWORD|NEO4J_PASSWORD)[ \t]*=[ \t]*['\"]?[A-Za-z0-9_/-]{12,}"
    ),
}


def git(root, *args, binary=False):
    return subprocess.check_output(
        ["git", "-C", str(root), *args], text=not binary, encoding=None if binary else "utf-8"
    )


def candidates(root=ROOT):
    names = git(root, "ls-files", "--cached", "--others", "--exclude-standard", "-z").split("\0")
    return sorted({n for n in names if n and (root / n).is_file()})


def inspect_blob(name, blob):
    path = Path(name)
    issues = []
    placeholder = name in {"materials_private/.gitkeep", "models/.gitkeep", "models/README.md"}
    if not placeholder and (
        FORBIDDEN_PARTS.intersection(path.parts)
        or any(p.startswith((".venv", ".conda")) for p in path.parts)
        or name.startswith(("data/private/", "reports/private/", "models/"))
    ):
        issues.append("private_path")
    if path.name == ".env" or (path.name.startswith(".env.") and path.name != ".env.example"):
        issues.append("environment_file")
    if path.suffix.lower() in FORBIDDEN_SUFFIXES:
        issues.append("private_or_binary_payload")
    if len(blob) > MAX_BYTES:
        issues.append("oversized")
    if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".ico"}:
        issues.extend(key for key, pattern in PATTERNS.items() if pattern.search(blob))
    return [{"path": name, "rule": rule} for rule in issues]


def check(root=ROOT, history=True):
    root = root.resolve()
    issues = []
    names = candidates(root)
    for name in names:
        if (root / name).is_symlink():
            issues.append({"path": name, "rule": "symlink"})
        else:
            issues.extend(
                {**r, "surface": "worktree"} for r in inspect_blob(name, (root / name).read_bytes())
            )
    for row in git(root, "ls-files", "-s").splitlines():
        meta, name = row.split("\t", 1)
        blob = git(root, "cat-file", "blob", meta.split()[1], binary=True)
        issues.extend({**r, "surface": "index"} for r in inspect_blob(name, blob))
    count = 0
    if history:
        seen = set()
        for row in git(root, "rev-list", "--objects", "--all").splitlines():
            oid, _, name = row.partition(" ")
            if not name or oid in seen or git(root, "cat-file", "-t", oid).strip() != "blob":
                continue
            seen.add(oid)
            count += 1
            issues.extend(
                {**r, "surface": "history", "object": oid}
                for r in inspect_blob(name, git(root, "cat-file", "blob", oid, binary=True))
            )
    return {
        "status": "PASS" if not issues else "FAIL",
        "candidate_files": len(names),
        "history_blobs_checked": count,
        "issues": issues,
        "limits": "Heuristic detection; no proof that every possible secret or PII is absent. Matches are never printed.",
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--output", type=Path)
    p.add_argument("--no-history", action="store_true")
    a = p.parse_args()
    report = check(a.root, not a.no_history)
    if a.output:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
