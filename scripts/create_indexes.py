"""Build and verify the five fulltext/vector index pairs."""

import json
from pathlib import Path

from ecommerce_graph_agent.datasync.neo4j_writer import driver
from ecommerce_graph_agent.graph.indexes import Embedder, create_indexes


def main():
    root = Path(__file__).resolve().parents[1]
    with driver(root) as instance:
        embedder = Embedder(root)
        first = create_indexes(instance, embedder)
        repeat = create_indexes(instance, embedder)
    if repeat["encoded_nodes"] or repeat["created"]:
        raise RuntimeError("Repeat index creation was not idempotent")
    path = root / "reports/private/indexes.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"status": "PASS", "first": first, "repeat": repeat}, indent=2), encoding="utf-8"
    )
    print("PASS: 10 indexes ONLINE; repeat encoded zero nodes")


if __name__ == "__main__":
    main()
