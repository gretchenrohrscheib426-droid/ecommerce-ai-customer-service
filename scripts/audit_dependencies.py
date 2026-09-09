"""Audit every installed third-party distribution, including the CPU torch base version."""

import importlib.metadata as metadata
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def requirements():
    packages = {}
    for dist in metadata.distributions():
        name = dist.metadata["Name"].lower().replace("_", "-")
        if name == "ecommerce-knowledge-graph-agent":
            continue  # This repository is source-audited, not a third-party PyPI package.
        version = dist.version
        if name == "torch" and version.endswith("+cpu"):
            version = version.removesuffix("+cpu")
        packages[name] = version
    return [f"{name}=={version}" for name, version in sorted(packages.items())]


def main():
    output = ROOT / "reports/private"
    output.mkdir(parents=True, exist_ok=True)
    target = output / "installed-audit-requirements.txt"
    target.write_text("\n".join(requirements()) + "\n", encoding="utf-8")
    lock = ROOT / "envs/locks/public/security-requirements.txt"
    if lock.exists():
        locked = [line.strip() for line in lock.read_text().splitlines()
                  if line.strip() and not line.startswith("#")]
        if locked != requirements():
            raise ValueError("Installed distribution set differs from public security lock; regenerate after review")
    result = subprocess.run(
        [sys.executable, "-m", "pip_audit", "--disable-pip", "--no-deps", "-r", str(target),
         "--format", "json", "--output", str(output / "dependency-audit-final.json")], cwd=ROOT,
    )
    data = json.loads((output / "dependency-audit-final.json").read_text(encoding="utf-8"))
    skipped = [d["name"] for d in data["dependencies"] if d.get("skip_reason")]
    print(json.dumps({"third_party_packages": len(requirements()), "skipped": skipped,
                      "torch_cpu_mapping": "The CPU build is audited as its upstream torch release",
                      "first_party_scope": "source boundary checks and regression tests"}))
    return result.returncode or int(bool(skipped))


if __name__ == "__main__":
    raise SystemExit(main())
