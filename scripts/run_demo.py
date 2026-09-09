"""Start/stop existing native demo services. Building is an explicit separate action."""

import argparse
import json

from services import start, stop

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["start", "stop"])
    a = p.parse_args()
    names = ["neo4j", "api"] if a.action == "start" else ["api", "neo4j"]
    for name in names:
        print(json.dumps((start if a.action == "start" else stop)(name)))
