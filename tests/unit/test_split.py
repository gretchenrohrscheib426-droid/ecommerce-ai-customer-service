import hashlib
import json

from ecommerce_graph_agent.models.ner.process import prepare


def test_split_manifest_hashes_actual_bytes_and_freezes(tmp_path):
    source = tmp_path / "source.json"
    source.write_text(
        json.dumps([{"id": i, "text": f"示例{i}", "label": []} for i in range(20)]), encoding="utf-8"
    )
    out = tmp_path / "split"
    result = prepare(source, out)
    for name, item in result["splits"].items():
        assert hashlib.sha256((out / f"{name}.json").read_bytes()).hexdigest() == item["sha256"]
    assert prepare(source, out) == result
