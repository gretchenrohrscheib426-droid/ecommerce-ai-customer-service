"""Local release gate. Never commits, pushes, stages, uploads or invokes an online LLM."""

import argparse
import hashlib
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from check_public_boundary import CONTROL, ROOT, candidates, check, git

REQUIRED = [
    "README.md",
    "README_EN.md",
    "LICENSE",
    "NOTICE.md",
    "THIRD_PARTY_NOTICES.md",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "CHANGELOG.md",
    "ROADMAP.md",
    "ARCHITECTURE.md",
    "PROJECT_STRUCTURE.md",
    "SOURCE_MAP.md",
    "RESUME_EVIDENCE.md",
    "annotation/ml_backend/requirements.txt",
    "annotation/ml_backend/README.md",
    "scripts/stop_api.ps1",
    "AGENTS.md",
    "PUBLISH_REVIEW.md",
    "demo.md",
    "pyproject.toml",
    "environment.yml",
    "requirements.txt",
    "requirements-dev.txt",
    ".env.example",
    ".gitignore",
    ".gitattributes",
    ".editorconfig",
    ".pre-commit-config.yaml",
    "docker-compose.yml",
    ".github/workflows/ci.yml",
    ".github/workflows/security.yml",
    ".github/workflows/release-check.yml",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/ISSUE_TEMPLATE/feature_request.yml",
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/pull_request_template.md",
    ".github/dependabot.yml",
    *[
        "docs/" + n + ".md"
        for n in [
            "GETTING_STARTED_WINDOWS",
            "ENVIRONMENT_SETUP",
            "DATA_PIPELINE",
            "NER_PIPELINE",
            "KNOWLEDGE_GRAPH",
            "HYBRID_RETRIEVAL",
            "AGENT_WORKFLOW",
            "CYPHER_SECURITY",
            "API",
            "DEMO_GUIDE",
            "TRAINING_GUIDE",
            "TROUBLESHOOTING",
            "PUBLIC_PRIVATE_BOUNDARY",
            "INTERVIEW_GUIDE",
            "RESUME_EVIDENCE",
        ]
    ],
    "examples/sample_questions.json",
    "examples/expected_responses.json",
    "examples/README.md",
    "data/sample/products.json",
    "data/sample/ner_sample.json",
    "data/sample/README.md",
    "data/README.md",
    "models/README.md",
    "models/.gitkeep",
    "materials_private/.gitkeep",
    "docs/assets/.gitkeep",
]


def run_check(name, argv):
    log = ROOT / "reports/private/release-checks" / (name + ".log")
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("w", encoding="utf-8") as f:
        result = subprocess.run([sys.executable, *argv], cwd=ROOT, stdout=f, stderr=subprocess.STDOUT)
    return {
        "status": "PASS" if result.returncode == 0 else "FAIL",
        "exit_code": result.returncode,
        "evidence": str(log.relative_to(ROOT)),
    }


def validate(run=False):
    missing = [p for p in REQUIRED if not (ROOT / p).is_file()]
    boundary = check()
    checks = {
        "required_files": {"status": "PASS" if not missing else "FAIL", "missing": missing},
        "public_boundary": boundary,
    }
    if run:
        for name, argv in {
            "ruff": ["-m", "ruff", "check", "src", "tests", "scripts", "annotation"],
            "mypy": ["-m", "mypy", "src/ecommerce_graph_agent"],
            "compile": ["-m", "compileall", "-q", "src", "scripts", "annotation"],
            "unit_and_api_mock": [
                "-m",
                "pytest",
                "tests/unit",
                "tests/e2e/test_api.py",
                "-q",
                "--junitxml=reports/private/release-checks/unit.xml",
            ],
            "pip_check": ["-m", "pip", "check"],
            "dependency_audit": ["scripts/audit_dependencies.py"],
        }.items():
            checks[name] = run_check(name, argv)
    else:
        checks["execution"] = {"status": "NOT_RUN", "reason": "Use --run for current-worktree checks"}
    audit = ROOT / "reports/private/dependency-audit-final.json"
    if run and audit.exists():
        data = json.loads(audit.read_text(encoding="utf-8"))
        findings = [
            {"package": d["name"], "version": d["version"], "ids": [v["id"] for v in d.get("vulns", [])]}
            for d in data.get("dependencies", [])
            if d.get("vulns")
        ]
        checks["dependency_audit"].update(findings=findings)
        if findings or any(d.get("skip_reason") for d in data.get("dependencies", [])):
            checks["dependency_audit"]["status"] = "FAIL"
    else:
        checks["dependency_audit"] = {"status": "NOT_RUN", "reason": "No current audit evidence"}
    names = candidates()
    for name in CONTROL:
        if name not in names:
            names.append(name)
    manifest = {
        "schema_version": 2,
        "dataset": "independent-sample",
        "publication_target": "gretchenrohrscheib426-droid/ecommerce-ai-customer-service",
        "visibility": "PUBLIC",
        "branch": "main",
        "exclude": ["course originals", "private SQL and annotations", "weights", "runtimes", "secrets", "personal fields", "raw local reports"],
        "digest_policy": "Control files listed with null hashes to avoid self-reference; all other entries SHA-256.",
        "files": [
            {
                "path": n,
                "sha256": None if n in CONTROL else hashlib.sha256((ROOT / n).read_bytes()).hexdigest(),
                "bytes": None if n in CONTROL else (ROOT / n).stat().st_size,
            }
            for n in sorted(names)
        ],
    }
    (ROOT / "publish_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    observed = {}
    for name, relative in {
        "real_database_integration": "reports/private/github-real-integration.xml",
        "independent_ml_sdk_mock": "reports/private/github-ml-sdk.xml",
        "synthetic_training_contract": "reports/private/transformers-contract.xml",
    }.items():
        path = ROOT / relative
        if path.exists():
            suites = ET.parse(path).getroot()
            observed[name] = {**junit_status(suites), "evidence": relative,
                              "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        else:
            observed[name] = {"status": "NOT_RUN", "evidence": relative}
    for name, relative in {
        "browser_real_and_fault_injection": "reports/private/browser-e2e.json",
        "native_restart": "reports/private/public-verification.json",
        "clean_source_installation": "reports/private/github-clean-validation.json",
    }.items():
        path = ROOT / relative
        if path.exists():
            value = json.loads(path.read_text(encoding="utf-8"))
            passed = value.get("status") == "passed" or (
                name == "clean_source_installation"
                and all(c["status"] == "PASS" for c in value["checks"].values())
            )
            observed[name] = {"status": "PASS" if passed else "FAIL", "evidence": relative,
                              "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        else:
            observed[name] = {"status": "NOT_RUN", "evidence": relative}
    report = {
        "schema_version": 2,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "READY" if all(v["status"] == "PASS" for v in checks.values()) else "NOT_READY",
        "checks": checks,
        "observed_verifications": observed,
        "source_revision": git(ROOT, "rev-parse", "HEAD").strip(),
        "worktree_has_uncommitted_changes": bool(git(ROOT, "status", "--porcelain")),
        "validation_subject": "worktree content identified by the companion publish manifest; HEAD is the parent revision at gate execution",
        "github_actions": "See actual GitHub run for the published commit; this local gate does not query Actions",
        "docker_runtime": "NOT_RUN",
        "full_training_of_this_revision": "NOT_RUN: no verified trained checkpoint for this revision",
        "deepseek_online": "NOT_RUN: no authorized online inference configured",
        "deployment": "LOCAL_ONLY",
    }
    (ROOT / "release_validation.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "files": len(names),
                "checks": {k: v["status"] for k, v in checks.items()},
            },
            ensure_ascii=False,
        )
    )
    return 0 if report["status"] == "READY" else 1


def junit_status(root):
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    total = sum(int(s.get("tests", "0")) for s in suites)
    skipped = sum(int(s.get("skipped", "0")) for s in suites)
    failures = sum(int(s.get("failures", "0")) + int(s.get("errors", "0")) for s in suites)
    return {"status": "FAIL" if failures else ("PASS" if total > skipped else "NOT_RUN"),
            "tests": total, "passed": total - skipped - failures, "skipped": skipped, "failures": failures}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--run", action="store_true")
    raise SystemExit(validate(p.parse_args().run))
