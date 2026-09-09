"""Read-only diagnostics; no software installation, secrets or broad disk scan."""

import importlib.metadata
import json
import platform
import shutil
import socket
import sys
from pathlib import Path

from ecommerce_graph_agent.config import Settings


def check():
    settings = Settings.load(Path(__file__).resolve().parents[1])
    versions = {}
    for package in [
        "fastapi",
        "pydantic-settings",
        "neo4j",
        "PyMySQL",
        "torch",
        "transformers",
        "pytest",
        "ruff",
    ]:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    ports = {}
    for port in [3306, 7474, 7687, 8000, settings.mysql_port, 7689, settings.api_port]:
        with socket.socket() as sock:
            sock.settimeout(0.2)
            ports[str(port)] = (
                "listening (not a health assertion)"
                if sock.connect_ex(("127.0.0.1", port)) == 0
                else "closed"
            )
    return {
        "sys.executable": sys.executable,
        "python": platform.python_version(),
        "os": platform.platform(),
        "free_bytes": shutil.disk_usage(settings.root).free,
        "conda_on_path": bool(shutil.which("conda")),
        "java_on_path": bool(shutil.which("java")),
        "docker_cli_found": bool(shutil.which("docker")),
        "git_found": bool(shutil.which("git")),
        "bundled_java_exists": (settings.root / ".runtime/jdk-21.0.12.1+1/bin/java.exe").is_file(),
        "path_detection_scope": "PATH only; false is not proof software is absent",
        "packages": versions,
        "ports": ports,
        **settings.diagnostics(),
    }


if __name__ == "__main__":
    print(json.dumps(check(), indent=2))
