"""Full upsert from whitelisted MySQL business tables; never CDC or delete sync."""

import json
from collections import Counter, defaultdict
from pathlib import Path

from ..graph.constraints import ensure_constraints
from ..graph.schema import GROUPS, LABELS
from .mysql_reader import read_business
from .neo4j_writer import driver, write_nodes, write_relationships
from .reconciliation import ensure_namespace, snapshot
from .validate import SQL_SHA256, graph_plan


def sync_plan(instance, plan, namespace):
    by_label = defaultdict(list)
    for node in plan["nodes"]:
        if node["label"] not in LABELS:
            raise ValueError("Label outside whitelist")
        by_label[node["label"]].append({**node["properties"], "dataset": namespace})
    by_group = defaultdict(list)
    for left, lid, relation, right, rid in plan["edges"]:
        key = (left, relation, right)
        if key not in GROUPS:
            raise ValueError("Relationship outside whitelist")
        by_group[key].append({"left": lid, "right": rid})
    with instance.session(database="neo4j") as session:
        ensure_namespace(session, namespace)
        before = snapshot(session)
        ensure_constraints(session)

        def transaction(tx):
            stats = {"nodes_created": 0, "relationships_created": 0, "properties_set": 0}
            for label, rows in by_label.items():
                result = write_nodes(tx, label, rows, namespace)
                for key in stats:
                    stats[key] += result[key]
            for (left, relation, right), rows in by_group.items():
                result = write_relationships(tx, (left, relation, right), rows, namespace)
                for key in stats:
                    stats[key] += result[key]
            return stats

        counters = session.execute_write(transaction)
        after = snapshot(session)
    expected_labels = Counter(n["label"] for n in plan["nodes"])
    expected_groups = Counter(f"{a}-{rel}-{b}" for a, _, rel, b, _ in plan["edges"])
    measured_labels = {k: v for k, v in after["nodes"].items() if k != "Tag"}
    measured_groups = {k: v for k, v in after["relationships"].items() if k != "SPU-Have-Tag"}
    if measured_labels != expected_labels or measured_groups != expected_groups:
        raise RuntimeError("Actual graph reconciliation failed; inspect scoped database")
    return {
        "status": "passed",
        "namespace": namespace,
        "operation": "full upsert; source deletions not synchronized",
        "before": before,
        "after": after,
        "counters": counters,
        "quarantined_relationship_rows": len(plan["quarantine"]),
        "duplicate_source_edges": plan["duplicate_edges"],
        "expected_labels": dict(expected_labels),
        "expected_groups": dict(expected_groups),
    }


def sync_course(root):
    root = Path(root)
    tables = read_business(root)
    known = json.loads((root / "data/private/known-missing.json").read_text(encoding="utf-8"))
    plan = graph_plan(tables, mode="quarantine-known", source_sha=SQL_SHA256, known_missing=known)
    with driver(root) as d:
        first = sync_plan(d, plan, "course-private")
        second = sync_plan(d, plan, "course-private")
    assert first["after"] == second["after"]
    assert second["counters"]["nodes_created"] == 0 and second["counters"]["relationships_created"] == 0
    report = {"status": "passed", "first_import": first, "repeat_import": second}
    (root / "reports/private/graph-structured.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return report
