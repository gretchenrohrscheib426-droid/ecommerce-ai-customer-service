"""JSON event logs contain only whitelisted operational fields."""

import json
import logging
from datetime import datetime, timezone


class EventFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": record.levelname,
                "module": record.name,
                "trace_id": getattr(record, "trace_id", None),
                "event": record.getMessage(),
            },
            ensure_ascii=False,
        )


def configure_logging(level="INFO"):
    logger = logging.getLogger("ecommerce_graph_agent")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(EventFormatter())
        logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False


def event(module, trace_id, status, **counts):
    safe = {k: v for k, v in counts.items() if k in {"input_length", "evidence_rows"} and type(v) is int}
    logging.getLogger(module).info(json.dumps({"status": status, **safe}), extra={"trace_id": trace_id})
