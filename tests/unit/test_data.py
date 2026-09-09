import copy
import json
from pathlib import Path

import pytest

from ecommerce_graph_agent.datasync.validate import SQL_SHA256, DataIntegrityError, graph_plan

ROOT = Path(__file__).resolve().parents[2]


def sample():
    return json.loads((ROOT / "data/sample/business.json").read_text(encoding="utf-8"))


def test_same_name_keeps_two_ids():
    nodes = graph_plan(sample())["nodes"]
    identical_names = [n for n in nodes if n["properties"]["name"] == "轻旅背包"]
    assert len(identical_names) == 2
    assert len({n["properties"]["canonical_id"] for n in identical_names}) == 2


def test_unknown_or_missing_endpoint_fails_even_with_known_count_mode():
    tables = sample()
    tables["sku_attr_value"][0]["value_id"] = 999
    with pytest.raises(DataIntegrityError, match="Missing endpoints"):
        graph_plan(tables)
    with pytest.raises(DataIntegrityError, match="exact audited source"):
        graph_plan(tables, "quarantine-known", SQL_SHA256, [])


def test_duplicate_rows_become_one_relation_with_explicit_count():
    tables = sample()
    tables["sku_attr_value"].append(dict(tables["sku_attr_value"][0], id=5))
    assert graph_plan(tables)["duplicate_edges"] == 1


def test_duplicate_business_ids_rejected():
    tables = sample()
    tables["spu_info"].append(copy.deepcopy(tables["spu_info"][0]))
    with pytest.raises(DataIntegrityError, match="duplicate"):
        graph_plan(tables)
