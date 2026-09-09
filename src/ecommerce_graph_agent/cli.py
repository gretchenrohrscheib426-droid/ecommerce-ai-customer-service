"""Commands import heavy dependencies only when selected."""

import argparse
import json
import os
import subprocess
import sys

from .config import Settings


def main():
    parser = argparse.ArgumentParser(prog="python -m ecommerce_graph_agent")
    parser.add_argument("--root", help="Explicit project directory")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="Interpreter and redacted configuration")
    for command_name in [
        "audit-data",
        "import-sql",
        "prepare-ner",
        "sync-tables",
        "sync-text",
        "build-indexes",
        "verify",
    ]:
        p = sub.add_parser(command_name)
        if command_name == "prepare-ner":
            p.add_argument("--source", required=True)
    for command_name in ["train-ner", "eval-ner"]:
        p = sub.add_parser(command_name)
        p.add_argument("--run-name")
        if command_name == "train-ner":
            p.add_argument("--run-type", choices=["smoke", "full"], required=True)
    for command_name in ["serve", "stop"]:
        p = sub.add_parser(command_name)
        p.add_argument("service", choices=["api", "mysql", "neo4j", "label-studio", "ml-backend"])
    args = parser.parse_args()
    if args.command == "doctor":
        print(
            json.dumps(
                {
                    "sys.executable": sys.executable,
                    "python": sys.version,
                    **Settings.load(args.root).diagnostics(),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return
    root = Settings.load(args.root).root
    os.environ["ECOMMERCE_ROOT"] = str(root)
    mapping = {
        "audit-data": ["scripts/generate_demo_data.py", "--check"],
        "import-sql": ["scripts/init_demo_mysql.py"],
        "sync-tables": ["scripts/sync_graph.py", "structured"],
        "sync-text": ["scripts/sync_graph.py", "tags"],
        "build-indexes": ["scripts/create_indexes.py"],
        "verify": ["-m", "pytest", "tests/unit", "-q"],
    }
    if args.command == "prepare-ner":
        from .models.ner.process import prepare

        source = root / args.source
        result = prepare(source, root / "data/private/ner-v1")
        print(json.dumps({k: v["count"] for k, v in result["splits"].items()}))
        return
    if args.command in ["train-ner", "eval-ner"]:
        command = [
            "-m",
            "ecommerce_graph_agent.models.ner." + ("train" if args.command == "train-ner" else "evaluate"),
            "--root",
            str(root),
        ]
        if args.command == "train-ner":
            command += ["--run-type", args.run_type]
        if args.run_name:
            command += ["--run-name", args.run_name]
    elif args.command in ["serve", "stop"]:
        command = ["scripts/services.py", "start" if args.command == "serve" else "stop", args.service]
    else:
        command = mapping[args.command]
    raise SystemExit(subprocess.run([sys.executable, *command], cwd=root).returncode)
