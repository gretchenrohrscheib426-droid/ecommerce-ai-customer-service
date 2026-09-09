"""Build a deterministic graph plan; never fabricate missing endpoints."""

import hashlib
import json
from collections import Counter

SQL_SHA256 = "b674a22d345b756aa40d48dc1a54aa72cb6cfb85baecd0ae7ad537b8a5159ef1"
TABLES = {
    "base_category1": ("Category1", "name"),
    "base_category2": ("Category2", "name"),
    "base_category3": ("Category3", "name"),
    "base_trademark": ("BaseTrademark", "tm_name"),
    "base_attr_info": ("BaseAttr", "attr_name"),
    "base_attr_value": ("BaseAttrValue", "value_name"),
    "spu_info": ("SPU", "spu_name"),
    "spu_sale_attr": ("SaleAttr", "sale_attr_name"),
    "spu_sale_attr_value": ("SaleAttrValue", "sale_attr_value_name"),
    "sku_info": ("SKU", "sku_name"),
}
BUSINESS_TABLES = tuple(TABLES) + ("sku_attr_value", "sku_sale_attr_value")


class DataIntegrityError(ValueError):
    pass


def digest(value):
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def graph_plan(tables, mode="strict", source_sha=None, known_missing=None):
    if mode not in {"strict", "quarantine-known"}:
        raise ValueError("Unknown anomaly mode")
    if set(tables) != set(BUSINESS_TABLES):
        raise DataIntegrityError("Exactly the 12 whitelisted business tables are required")
    nodes, edges, missing = [], [], []
    keys: dict[str, set[int]] = {}
    for table, (label, column) in TABLES.items():
        keys[label] = set()
        for row in tables[table]:
            if type(row.get("id")) is not int or row["id"] in keys[label]:
                raise DataIntegrityError(f"Invalid or duplicate {table}.id")
            name = row.get(column)
            if not isinstance(name, str) or not name.strip():
                raise DataIntegrityError(f"Empty {table}.{column}")
            keys[label].add(row["id"])
            props = {
                "id": row["id"],
                "name": name,
                "canonical_id": f"{label}:{row['id']}",
                "source_table": table,
                "source_hash": digest(row),
            }
            if label == "SPU":
                props["description"] = row["description"]
            if label == "SKU":
                props["price"] = str(row["price"])
                props["is_sale"] = row["is_sale"]
            nodes.append({"label": label, "properties": props})

    def edge(table, row, left, left_id, relation, right, right_id, foreign_key):
        if left_id not in keys[left] or right_id not in keys[right]:
            missing.append(
                {
                    "table": table,
                    "row_id": row["id"],
                    "foreign_key": foreign_key,
                    "left": [left, left_id],
                    "relation": relation,
                    "right": [right, right_id],
                }
            )
        else:
            edges.append((left, left_id, relation, right, right_id))

    for row in tables["base_category2"]:
        edge(
            "base_category2",
            row,
            "Category2",
            row["id"],
            "Belong",
            "Category1",
            row["category1_id"],
            "category1_id",
        )
    for row in tables["base_category3"]:
        edge(
            "base_category3",
            row,
            "Category3",
            row["id"],
            "Belong",
            "Category2",
            row["category2_id"],
            "category2_id",
        )
    for row in tables["base_attr_info"]:
        if row["category_level"] not in (1, 2, 3):
            raise DataIntegrityError("Invalid category_level")
        edge(
            "base_attr_info",
            row,
            f"Category{row['category_level']}",
            row["category_id"],
            "Have",
            "BaseAttr",
            row["id"],
            "category_id",
        )
    for row in tables["base_attr_value"]:
        edge(
            "base_attr_value", row, "BaseAttr", row["attr_id"], "Have", "BaseAttrValue", row["id"], "attr_id"
        )
    for row in tables["spu_info"]:
        for target, column in (("Category3", "category3_id"), ("BaseTrademark", "tm_id")):
            edge("spu_info", row, "SPU", row["id"], "Belong", target, row[column], column)
    sale_map = {}
    for row in tables["spu_sale_attr"]:
        pair = (row["spu_id"], row["base_sale_attr_id"])
        if pair in sale_map:
            raise DataIntegrityError("Non-unique sale attribute composite key")
        sale_map[pair] = row["id"]
        edge("spu_sale_attr", row, "SPU", row["spu_id"], "Have", "SaleAttr", row["id"], "spu_id")
    for row in tables["spu_sale_attr_value"]:
        pair = (row["spu_id"], row["base_sale_attr_id"])
        if pair not in sale_map:
            raise DataIntegrityError("Sale attribute value cannot join composite key")
        edge(
            "spu_sale_attr_value",
            row,
            "SaleAttr",
            sale_map[pair],
            "Have",
            "SaleAttrValue",
            row["id"],
            "spu_id+base_sale_attr_id",
        )
    for row in tables["sku_info"]:
        edge("sku_info", row, "SKU", row["id"], "Belong", "SPU", row["spu_id"], "spu_id")
    for table, target, column in (
        ("sku_attr_value", "BaseAttrValue", "value_id"),
        ("sku_sale_attr_value", "SaleAttrValue", "sale_attr_value_id"),
    ):
        for row in tables[table]:
            edge(table, row, "SKU", row["sku_id"], "Have", target, row[column], column)
    if missing:
        if mode == "strict":
            raise DataIntegrityError(f"Missing endpoints: {len(missing)}; inspect quarantine report")
        if source_sha != SQL_SHA256 or not known_missing or digest(missing) != digest(known_missing):
            raise DataIntegrityError("Quarantine must match the exact audited source AND row identities")
        counts = Counter((r["table"], r["foreign_key"]) for r in missing)
        if counts != {("base_attr_value", "attr_id"): 36, ("sku_attr_value", "value_id"): 14}:
            raise DataIntegrityError("Unexpected anomaly counts")
    unique = sorted(set(edges), key=lambda e: tuple(map(str, e)))
    return {
        "nodes": nodes,
        "edges": unique,
        "quarantine": missing,
        "duplicate_edges": len(edges) - len(unique),
        "expected_nodes": len(nodes),
        "expected_edges": len(unique),
        "status": "static-plan-not-import-result",
    }
