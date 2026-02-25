import logging
from core.config import settings
import json
from datetime import datetime
from core.request_id import get_request_id


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "module": record.name,
            "request_id": getattr(record, "request_id", None),
            "message": record.getMessage(),
        }
        # include any extra keys that are JSON-serializable
        extras = {k: v for k, v in record.__dict__.items() if k not in ("name", "msg", "args", "levelname", "levelno", "pathname", "filename", "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName", "created", "msecs", "relativeCreated", "thread", "threadName", "processName", "process")}
        for k, v in extras.items():
            try:
                json.dumps({k: v})
                payload[k] = v
            except Exception:
                # skip non-serializable extras
                pass
        return json.dumps(payload)


def configure_logging() -> None:
    """Configure root logger to produce JSON-structured logs.

    Controlled by `LOG_LEVEL` environment variable. Default: INFO.
    """
    level = (settings.LOG_LEVEL or "INFO").upper()
    numeric_level = getattr(logging, level, logging.INFO)

    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    # add a filter that injects the request_id from contextvar into records
    class RequestIDFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:  # type: ignore[override]
            try:
                rid = get_request_id()
            except Exception:
                rid = None
            record.request_id = rid
            return True

    handler.addFilter(RequestIDFilter())

    root = logging.getLogger()
    # avoid adding multiple handlers during reloads
    if not root.handlers:
        root.addHandler(handler)
    root.setLevel(numeric_level)


def setup_logging(level: str = "INFO") -> None:
    """Simple logging setup for early app startup (non-JSON)."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
