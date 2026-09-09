"""Configure a new owned native MySQL instance without touching an existing database."""

import argparse
import json
import secrets
import subprocess
import time

from services import LOCAL, LOGS, MYSQL, ROOT


def configure(port=3308):
    if type(port) is not int or not 1024 <= port <= 65535:
        raise ValueError("Use an unprivileged TCP port")
    folder = LOCAL / "mysql"
    marker = folder / "owned.json"
    runtime = LOCAL / "runtime.json"
    settings = json.loads(runtime.read_text()) if runtime.exists() else {}
    if "mysql_port" in settings and settings["mysql_port"] != port:
        raise ValueError("Existing MySQL port differs; refusing overwrite")
    if folder.exists() and any(folder.iterdir()) and not marker.exists():
        raise ValueError("Unowned MySQL directory; refusing initialization")
    if marker.exists():
        if json.loads(marker.read_text())["port"] != port:
            raise ValueError("Existing owned port differs")
        print("Owned MySQL configuration already exists")
        return
    if not MYSQL.is_file():
        raise FileNotFoundError("Download the pinned MySQL runtime first")
    folder.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    ini = folder / "my.ini"
    ini.write_text(
        "[mysqld]\n"
        f"basedir={MYSQL.parents[1].as_posix()}\n"
        f"datadir={(folder / 'data').as_posix()}\n"
        f"port={port}\nbind-address=127.0.0.1\nmysqlx=0\n"
        "character-set-server=utf8mb4\n",
        encoding="utf-8",
    )
    with (LOGS / "mysql-initialize.log").open("w", encoding="utf-8") as log:
        subprocess.run(
            [str(MYSQL), f"--defaults-file={ini}", "--initialize-insecure", "--console"],
            cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True,
        )
    settings.update(mysql_port=port, mysql_database="ecommerce_demo", mysql_user="demo_reader")
    runtime.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    marker.write_text(json.dumps({"port": port, "dataset": "independent-sample"}), encoding="utf-8")
    print("New local MySQL data directory initialized; start then secure it immediately")


def secure():
    import pymysql

    from ecommerce_graph_agent.config import Settings

    settings = Settings.load(ROOT)
    marker = LOCAL / "mysql/secured.json"
    if not (LOCAL / "mysql/owned.json").exists():
        raise ValueError("No owned initialization marker")
    authfile = LOCAL / "credentials.json"
    auth = json.loads(authfile.read_text()) if authfile.exists() else {}
    password = auth.get("mysql_root") or secrets.token_urlsafe(32)
    # Save before ALTER so an interrupted run can recover using the generated credential.
    auth["mysql_root"] = password
    authfile.write_text(json.dumps(auth), encoding="utf-8")
    deadline = time.monotonic() + 45
    while True:
        try:
            try:
                connection = pymysql.connect(host="127.0.0.1", port=settings.mysql_port,
                                             user="root", password=password, connect_timeout=2)
            except pymysql.err.OperationalError as exc:
                if exc.args[0] != 1045 or marker.exists():
                    raise
                connection = pymysql.connect(host="127.0.0.1", port=settings.mysql_port,
                                             user="root", password="", connect_timeout=2)
                with connection.cursor() as cursor:
                    cursor.execute("ALTER USER 'root'@'localhost' IDENTIFIED BY %s", (password,))
                connection.commit()
            connection.close()
            break
        except pymysql.err.OperationalError as exc:
            if exc.args[0] not in {2003, 2013} or time.monotonic() >= deadline:
                raise
            time.sleep(0.5)
    marker.write_text('{"secured":true}', encoding="utf-8")
    print("Owned MySQL authentication verified; credentials remain local")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["configure", "secure"])
    parser.add_argument("--port", type=int, default=3308)
    args = parser.parse_args()
    if args.action == "configure":
        configure(args.port)
    else:
        secure()
