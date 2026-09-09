"""Independent, bounded dependency probes; configuration is not connectivity."""

from pathlib import Path

from .config import Settings


def status(root, service=None):
    settings = Settings.load(root)
    report = {
        "app": "ok",
        "mysql": "not_configured",
        "neo4j": "unavailable",
        "llm": "not_enabled",
        "ner_model": "not_present",
        "embedding": "unavailable",
        "demo_mode": settings.demo_mode,
        "dataset": getattr(service, "dataset", "unknown"),
        "generation": "Demo fallback: local graph templates",
        "raw_cypher": False,
    }
    if settings.secret("mysql"):
        try:
            from .datasync.mysql_reader import connect

            with connect(root) as connection, connection.cursor() as cursor:
                cursor.execute("SELECT 1 AS alive")
                report["mysql"] = "ok" if cursor.fetchone()["alive"] == 1 else "unavailable"
        except (RuntimeError, ValueError):
            report["mysql"] = "unavailable"
    instance = getattr(service, "driver", None)
    if instance is not None:
        try:
            with instance.session(database="neo4j") as session:
                session.run("RETURN 1").consume()
            report["neo4j"] = "ok"
        except Exception:
            report["neo4j"] = "unavailable"
    if getattr(service, "retriever", None) is not None:
        report["embedding"] = "loaded"
    model = Path(root) / "artifacts/local/ner-full/best_model"
    required = ["model.safetensors", "training_provenance.json", "config.json", "tokenizer_config.json"]
    if all((model / name).is_file() for name in required):
        report["ner_model"] = "bundle_present_not_probed"
    if settings.online_enabled:
        report["generation"] = "DeepSeek requested; connectivity not probed"
        try:
            from .llm.deepseek_client import DeepSeek

            DeepSeek(root).settings()
            report["llm"] = "configured_not_probed"
        except (RuntimeError, ValueError):
            report["llm"] = "unavailable"
    return report
