import logging
import logging.config
import sys
from pathlib import Path
from typing import Any, Dict

from app.core.settings import settings


def get_logging_config() -> Dict[str, Any]:
    """Builds a ``dictConfig``-compatible logging configuration.

    Ensures the ``logs`` directory exists and wires console, rotating app log,
    and error log handlers.

    Returns:
        dict: Configuration accepted by ``logging.config.dictConfig``.

    """
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime)s %(name)s %(levelname)s %(funcName)s %(lineno)d %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO" if not settings.logging_settings.DEBUG else "DEBUG",
                "formatter": "default",
                "stream": sys.stdout,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": settings.logging_settings.LOG_LEVEL,
                "formatter": "detailed",
                "filename": settings.logging_settings.LOG_FILE_PATH,
                "maxBytes": settings.logging_settings.LOG_MAX_BYTES,
                "backupCount": settings.logging_settings.LOG_BACKUP_COUNT,
                "encoding": "utf-8",
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filename": "logs/error.log",
                "maxBytes": settings.logging_settings.LOG_MAX_BYTES,
                "backupCount": settings.logging_settings.LOG_BACKUP_COUNT,
                "encoding": "utf-8",
            },
        },
        "loggers": {
            "app": {
                "level": "DEBUG" if settings.logging_settings.DEBUG else "INFO",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "uvicorn.error": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "level": "INFO" if settings.logging_settings.DEBUG else "WARNING",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "alembic": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False,
            },
        },
        "root": {
            "level": "INFO",
            "handlers": ["console", "file", "error_file"],
        },
    }

    return config


def setup_logging() -> logging.Logger:
    """Applies dict logging config and returns the ``app`` logger.

    Returns:
        logging.Logger: Logger named ``app``.

    """
    config = get_logging_config()
    logging.config.dictConfig(config)

    logger = logging.getLogger("app")

    logger.info("Logging system initialized")
    return logger


def get_logger(name: str = "app") -> logging.Logger:
    """Returns a logger by name (child of configured hierarchy).

    Args:
        name: Logger name, default ``app``.

    Returns:
        logging.Logger: Named logger instance.

    """
    return logging.getLogger(name)
