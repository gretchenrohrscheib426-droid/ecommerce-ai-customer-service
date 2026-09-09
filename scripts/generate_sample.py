"""Reproducible synthetic fixture, authored independently of course rows."""

import argparse
import json
from pathlib import Path


def generate():
    names = ["轻旅背包", "轻旅背包", "随行水杯"]
    colors = ["海蓝", "岩灰", "云白"]
    descriptions = ["轻量防水，配独立电脑隔层。", "日常通勤，配宽肩带。", "双层保温，杯盖防漏。"]
    data = {
        "base_category1": [{"id": 1, "name": "示例生活"}],
        "base_category2": [{"id": 11, "name": "出行用品", "category1_id": 1}],
        "base_category3": [
            {"id": 111, "name": "背包", "category2_id": 11},
            {"id": 112, "name": "水杯", "category2_id": 11},
        ],
        "base_trademark": [{"id": 1, "tm_name": "青岚示例"}, {"id": 2, "tm_name": "白屿示例"}],
        "base_attr_info": [{"id": 1, "attr_name": "材质", "category_level": 2, "category_id": 11}],
        "base_attr_value": [
            {"id": 1, "value_name": "再生织物", "attr_id": 1},
            {"id": 2, "value_name": "不锈钢", "attr_id": 1},
        ],
        "spu_info": [],
        "spu_sale_attr": [],
        "spu_sale_attr_value": [],
        "sku_info": [],
        "sku_attr_value": [],
        "sku_sale_attr_value": [],
    }
    for i in range(1, 4):
        data["spu_info"].append(
            {
                "id": i,
                "spu_name": names[i - 1],
                "description": descriptions[i - 1],
                "category3_id": 111 if i < 3 else 112,
                "tm_id": 2 if i == 2 else 1,
            }
        )
        data["spu_sale_attr"].append({"id": i, "spu_id": i, "base_sale_attr_id": 1, "sale_attr_name": "颜色"})
        data["spu_sale_attr_value"].append(
            {
                "id": i,
                "spu_id": i,
                "base_sale_attr_id": 1,
                "sale_attr_value_name": colors[i - 1],
                "sale_attr_name": "颜色",
            }
        )
        data["sku_info"].append(
            {
                "id": i,
                "spu_id": i,
                "sku_name": names[i - 1] + " " + colors[i - 1],
                "price": ["129", "99", "59"][i - 1],
                "is_sale": 1 if i < 3 else 0,
            }
        )
        data["sku_attr_value"].append({"id": i, "sku_id": i, "value_id": 1 if i < 3 else 2})
        data["sku_sale_attr_value"].append({"id": i, "sku_id": i, "sale_attr_value_id": i})
    return data


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    target = Path(__file__).resolve().parents[1] / "data/sample/business.json"
    if args.check:
        assert json.loads(target.read_text(encoding="utf-8")) == generate()
        print("passed: independent fixture matches generator")
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(generate(), ensure_ascii=False, indent=2), encoding="utf-8")
        print("Independent sample generated")
