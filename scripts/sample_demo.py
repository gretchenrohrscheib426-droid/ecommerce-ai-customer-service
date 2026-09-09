"""Independent public data in its own Neo4j instance; no course material required."""

import argparse
import hashlib
import json
import secrets
import shutil
import sys
import time

from services import LOCAL, LOGS, NEO, ROOT

from ecommerce_graph_agent.datasync.sync import sync_plan, sync_tags
from ecommerce_graph_agent.datasync.validate import graph_plan
from ecommerce_graph_agent.db.neo4j import driver


def configure(bolt_port=7689, http_port=7476, api_port=8012):
    ports = (bolt_port, http_port, api_port)
    if any(type(port) is not int or not 1024 <= port <= 65535 for port in ports):
        raise ValueError("Use unprivileged ports from 1024 to 65535")
    if len(set(ports)) != len(ports):
        raise ValueError("Service ports must be distinct")
    runtime = LOCAL / "runtime.json"
    desired = {
        "neo4j_uri": f"bolt://127.0.0.1:{bolt_port}",
        "neo4j_http_port": http_port,
        "api_port": api_port,
        "dataset": "independent-sample",
    }
    if (LOCAL / "neo4j/conf/neo4j.conf").exists() and not runtime.exists():
        raise RuntimeError("Existing course instance detected; use a clean public-release directory")
    existing = json.loads(runtime.read_text()) if runtime.exists() else {}
    if any(existing.get(k, v) != v for k, v in desired.items()):
        raise RuntimeError("Existing runtime differs")
    LOCAL.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    runtime.write_text(json.dumps({**existing, **desired}, indent=2), encoding="utf-8")
    authfile = LOCAL / "credentials.json"
    if not authfile.exists():
        authfile.write_text(json.dumps({"neo4j": secrets.token_urlsafe(32)}), encoding="utf-8")
    conf = LOCAL / "neo4j/conf"
    conf.mkdir(parents=True, exist_ok=True)
    for name in ["server-logs.xml", "user-logs.xml"]:
        if not (conf / name).exists():
            shutil.copyfile(NEO / "conf" / name, conf / name)
    path = conf / "neo4j.conf"
    if not path.exists():
        settings = {
            "server.default_listen_address": "127.0.0.1",
            "server.default_advertised_address": "127.0.0.1",
            "server.bolt.enabled": "true",
            "server.bolt.listen_address": f"127.0.0.1:{bolt_port}",
            "server.bolt.advertised_address": f"127.0.0.1:{bolt_port}",
            "server.http.enabled": "true",
            "server.http.listen_address": f"127.0.0.1:{http_port}",
            "server.http.advertised_address": f"127.0.0.1:{http_port}",
            "server.https.enabled": "false",
            "server.memory.pagecache.size": "256m",
            "server.windows_service_name": "ecommerce-independent-sample",
            "dbms.security.auth_enabled": "true",
            "dbms.usage_report.enabled": "false",
            "dbms.security.allow_csv_import_from_file_urls": "false",
            "server.databases.default_to_read_only": "false",
            "db.transaction.timeout": "5s",
        }
        for folder in ["data", "logs", "import", "run"]:
            settings[f"server.directories.{folder}"] = (LOCAL / "neo4j" / folder).as_posix()
        path.write_text("\n".join(f"{k}={v}" for k, v in settings.items()) + "\n", encoding="utf-8")
    print("Independent sample runtime configured; no course SQL or data used")


def secure():
    from neo4j import GraphDatabase
    from neo4j.exceptions import ServiceUnavailable

    from ecommerce_graph_agent.config import Settings

    auth = json.loads((LOCAL / "credentials.json").read_text())
    marker = LOCAL / "neo4j/secured.json"
    if marker.exists():
        with driver(ROOT) as d:
            d.verify_connectivity()
        return
    deadline = time.monotonic() + 60
    while True:
        try:
            with (
                GraphDatabase.driver(
                    Settings.load(ROOT).neo4j_uri, auth=("neo4j", "neo4j"), connection_timeout=2
                ) as d,
                d.session(database="system") as s,
            ):
                s.run(
                    "ALTER CURRENT USER SET PASSWORD FROM $old TO $new", old="neo4j", new=auth["neo4j"]
                ).consume()
            break
        except ServiceUnavailable:
            if time.monotonic() >= deadline:
                raise
            time.sleep(1)
    marker.write_text('{"initialized_by":"independent-sample"}', encoding="utf-8")
    print("Independent database authentication configured")


def build():
    business = json.loads((ROOT / "data/sample/business.json").read_text(encoding="utf-8"))
    plan = graph_plan(business)
    # This fixture is explicitly human-authored, never a fake BERT checkpoint.
    samples = {1: [(0, 4)], 2: [(6, 9)], 3: [(0, 4), (5, 9)]}
    extracted = []
    for row in business["spu_info"]:
        text = row["description"]
        spans = [{"start": a, "end": b, "text": text[a:b], "labels": ["TAG"]} for a, b in samples[row["id"]]]
        extracted.append(
            {
                "spu_id": row["id"],
                "text": text,
                "source_sha256": hashlib.sha256(text.encode()).hexdigest(),
                "spans": spans,
                "model_sha256": "independent-manual-fixture-v1-not-BERT",
                "semantic_review": "authored synthetic fixture",
            }
        )
    with driver(ROOT) as d:
        first = sync_plan(d, plan, "independent-sample")
        tagged = sync_tags(d, extracted, "independent-sample")
        second = sync_plan(d, plan, "independent-sample")
        tags_again = sync_tags(d, extracted, "independent-sample")
    assert second["counters"]["nodes_created"] == 0 and second["counters"]["relationships_created"] == 0
    assert tags_again["after"] == tagged["after"]
    (ROOT / "configs/approved-aliases.json").write_text(
        json.dumps(
            {"青岚": ["BaseTrademark:1"], "随行杯": ["SPU:3"], "轻旅": ["SPU:1", "SPU:2"]},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    report = {
        "status": "passed",
        "sys.executable": sys.executable,
        "profile": "independent-sample",
        "structured": first,
        "tags": tagged,
        "repeat_structured": second,
        "repeat_tags": tags_again,
        "BERT_inference": "not_run; public Tags are manual synthetic fixtures",
    }
    (LOGS / "sample-build.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps({"status": "passed", "actual": tagged["after"], "tag_source": "manual fixture, not BERT"})
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["configure", "secure", "build"])
    p.add_argument("--bolt-port", type=int, default=7689)
    p.add_argument("--http-port", type=int, default=7476)
    p.add_argument("--api-port", type=int, default=8012)
    a = p.parse_args()
    if a.action == "configure":
        configure(a.bolt_port, a.http_port, a.api_port)
    else:
        {"secure": secure, "build": build}[a.action]()
