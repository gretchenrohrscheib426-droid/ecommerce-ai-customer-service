"""Fixed course-compatible graph labels and directed relationships."""

from ..datasync.validate import TABLES

LABELS = {v[0] for v in TABLES.values()}
GROUPS = {
    ("Category2", "Belong", "Category1"),
    ("Category3", "Belong", "Category2"),
    *{(f"Category{i}", "Have", "BaseAttr") for i in (1, 2, 3)},
    ("BaseAttr", "Have", "BaseAttrValue"),
    ("SPU", "Belong", "Category3"),
    ("SPU", "Belong", "BaseTrademark"),
    ("SPU", "Have", "SaleAttr"),
    ("SaleAttr", "Have", "SaleAttrValue"),
    ("SKU", "Belong", "SPU"),
    ("SKU", "Have", "BaseAttrValue"),
    ("SKU", "Have", "SaleAttrValue"),
}
