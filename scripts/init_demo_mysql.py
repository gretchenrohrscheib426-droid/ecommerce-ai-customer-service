"""Initialize only a dedicated synthetic schema. Never DROP, truncate or overwrite rows."""

import json
import secrets
from pathlib import Path

from generate_sample import generate

from ecommerce_graph_agent.config import Settings
from ecommerce_graph_agent.datasync.mysql_reader import connect, read_business

ROOT = Path(__file__).resolve().parents[1]


def initialize():
    settings = Settings.load(ROOT)
    if settings.mysql_database not in {"ecommerce_demo", "ecommerce_public_demo"}:
        raise ValueError("Only the dedicated synthetic schema is allowed")
    if settings.mysql_user not in {"demo_reader", "ecommerce_demo_reader"}:
        raise ValueError("Only the dedicated synthetic reader is allowed")
    expected = generate()
    authpath = ROOT / "artifacts/local/credentials.json"
    auth = json.loads(authpath.read_text(encoding="utf-8")) if authpath.exists() else {}
    password = settings.secret("mysql") or secrets.token_urlsafe(32)
    with connect(ROOT, admin=True) as connection, connection.cursor() as cursor:
        db = settings.mysql_database
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db}` CHARACTER SET utf8mb4")
        cursor.execute(
            "SELECT TABLE_NAME AS name FROM information_schema.tables WHERE table_schema=%s", (db,)
        )
        existing = {r["name"] for r in cursor.fetchall()}
        if existing and existing != set(expected):
            raise ValueError("Partial or foreign schema exists; inspect before continuing")
        if not existing:
            for table, rows in expected.items():
                columns = list(rows[0])
                if any(not name.replace("_", "").isalnum() for name in [table, *columns]):
                    raise ValueError("Invalid generator identifier")
                ddl = ", ".join(
                    f"`{name}` "
                    + ("BIGINT" if type(rows[0][name]) is int else "TEXT")
                    + (" PRIMARY KEY" if name == "id" else "")
                    for name in columns
                )
                cursor.execute(f"CREATE TABLE `{db}`.`{table}` ({ddl})")
                columns_sql = ",".join(f"`{name}`" for name in columns)
                placeholders = ",".join(["%s"] * len(columns))
                cursor.executemany(
                    f"INSERT INTO `{db}`.`{table}` ({columns_sql}) VALUES ({placeholders})",
                    [[row[c] for c in columns] for row in rows],
                )
            connection.commit()
        cursor.execute(
            "SELECT COUNT(*) AS n FROM mysql.user WHERE User=%s AND Host=%s",
            (settings.mysql_user, "127.0.0.1"),
        )
        exists = cursor.fetchone()["n"]
        if exists and not settings.secret("mysql"):
            raise ValueError("Existing reader credentials unknown; no account modified")
        if not exists:
            cursor.execute("CREATE USER %s@%s IDENTIFIED BY %s", (settings.mysql_user, "127.0.0.1", password))
        cursor.execute(f"GRANT SELECT ON `{db}`.* TO %s@%s", (settings.mysql_user, "127.0.0.1"))
        connection.commit()
    auth["mysql_reader"] = password
    authpath.parent.mkdir(parents=True, exist_ok=True)
    authpath.write_text(json.dumps(auth), encoding="utf-8")
    actual = read_business(ROOT)
    if actual != expected:
        raise ValueError("Existing database differs from synthetic generator; no data overwritten")
    report = {
        "status": "PASS",
        "dataset": "Synthetic Demo Data",
        "tables": {k: len(v) for k, v in actual.items()},
        "root_used_for_initialization_only": True,
        "runtime_reader": "SELECT only",
    }
    target = ROOT / "reports/private/demo-mysql.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report))
    return report


if __name__ == "__main__":
    initialize()
