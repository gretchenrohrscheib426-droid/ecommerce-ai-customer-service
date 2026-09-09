"""Explicit structured or Tag synchronization; public/private input selection is visible."""

import argparse
import json
from pathlib import Path

from ecommerce_graph_agent.config import Settings
from ecommerce_graph_agent.datasync.mysql_reader import read_business
from ecommerce_graph_agent.datasync.neo4j_writer import driver
from ecommerce_graph_agent.datasync.reconciliation import save_report
from ecommerce_graph_agent.datasync.table_sync import sync_course, sync_plan
from ecommerce_graph_agent.datasync.text_sync import sync_tags
from ecommerce_graph_agent.datasync.validate import graph_plan

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("kind", choices=["structured", "tags"])
    p.add_argument("--source", choices=["sample", "mysql"], default="sample")
    p.add_argument("--private-course", action="store_true")
    a = p.parse_args()
    settings = Settings.load(ROOT)
    if a.private_course:
        if settings.demo_mode:
            raise ValueError("Set DEMO_MODE=false only in the private reproduction workspace")
        if a.kind == "structured":
            report = sync_course(ROOT)
        else:
            predictions = json.loads(
                (ROOT / "artifacts/local/ner-full/descriptor-predictions.json").read_text(encoding="utf-8")
            )
            with driver(ROOT) as instance:
                report = sync_tags(instance, predictions, "course-private")
    elif a.kind == "tags":
        from sample_demo import build

        build()
        return
    else:
        source = (
            read_business(ROOT)
            if a.source == "mysql"
            else json.loads((ROOT / "data/sample/business.json").read_text(encoding="utf-8"))
        )
        plan = graph_plan(source)
        with driver(ROOT) as instance:
            first = sync_plan(instance, plan, "independent-sample")
            second = sync_plan(instance, plan, "independent-sample")
        if second["counters"]["nodes_created"] or second["counters"]["relationships_created"]:
            raise RuntimeError("Repeat sync created duplicates")
        report = {"status": "PASS", "input": a.source, "first": first, "repeat": second}
    print(str(save_report(report, ROOT)))


if __name__ == "__main__":
    main()
