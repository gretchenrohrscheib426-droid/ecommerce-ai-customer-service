"""Generate Synthetic Demo Data without reading any course file."""

import argparse
import json
from pathlib import Path

from generate_sample import generate

ROOT = Path(__file__).resolve().parents[1]


def payloads():
    business = generate()
    spans = {1: [(0, 4)], 2: [(6, 9)], 3: [(0, 4), (5, 9)]}
    ner = [
        {
            "id": r["id"],
            "text": r["description"],
            "label": [
                {"start": a, "end": b, "text": r["description"][a:b], "labels": ["TAG"]}
                for a, b in spans[r["id"]]
            ],
        }
        for r in business["spu_info"]
    ]
    products = {
        "dataset": "Synthetic Demo Data",
        "version": "independent-v1",
        "production_data": False,
        "spu": business["spu_info"],
        "sku": business["sku_info"],
        "brands": business["base_trademark"],
        "tags": ner,
        "relationships_source": "business.json contains 12 relational tables",
    }
    return {"business.json": business, "products.json": products, "ner_sample.json": ner}


def main(check=False):
    folder = ROOT / "data/sample"
    folder.mkdir(parents=True, exist_ok=True)
    for name, content in payloads().items():
        path = folder / name
        if check:
            if json.loads(path.read_text(encoding="utf-8")) != content:
                raise ValueError("Synthetic fixture differs from generator: " + name)
        else:
            path.write_text(json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8")
    print("PASS: Synthetic Demo Data; 3 SPU, 3 SKU, 2 fictitious brands; no course rows")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    main(parser.parse_args().check)
