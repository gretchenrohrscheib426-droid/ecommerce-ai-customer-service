"""Measured graph snapshots and strict expected/measured comparison."""

import json
from pathlib import Path


def snapshot(session):
    nodes = {
        r["label"]: r["count"]
        for r in session.run("MATCH (n) RETURN labels(n)[0] AS label,count(*) AS count")
    }
    edges = {
        f"{r['left']}-{r['type']}-{r['right']}": r["count"]
        for r in session.run(
            "MATCH (a)-[r]->(b) RETURN labels(a)[0] AS left,type(r) AS type,labels(b)[0] AS right,count(*) AS count"
        )
    }
    return {
        "nodes": nodes,
        "relationships": edges,
        "node_total": sum(nodes.values()),
        "relationship_total": sum(edges.values()),
    }


def ensure_namespace(session, namespace):
    # Dedicated database only; refuse mixing public sample and private course data.
    scopes = [r["scope"] for r in session.run("MATCH (n) RETURN DISTINCT n.dataset AS scope")]
    if scopes and scopes != [namespace]:
        raise ValueError("Database contains a different or unowned dataset; use a fresh instance")


def save_report(report, root):
    path = Path(root) / "artifacts/reconciliation/graph_sync_report.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
