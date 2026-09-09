"""DeepSeek adapter. Paid calls require explicit local configuration and bounded budget."""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import httpx

from ..config import Settings
from ..qa.cypher import validate_query
from ..qa.schema import Plan
from .prompts import EVIDENCE_POLICY, PLAN_POLICY


class OnlineBlocked(RuntimeError):
    pass


class DeepSeek:
    def __init__(self, root):
        self.root = Path(root)

    def settings(self):
        path = self.root / "artifacts/local/online_authorization.json"
        if not path.exists():
            raise OnlineBlocked("Online call not authorized/configured")
        value = json.loads(path.read_text(encoding="utf-8"))
        if (
            not value.get("chat_enabled")
            or not value.get("model")
            or not Settings.load(self.root).deepseek_api_key.get_secret_value()
        ):
            raise OnlineBlocked("Online call not authorized/configured")
        return value

    def call(self, messages, json_mode=False):
        settings = self.settings()
        with sqlite3.connect(self.root / "artifacts/local/chat-budget.sqlite3", timeout=5) as db:
            db.execute("CREATE TABLE IF NOT EXISTS calls(id INTEGER PRIMARY KEY,created TEXT)")
            db.execute("BEGIN IMMEDIATE")
            if db.execute("SELECT COUNT(*) FROM calls").fetchone()[0] >= int(
                settings.get("max_chat_calls", 0)
            ):
                raise OnlineBlocked("Online call budget exhausted")
            db.execute("INSERT INTO calls(created) VALUES (?)", (datetime.now(timezone.utc).isoformat(),))
        body = {"model": settings["model"], "messages": messages, "temperature": 0, "max_tokens": 1000}
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        try:
            with httpx.Client(timeout=httpx.Timeout(10, connect=5), follow_redirects=False) as client:
                response = client.post(
                    "https://api.deepseek.com/chat/completions",
                    json=body,
                    headers={
                        "Authorization": "Bearer "
                        + Settings.load(self.root).deepseek_api_key.get_secret_value()
                    },
                )
        except httpx.RequestError as error:
            raise OnlineBlocked("Online model network/timeout failure") from error
        if response.status_code != 200:
            raise OnlineBlocked(f"Online model HTTP {response.status_code}; body redacted")
        try:
            return response.json()["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as error:
            raise OnlineBlocked("Invalid provider response") from error

    def plan(self, message):
        schema = Plan.model_json_schema()
        text = self.call(
            [
                {"role": "system", "content": PLAN_POLICY + json.dumps(schema, ensure_ascii=False)},
                {"role": "user", "content": message},
            ],
            json_mode=True,
        )
        return Plan.model_validate_json(text)

    def course_query(self, message, templates):
        text = self.call(
            [
                {
                    "role": "system",
                    "content": "仅返回 JSON {query,parameters}，query 必须逐字选择下列模板，parameters 仅 entity_id 正整数和limit 1到20。未知实体返回错误，不猜id。"
                    + json.dumps(templates, ensure_ascii=False),
                },
                {"role": "user", "content": message},
            ],
            json_mode=True,
        )
        value = json.loads(text)
        if set(value) != {"query", "parameters"}:
            raise ValueError("Invalid course query fields")
        return validate_query(value["query"], value["parameters"])

    def answer(self, message, rows, dataset):
        settings = self.settings()
        if settings.get("allowed_dataset") != dataset:
            raise OnlineBlocked("Result egress dataset is not authorized")
        # Model returns evidence row IDs only. Product facts are rendered from actual rows by code.
        value = json.loads(
            self.call(
                [
                    {"role": "system", "content": EVIDENCE_POLICY},
                    {
                        "role": "user",
                        "content": json.dumps({"question": message, "rows": rows}, ensure_ascii=False),
                    },
                ],
                json_mode=True,
            )
        )
        indices = value.get("row_indices")
        if (
            set(value) != {"row_indices"}
            or not isinstance(indices, list)
            or len(set(indices)) != len(indices)
            or any(type(i) is not int or not 0 <= i < len(rows) for i in indices)
        ):
            raise ValueError("Invalid answer evidence selection")
        if rows and not indices:
            raise ValueError("Model discarded all actual evidence")
        return [rows[i] for i in indices]
