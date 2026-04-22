"""Structured logging configuration using structlog."""

import logging
import sys
from datetime import datetime
from typing import Any, Dict

import structlog
import orjson
from structlog import contextvars
from structlog.stdlib import BoundLogger, LoggerFactory


def add_timestamp(_, __, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add current datetime to log event."""
    event_dict["timestamp"] = datetime.now().isoformat()
    return event_dict


def get_logger(name: str = None, **kwargs) -> BoundLogger:
    """Create structlog logger for logging.
    
    Args:
        name: Optional logger name
        **kwargs: Additional context to bind
        
    Returns:
        Configured BoundLogger instance
    """
    if not logging.getLogger().handlers:
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=logging.INFO,
            force=True,
        )

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso", key="timestamp"),
            contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(
                serializer=lambda obj, **kw: orjson.dumps(
                    obj,
                    option=orjson.OPT_NON_STR_KEYS | orjson.OPT_SERIALIZE_NUMPY,
                    default=str
                ).decode()
            )
        ],
        logger_factory=LoggerFactory(),
        cache_logger_on_first_use=True,
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    )
    
    bound_logger = structlog.get_logger(**kwargs)
    if name:
        bound_logger = bound_logger.bind(logger_name=name)
    return bound_logger


# Global logger instance
logger = get_logger()

