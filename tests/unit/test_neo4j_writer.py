from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from ecommerce_graph_agent.datasync.neo4j_writer import write_nodes, write_relationships


def test_stable_id_and_mutable_name_and_measured_count():
    tx = MagicMock()
    tx.run.return_value.single.return_value = {"matched": 1}
    tx.run.return_value.consume.return_value.counters = SimpleNamespace(
        nodes_created=0, relationships_created=0, properties_set=2
    )
    result = write_nodes(tx, "SPU", [{"id": 7, "name": "改名商品"}], "test")
    query = tx.run.call_args.args[0]
    assert "MERGE (n:SPU {id:row.id})" in query and "SET n += row" in query
    assert result["created_or_matched_count"] == 1 and result["nodes_created"] == 0


def test_missing_endpoint_raises_before_relationship_write():
    tx = MagicMock()
    tx.run.return_value.single.return_value = {"missing_start": 0, "missing_end": 1}
    with pytest.raises(ValueError, match="end=1"):
        write_relationships(tx, ("SPU", "Belong", "Category3"), [{"left": 1, "right": 999}], "test")
    assert tx.run.call_count == 1


def test_bad_identity_and_label_never_hit_driver():
    tx = MagicMock()
    for label, row in [("User", {"id": 1, "name": "private"}), ("SPU", {"id": True, "name": "invalid"})]:
        with pytest.raises(ValueError):
            write_nodes(tx, label, [row], "test")
    tx.run.assert_not_called()
