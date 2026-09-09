"""Own only recorded processes with matching creation time and executable.

No service registration, no global process kills, no database re-import on startup.
"""

import argparse
import json
import os
import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / "artifacts/local"
LOGS = ROOT / "reports/private"
REGISTRY = LOCAL / "processes.json"
JAVA = ROOT / ".runtime/jdk-21.0.12.1+1/bin/java.exe"
NEO = ROOT / ".runtime/neo4j-community-5.26.30"
MYSQL = ROOT / ".runtime/mysql-8.4.11-winx64/bin/mysqld.exe"


def read_registry():
    return json.loads(REGISTRY.read_text(encoding="utf-8")) if REGISTRY.exists() else {}


def write_registry(data):
    LOCAL.mkdir(parents=True, exist_ok=True)
    temp = REGISTRY.with_suffix(".tmp")
    temp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    temp.replace(REGISTRY)


def checked_process(record):
    import psutil

    try:
        p = psutil.Process(record["pid"])
        if (
            abs(p.create_time() - record["created"]) > 0.01
            or Path(p.exe()).resolve() != Path(record["exe"]).resolve()
        ):
            raise RuntimeError("PID ownership mismatch; refusing process operation")
        if p.cmdline() != record["command"]:
            raise RuntimeError("Command ownership mismatch; refusing process operation")
        return p
    except psutil.NoSuchProcess:
        return None


def specs(name):
    from urllib.parse import urlparse

    from ecommerce_graph_agent.config import Settings

    settings = Settings.load(ROOT)
    python = Path(sys.executable)
    if name == "mysql":
        return [str(MYSQL), f"--defaults-file={LOCAL / 'mysql/my.ini'}", "--console"], [settings.mysql_port]
    if name == "neo4j":
        classpath = (
            str(ROOT / ".runtime/launcher")
            + ";"
            + ";".join(str(NEO / folder / "*") for folder in ["plugins", "conf", "lib"])
        )
        return [
            str(JAVA),
            "-Xms256m",
            "-Xmx1024m",
            "-cp",
            classpath,
            "-XX:+UseG1GC",
            "-XX:-OmitStackTraceInFastThrow",
            "-XX:+UnlockExperimentalVMOptions",
            "-XX:+TrustFinalNonStaticFields",
            "-XX:+DisableExplicitGC",
            "-Djdk.nio.maxCachedBufferSize=1024",
            "-Dio.netty.tryReflectionSetAccessible=true",
            "--add-opens=java.base/java.nio=ALL-UNNAMED",
            "--add-opens=java.base/java.io=ALL-UNNAMED",
            "--add-opens=java.base/sun.nio.ch=ALL-UNNAMED",
            "--enable-native-access=ALL-UNNAMED",
            "-Dlog4j2.disable.jmx=true",
            "-Dfile.encoding=UTF-8",
            "LocalNeo4j",
            f"--home-dir={NEO}",
            f"--config-dir={LOCAL / 'neo4j/conf'}",
            "--console-mode",
        ], [
            int(json.loads((LOCAL / "runtime.json").read_text()).get("neo4j_http_port", 7475))
            if (LOCAL / "runtime.json").exists()
            else 7475,
            urlparse(settings.neo4j_uri).port,
        ]
    if name == "api":
        return [
            str(python),
            "-m",
            "uvicorn",
            "ecommerce_graph_agent.web.app:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(settings.api_port),
        ], [settings.api_port]
    if name == "label-studio":
        return [
            str(ROOT / ".conda/label-studio/python.exe"),
            "-m",
            "label_studio.server",
            "start",
            "--host",
            "http://127.0.0.1:8082",
            "--internal-host",
            "127.0.0.1",
            "--port",
            "8082",
            "--no-browser",
        ], [8082]
    if name == "ml-backend":
        return [str(ROOT / ".conda/ml-backend/python.exe"), str(ROOT / "annotation/ml_backend/_wsgi.py")], [
            9092
        ]
    raise ValueError("Unknown service")


def start(name):
    import psutil

    registry = read_registry()
    if name in registry and checked_process(registry[name]):
        return {"service": name, "status": "already-running", "pid": registry[name]["pid"]}
    command, ports = specs(name)
    if name == "neo4j":
        source = ROOT / "scripts/java/LocalNeo4j.java"
        target = ROOT / ".runtime/launcher/LocalNeo4j.class"
        if not target.exists() or target.stat().st_mtime < source.stat().st_mtime:
            target.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                [
                    str(JAVA.parent / "javac.exe"),
                    "-encoding",
                    "UTF-8",
                    "-proc:none",
                    "-cp",
                    str(NEO / "lib/*"),
                    "-d",
                    str(target.parent),
                    str(source),
                ],
                check=True,
                cwd=ROOT,
            )
    # Windows exclusive bind checks local and all-interface conflicts; never kill the occupant.
    for port in ports:
        with socket.socket() as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            s.bind(("127.0.0.1", port))
    env = dict(
        os.environ,
        PYTHONUTF8="1",
        ECOMMERCE_ROOT=str(ROOT),
        HF_HUB_OFFLINE="1",
        TRANSFORMERS_OFFLINE="1",
        HF_HUB_DISABLE_TELEMETRY="1",
        LABEL_STUDIO_DISABLE_SIGNUP_WITHOUT_LINK="true",
        LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED="false",
        LABEL_STUDIO_BASE_DATA_DIR=str(LOCAL / "label-studio"),
        COLLECT_ANALYTICS="false",
        LOG_LEVEL="WARNING",
        DJANGO_DEBUG="false",
        MODEL_DIR=str(LOCAL / "ml-backend"),
        ML_MODE="blocked",
        CACHE_TYPE="sqlite",
    )
    if name == "neo4j":
        marker = LOCAL / "neo4j/stop.request"
        if marker.exists():
            marker.unlink()  # Only an owned stale stop marker, never database files.
        env["ECOMMERCE_NEO4J_STOP_FILE"] = str(marker)
    prefix = Path(command[0]).parent
    env["PATH"] = str(prefix / "Library/bin") + os.pathsep + str(prefix) + os.pathsep + env["PATH"]
    for p in [LOCAL / "label-studio", LOCAL / "ml-backend", LOGS]:
        p.mkdir(parents=True, exist_ok=True)
    if name == "label-studio":
        auth = json.loads((LOCAL / "credentials.json").read_text(encoding="utf-8"))
        env["LABEL_STUDIO_USERNAME"] = "learner@example.invalid"
        env["LABEL_STUDIO_PASSWORD"] = auth["label_studio_password"]
        env["LABEL_STUDIO_COLLECT_ANALYTICS"] = "false"
        env["LABEL_STUDIO_SENTRY_DSN"] = ""
    with (
        (LOGS / f"{name}.stdout.log").open("ab") as stdout,
        (LOGS / f"{name}.stderr.log").open("ab") as stderr,
    ):
        process = subprocess.Popen(
            command,
            cwd=ROOT,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=stdout,
            stderr=stderr,
            creationflags=subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP,
        )
    p = psutil.Process(process.pid)
    registry[name] = {
        "pid": process.pid,
        "created": p.create_time(),
        "exe": p.exe(),
        "command": p.cmdline(),
        "ports": ports,
    }
    write_registry(registry)
    return {"service": name, "status": "started-not-yet-ready", "pid": process.pid, "ports": ports}


def stop(name):
    registry = read_registry()
    if name not in registry:
        return {"service": name, "status": "not-recorded"}
    record = registry[name]
    p = checked_process(record)
    if p:
        if name == "mysql":
            import pymysql

            from ecommerce_graph_agent.config import Settings

            settings = Settings.load(ROOT)
            with pymysql.connect(
                host="127.0.0.1", port=settings.mysql_port, user="root",
                password=settings.secret("mysql_root"), connect_timeout=5
            ) as c:
                c.cursor().execute("SHUTDOWN")
        elif name == "neo4j":
            if "LocalNeo4j" in record["command"]:
                (LOCAL / "neo4j/stop.request").write_text("shutdown", encoding="ascii")
            else:
                # One-time migration of the old owned launcher, recorded as abrupt close.
                p.terminate()
        else:
            p.terminate()
        p.wait(timeout=30)
    del registry[name]
    write_registry(registry)
    shutdown = (
        "sql-shutdown"
        if name == "mysql"
        else (
            "neo4j-bootstrapper-stop"
            if name == "neo4j" and "LocalNeo4j" in record.get("command", [])
            else "process-termination"
        )
    )
    return {"service": name, "status": "stopped", "shutdown": shutdown}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["start", "stop", "status"])
    parser.add_argument("name", choices=["mysql", "neo4j", "api", "label-studio", "ml-backend"])
    args = parser.parse_args()
    if args.action == "status":
        record = read_registry().get(args.name)
        result = {"service": args.name, "running": bool(record and checked_process(record))}
    else:
        result = (start if args.action == "start" else stop)(args.name)
    print(json.dumps(result))
