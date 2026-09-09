"""Install the fixed upstream ML SDK into a dedicated environment, then check dependencies."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVISION = "54206e6dcb7f1ca4ebf706f2399eca52612f4d8e"


def main():
    prefix = Path(sys.prefix).name.lower()
    if not any(name in prefix for name in ["ml-backend", "ml-sdk"]):
        raise ValueError("Use a dedicated ml-backend or ml-sdk environment, never the graph environment")
    print(sys.executable, flush=True)
    subprocess.run([sys.executable, "-m", "pip", "install", "-r",
                    str(ROOT / "annotation/ml_backend/requirements.txt")], check=True)
    # Upstream requirements point label-studio-sdk at unpinned Git main.
    # Install every declared dependency explicitly above, then the fixed source without re-resolution.
    subprocess.run([sys.executable, "-m", "pip", "install", "--no-deps",
                    f"https://codeload.github.com/HumanSignal/label-studio-ml-backend/zip/{REVISION}"],
                   check=True)
    # The backend imports shared span validation from this project. Its lightweight
    # base dependencies are needed; retrieval/training extras remain separate.
    subprocess.run([sys.executable, "-m", "pip", "install", "-e", str(ROOT)], check=True)
    subprocess.run([sys.executable, "-m", "pip", "check"], check=True)


if __name__ == "__main__":
    main()
