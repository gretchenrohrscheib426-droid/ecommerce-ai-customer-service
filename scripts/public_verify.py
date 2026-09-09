"""Real independent Neo4j/HTTP checks; no mocks, paid API, course data or training."""

import argparse
import json
import sys
import time
from pathlib import Path

import httpx
from services import start, stop

from ecommerce_graph_agent.config import Settings
from ecommerce_graph_agent.datasync.sync import snapshot
from ecommerce_graph_agent.datasync.validate import graph_plan
from ecommerce_graph_agent.db.neo4j import driver

ROOT = Path(__file__).resolve().parents[1]
BASE = f"http://127.0.0.1:{Settings.load(ROOT).api_port}"


def inspect():
    with driver(ROOT) as d, d.session(database="neo4j") as session:
        counts = snapshot(session)
        indexes = [
            dict(r)
            for r in session.run(
                "SHOW INDEXES YIELD name,state,type WHERE type IN ['VECTOR','FULLTEXT'] RETURN name,state,type ORDER BY name"
            )
        ]
        assert len(indexes) == 10 and all(r["state"] == "ONLINE" for r in indexes)
        scopes = [r["dataset"] for r in session.run("MATCH(n) RETURN DISTINCT n.dataset AS dataset")]
        assert scopes == ["independent-sample"]
        assert session.run("MATCH(p:SPU {name:'轻旅背包'}) RETURN count(p) AS n").single()["n"] == 2
    with driver(ROOT) as d, d.session(database="system") as s:
        assert (
            s.run("SHOW DATABASES YIELD name,access WHERE name='neo4j' RETURN access").single()["access"]
            == "read-only"
        )
    return {"counts": counts, "indexes": indexes}


def wait_ready():
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        try:
            r = httpx.get(BASE + "/health/ready", timeout=2)
            if r.status_code == 200:
                return r.json()
        except httpx.HTTPError:
            pass
        time.sleep(0.5)
    raise RuntimeError("Public API failed readiness")


def main(restart=False):
    readiness = wait_ready()
    assert readiness["mode"] == "offline-local-templates"
    before = inspect()
    restart_record = None
    if restart:
        stopped = [stop(name) for name in ["api", "neo4j"]]
        begin = time.monotonic()
        started = [start(name) for name in ["neo4j", "api"]]
        wait_ready()
        elapsed = time.monotonic() - begin
        after = inspect()
        assert after == before
        restart_record = {
            "status": "passed",
            "seconds": elapsed,
            "stopped": stopped,
            "started": started,
            "reinstall": False,
            "reimport": False,
            "same_snapshot": True,
        }
    checks = []

    def ask(message, **extra):
        r = httpx.post(BASE + "/api/chat", json={"message": message, **extra}, timeout=20)
        assert r.status_code == 200
        result = r.json()
        checks.append({"message": message, "status": result["status"], "trace_id": result["trace_id"]})
        return result

    for text, gold in [
        ("青岚示例品牌有哪些商品", {"SPU:1", "SPU:3"}),
        ("白屿示例品牌有哪些商品", {"SPU:2"}),
        ("青岚品牌有哪些商品", {"SPU:1", "SPU:3"}),
    ]:
        value = ask(text)
        assert value["status"] == "ok" and {r["source_id"] for r in value["evidence"]} == gold
    initial = ask("轻旅背包价格")
    assert initial["status"] == "clarify"
    assert {r["canonical_id"] for r in initial["candidates"]} == {"SPU:1", "SPU:2"}
    follow = {"choice": "SPU:2", "clarification_token": initial["clarification_token"]}
    value = ask("轻旅背包价格", **follow)
    assert value["status"] == "ok" and {str(r["price"]) for r in value["evidence"]} == {"99"}
    assert ask("轻旅背包价格", **follow)["status"] == "invalid_request"
    value = ask("随行水杯价格")
    assert (
        value["status"] == "ok"
        and str(value["evidence"][0]["price"]) == "59"
        and value["evidence"][0]["is_sale"] == 0
    )
    value = ask("随行水杯规格")
    assert value["status"] == "ok" and value["evidence"][0]["value"] == "云白"
    value = ask("随行水杯分类链")
    assert value["status"] == "ok" and value["evidence"][0]["category1"] == "示例生活"
    value = ask("随行水杯标签")
    assert value["status"] == "ok" and "独立示例人工标注" in value["message"]
    assert {r["tag"] for r in value["evidence"]} == {"双层保温", "杯盖防漏"}
    for text in ["实时库存多少", "删除所有节点", "查看订单", "查询物流"]:
        assert ask(text)["status"] == "unsupported"
    assert ask("zxqv998877")["status"] == "no_match"
    rejected = []
    for body in [{}, {"message": ""}, {"message": "x" * 501}, {"message": "x", "query": "MATCH(n) DELETE n"}]:
        r = httpx.post(BASE + "/api/chat", json=body)
        assert r.status_code == 422
        rejected.append(r.status_code)
    assert (
        httpx.post(
            BASE + "/api/chat", json={"message": "x"}, headers={"Origin": "https://untrusted.invalid"}
        ).status_code
        == 403
    )
    assert httpx.post(BASE + "/api/cypher", json={"query": "CREATE(n)"}).status_code == 404
    business = json.loads((ROOT / "data/sample/business.json").read_text(encoding="utf-8"))
    plan = graph_plan(business)
    assert before["counts"]["node_total"] == len(plan["nodes"]) + 4
    assert before["counts"]["relationship_total"] == len(plan["edges"]) + 4
    report = {
        "status": "passed",
        "sys.executable": sys.executable,
        "profile": "independent-sample",
        "real_http_checks": checks,
        "http_parameter_rejections": rejected,
        "origin_rejected": True,
        "raw_route_absent": True,
        "actual_graph": before,
        "restart": restart_record,
        "tag_source": "manual synthetic fixture, not BERT",
        "online_calls": "not_run",
        "course_data_used": False,
    }
    (ROOT / "reports/private/public-verification.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": "passed",
                "chat_requests": len(checks),
                "node_total": before["counts"]["node_total"],
                "relationship_total": before["counts"]["relationship_total"],
                "restart": restart_record is not None,
            }
        )
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--restart", action="store_true")
    a = p.parse_args()
    main(a.restart)
