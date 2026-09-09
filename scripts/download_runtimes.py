"""Download pinned official portable runtimes into this project, without service registration."""

import argparse
import hashlib
import json
import shutil
import sys
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache/downloads"
RUNTIME = ROOT / ".runtime"
SDK_REVISION = "54206e6dcb7f1ca4ebf706f2399eca52612f4d8e"


def read_url(url):
    request = urllib.request.Request(url, headers={"User-Agent": "ecommerce-course-reproduction/0.1"})
    return urllib.request.urlopen(request, timeout=90)


def fetch(name, url, expected=None, algorithm="sha256"):
    CACHE.mkdir(parents=True, exist_ok=True)
    target = CACHE / name
    if shutil.disk_usage(ROOT).free < 12 * 1024**3:
        raise RuntimeError("Less than 12 GiB free; refusing runtime downloads")
    if not target.exists():
        partial = target.with_suffix(target.suffix + ".part")
        with read_url(url) as response, partial.open("wb") as out:
            shutil.copyfileobj(response, out, 1024 * 1024)
        partial.replace(target)
    blob = target.read_bytes()
    observed = hashlib.new(algorithm, blob).hexdigest()
    if expected and expected.strip().split()[0] != observed:
        raise ValueError(f"Hash mismatch: {name}; refusing extraction")
    return target, {
        "name": name,
        "url": url,
        "bytes": len(blob),
        "sha256": hashlib.sha256(blob).hexdigest(),
        "publisher_digest_algorithm": algorithm if expected else None,
        "publisher_digest_verified": bool(expected),
    }


def extract(path, destination):
    with zipfile.ZipFile(path) as archive:
        total, seen = 0, set()
        for member in archive.infolist():
            p = PurePosixPath(member.filename.replace("\\", "/"))
            key = str(p).casefold()
            if p.is_absolute() or ".." in p.parts or ":" in str(p) or "\0" in str(p):
                raise ValueError("Unsafe archive path")
            if key in seen or (member.external_attr >> 16) & 0o170000 == 0o120000 or member.flag_bits & 1:
                raise ValueError("Unsafe archive member")
            seen.add(key)
            total += member.file_size
        if total > 5 * 1024**3 or total > shutil.disk_usage(ROOT).free - 5 * 1024**3:
            raise ValueError("Archive too large")
        for member in archive.infolist():
            target = destination.joinpath(*PurePosixPath(member.filename.replace("\\", "/")).parts)
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            elif not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member) as source, target.open("xb") as out:
                    shutil.copyfileobj(source, out)
            elif target.stat().st_size != member.file_size:
                raise ValueError("Existing extraction differs; refusing overwrite")


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--public", action="store_true")
    mode.add_argument("--mysql-only", action="store_true")
    args = parser.parse_args()
    (ROOT / "reports/private").mkdir(parents=True, exist_ok=True)
    neo_url = "https://dist.neo4j.org/neo4j-community-5.26.30-windows.zip"
    neo_hash = None
    if not args.mysql_only:
        with read_url(neo_url + ".sha256") as response:
            neo_hash = response.read().decode().strip().split()[0]
    jobs = [
        (
            "OpenJDK21U-jdk_x64_windows_hotspot_21.0.12.1_1.zip",
            "https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.12.1%2B1/OpenJDK21U-jdk_x64_windows_hotspot_21.0.12.1_1.zip",
            "f9d6e191ab098c0d416e7d588a24420a8621cd2f4720dab2459b8b7b2d2d8b4e",
            "sha256",
        ),
        ("neo4j-community-5.26.30-windows.zip", neo_url, neo_hash, "sha256"),
        (
            "mysql-8.4.11-winx64.zip",
            "https://cdn.mysql.com/Downloads/MySQL-8.4/mysql-8.4.11-winx64.zip",
            "2e833921898a9a030ea6bfe81bd811bc",
            "md5",
        ),
        (
            f"label-studio-ml-backend-{SDK_REVISION}.zip",
            f"https://codeload.github.com/HumanSignal/label-studio-ml-backend/zip/{SDK_REVISION}",
            None,
            "sha256",
        ),
    ]
    if args.public:
        jobs = jobs[:2]
    elif args.mysql_only:
        jobs = jobs[2:3]
    results = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(fetch, *args) for args in jobs]
        for future in futures:
            path, record = future.result()
            extract(path, RUNTIME)
            results.append(record)
            print(json.dumps(record), flush=True)
    (ROOT / "reports/private/runtime_downloads.json").write_text(
        json.dumps({"interpreter": sys.executable, "files": results, "services_registered": False}, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
