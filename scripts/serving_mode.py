"""Switch only the owned instance. Real write rejection is required before serving."""

import argparse
import json
import time
from pathlib import Path

from services import start, stop

from ecommerce_graph_agent.db.neo4j import driver

ROOT = Path(__file__).resolve().parents[1]


def switch(mode):
    if mode not in {"build", "serve"}:
        raise ValueError("Unknown mode")
    config = ROOT / "artifacts/local/neo4j/conf/neo4j.conf"
    content = config.read_text(encoding="utf-8")
    setting = "server.databases.default_to_read_only="
    lines = content.splitlines()
    if sum(line.startswith(setting) for line in lines) != 1:
        raise ValueError("Expected exactly one read-only setting")
    stop("api")
    stop_result = stop("neo4j")
    lines = [
        setting + ("true" if mode == "serve" else "false") if line.startswith(setting) else line
        for line in lines
    ]
    config.write_text("\n".join(lines) + "\n", encoding="utf-8")
    start("neo4j")
    last = None
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        try:
            with driver(ROOT) as d:
                with d.session(database="system") as s:
                    status = s.run(
                        "SHOW DATABASES YIELD name,currentStatus WHERE name='neo4j' RETURN currentStatus"
                    ).single()["currentStatus"]
                if status == "offline":
                    raise RuntimeError("Database offline; inspect local Neo4j debug log")
                with d.session(database="neo4j") as s:
                    s.run("RETURN 1").consume()
            break
        except RuntimeError:
            raise
        except Exception as error:
            last = error
            time.sleep(1)
    else:
        raise RuntimeError("Owned Neo4j restart failed") from last
    report = {
        "mode": mode,
        "status": "passed",
        "shutdown": stop_result,
        "database_scope": "neo4j only; system database is NOT protected by this mode",
        "raw_cypher_enabled": False,
    }
    with driver(ROOT) as d:
        with d.session(database="system") as s:
            report["access"] = s.run(
                "SHOW DATABASES YIELD name,access WHERE name='neo4j' RETURN access"
            ).single()["access"]
        if mode == "serve":
            from neo4j.exceptions import ClientError

            with d.session(database="neo4j") as s:
                transaction = s.begin_transaction()
                try:
                    transaction.run("CREATE (:ServingWriteProbe {id:1})").consume()
                except ClientError as error:
                    report["write_attempt"] = "denied"
                    report["error_code"] = error.code
                    if error.code != "Neo.ClientError.General.WriteOnReadOnlyAccessDatabase":
                        raise
                else:
                    raise AssertionError("Write unexpectedly allowed; query service must remain stopped")
                finally:
                    transaction.rollback()
                assert s.run("MATCH (n:ServingWriteProbe) RETURN count(n) AS count").single()["count"] == 0
            if report["access"] != "read-only":
                raise AssertionError("Database is not read-only")
    (ROOT / "reports/private/serving-mode.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return report


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=["build", "serve"])
    a = p.parse_args()
    print(json.dumps(switch(a.mode), ensure_ascii=False))
