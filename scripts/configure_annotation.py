"""Initialize local annotation login interactively; never print passwords."""

import getpass
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    target = ROOT / "artifacts/local/credentials.json"
    auth = json.loads(target.read_text(encoding="utf-8")) if target.exists() else {}
    if "label_studio_password" in auth:
        print("Existing local annotation credential preserved")
        return
    password = getpass.getpass("Choose local Label Studio password (at least 12 characters): ")
    if len(password) < 12 or password != getpass.getpass("Confirm password: "):
        raise ValueError("Password length or confirmation failed")
    auth["label_studio_password"] = password
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(auth), encoding="utf-8")
    print("Local login configured for learner@example.invalid; password omitted")


if __name__ == "__main__":
    main()
