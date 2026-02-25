import logging
import json
from datetime import datetime
from core.config import settings
from core.request_id import get_request_id


# -----------------------------
# JSON LOG FORMATTER
# -----------------------------
class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        # NEVER overwrite reserved logging fields like "module"
        app_module = getattr(record, "app_module", record.name)

        payload = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "app_module": app_module,
            "request_id": getattr(record, "request_id", None),
            "message": record.getMessage(),
        }

        # safely include extra fields
        reserved = {
            "name", "msg", "args", "levelname", "levelno",
            "pathname", "filename", "module", "exc_info",
            "exc_text", "stack_info", "lineno", "funcName",
            "created", "msecs", "relativeCreated", "thread",
            "threadName", "processName", "process"
        }

        for key, value in record.__dict__.items():
            if key in reserved or key in payload:
                continue
            try:
                json.dumps(value)
                payload[key] = value
            except Exception:
                pass

        return json.dumps(payload)


# -----------------------------
# REQUEST ID FILTER
# -----------------------------
class RequestIDFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            record.request_id = get_request_id()
        except Exception:
            record.request_id = None
        return True


# -----------------------------
# PRODUCTION JSON LOGGING
# -----------------------------
def configure_logging() -> None:
    level = (settings.LOG_LEVEL or "INFO").upper()
    numeric_level = getattr(logging, level, logging.INFO)

    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    handler.addFilter(RequestIDFilter())

    root = logging.getLogger()

    # prevent duplicate handlers during reload
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(numeric_level)


# -----------------------------
# EARLY STARTUP LOGGING
# -----------------------------
def setup_logging(level: str = "INFO") -> None:
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )