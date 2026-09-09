"""Typed local configuration. Environment > .env > runtime.json > defaults."""

import json
import os
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore", case_sensitive=False, env_ignore_empty=True, hide_input_in_errors=True
    )
    root: Path = Field(default_factory=Path.cwd)
    app_env: Literal["local", "test"] = "local"
    demo_mode: bool = True
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    profile: Literal["safe-demo", "course-reference"] = "safe-demo"
    neo4j_uri: str = "bolt://127.0.0.1:7689"
    neo4j_user: str = "neo4j"
    neo4j_password: SecretStr = SecretStr("")
    neo4j_database: Literal["neo4j"] = "neo4j"
    mysql_host: Literal["127.0.0.1", "localhost"] = "127.0.0.1"
    mysql_port: int = Field(default=3308, ge=1, le=65535)
    mysql_database: str = "ecommerce_demo"
    mysql_user: str = "demo_reader"
    mysql_password: SecretStr = SecretStr("")
    mysql_root_password: SecretStr = SecretStr("")
    mysql_timeout: int = Field(default=5, ge=1, le=30)
    api_port: int = Field(default=8012, ge=1, le=65535)
    online_enabled: bool = False
    deepseek_api_key: SecretStr = SecretStr("")
    ner_model_name: str = "google-bert/bert-base-chinese"
    embedding_model_name: Literal["BAAI/bge-small-zh-v1.5"] = "BAAI/bge-small-zh-v1.5"
    entity_alignment_threshold: float = Field(default=0.85, ge=0, le=1)
    query_max_rows: int = Field(default=20, ge=1, le=20)
    model_dir: Path = Path("artifacts/local/models")
    data_dir: Path = Path("data")

    @classmethod
    def settings_customise_sources(
        cls, settings_cls, init_settings, env_settings, dotenv_settings, file_secret_settings
    ):
        return env_settings, dotenv_settings, init_settings, file_secret_settings

    @field_validator("neo4j_uri")
    @classmethod
    def local_bolt(cls, value):
        parsed = urlparse(value)
        if (
            parsed.scheme != "bolt"
            or parsed.hostname not in {"127.0.0.1", "localhost"}
            or parsed.username
            or parsed.password
            or not parsed.port
            or parsed.path not in {"", "/"}
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("Only local, credential-free Bolt endpoints are accepted")
        return value

    @field_validator("mysql_database", "mysql_user")
    @classmethod
    def identifier(cls, value):
        if not value or len(value) > 64 or not value.replace("_", "").isalnum():
            raise ValueError("Invalid database identifier")
        return value

    @classmethod
    def load(cls, root=None):
        root = Path(root or os.environ.get("ECOMMERCE_ROOT") or Path.cwd()).resolve()
        config_file = root / "artifacts/local/runtime.json"
        runtime = json.loads(config_file.read_text(encoding="utf-8")) if config_file.exists() else {}
        runtime.update(
            root=root,
            profile=os.environ.get("ECOMMERCE_PROFILE", "safe-demo"),
            online_enabled=os.environ.get("ECOMMERCE_ONLINE") == "1",
        )
        options = {**runtime, "_env_file": root / ".env", "_env_file_encoding": "utf-8"}
        result = cls(**options)
        for name in ("model_dir", "data_dir"):
            path = getattr(result, name)
            if not path.is_absolute():
                setattr(result, name, root / path)
        return result

    def secret(self, name: str) -> str:
        """Native bootstrap credentials are ignored local files; environment takes priority."""
        value = getattr(self, name + "_password", None)
        if value and value.get_secret_value():
            return value.get_secret_value()
        path = self.root / "artifacts/local/credentials.json"
        auth = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        return auth.get({"mysql": "mysql_reader"}.get(name, name), "")

    def diagnostics(self):
        return {
            "profile": self.profile,
            "demo_mode": self.demo_mode,
            "api_port": self.api_port,
            "online_enabled": self.online_enabled,
            "deepseek_key_present": bool(self.deepseek_api_key.get_secret_value()),
            "neo4j_configured": bool(self.secret("neo4j")),
            "mysql_configured": bool(self.secret("mysql")),
        }
