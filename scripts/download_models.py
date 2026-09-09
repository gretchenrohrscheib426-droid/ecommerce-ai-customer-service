"""Pinned, safe weights only. Downloads are not trained models."""

import argparse
import hashlib
import json
import shutil
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODELS = [
    ("google-bert/bert-base-chinese", "8f23c25b06e129b6c986331a13d8d025a92cf0ea", "bert-base-chinese"),
    ("BAAI/bge-small-zh-v1.5", "7999e1d3359715c523056ef9478215996d62a620", "bge-small-zh-v1.5"),
]
ALLOWED = {
    "README.md",
    "config.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "vocab.txt",
    "special_tokens_map.json",
    "model.safetensors",
    "modules.json",
    "1_Pooling/config.json",
    "config_sentence_transformers.json",
    "sentence_bert_config.json",
}


def download(repo, revision, directory):
    base = ROOT / "artifacts/local/models" / directory
    with urllib.request.urlopen(
        f"https://huggingface.co/api/models/{repo}/revision/{revision}?blobs=true", timeout=60
    ) as response:
        metadata = json.load(response)
    if metadata["sha"] != revision:
        raise ValueError("Model revision mismatch")
    records = []
    for item in metadata["siblings"]:
        name = item["rfilename"]
        if name not in ALLOWED:
            continue
        target = base / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            url = f"https://huggingface.co/{repo}/resolve/{revision}/{name}?download=true"
            request = urllib.request.Request(url, headers={"User-Agent": "ecommerce-local-course/0.1"})
            with (
                urllib.request.urlopen(request, timeout=120) as response,
                target.with_suffix(target.suffix + ".part").open("wb") as out,
            ):
                shutil.copyfileobj(response, out, 1024 * 1024)
            target.with_suffix(target.suffix + ".part").replace(target)
        blob = target.read_bytes()
        sha = hashlib.sha256(blob).hexdigest()
        if len(blob) != item["size"] or item.get("lfs", {}).get("sha256", sha) != sha:
            raise ValueError(f"Model artifact hash/size mismatch: {repo}/{name}")
        records.append(
            {
                "path": name,
                "bytes": len(blob),
                "sha256": sha,
                "publisher_sha256_verified": bool(item.get("lfs")),
            }
        )
        print(f"verified {repo}/{name}", flush=True)
    record = {
        "repo": repo,
        "revision": revision,
        "license_metadata": metadata.get("cardData", {}).get("license"),
        "files": records,
        "fine_tuned": False,
        "interpreter": sys.executable,
    }
    (base / "download_provenance.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--bge-only", action="store_true")
    args = parser.parse_args()
    (ROOT / "reports/private").mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        records = list(pool.map(lambda args: download(*args), MODELS[1:] if args.bge_only else MODELS))
    (ROOT / "reports/private/model_downloads.json").write_text(
        json.dumps(records, indent=2), encoding="utf-8"
    )
