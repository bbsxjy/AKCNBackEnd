"""
Centralized logging configuration for the application
"""

import logging
import logging.config
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import structlog


class SQLAlchemyFilter(logging.Filter):
    """Filter to reduce noise from SQLAlchemy logs."""
    
    def __init__(self, settings=None):
        """Initialize filter with settings."""
        super().__init__()
        self.settings = settings
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Filter out certain SQLAlchemy log messages."""
        
        # Import settings lazily to avoid circular imports
        if self.settings is None:
            from app.core.config import settings
            self.settings = settings
        
        # Skip if SQL logging is disabled
        if not self.settings.LOG_SQL:
            # Only allow WARNING and above
            if record.levelno < logging.WARNING:
                return False
        
        # Filter out routine pool checkout/checkin messages
        if "Pool" in record.getMessage():
            if any(phrase in record.getMessage() for phrase in [
                "checked out",
                "checked in",
                "being returned",
                "created new connection",
            ]):
                return record.levelno >= logging.WARNING
        
        # Filter out routine transaction messages in non-debug mode
        if not self.settings.DEBUG:
            if any(phrase in record.getMessage() for phrase in [
                "BEGIN (implicit)",
                "COMMIT",
                "ROLLBACK",
            ]):
                return False
        
        return True


class StructlogFormatter(logging.Formatter):
    """Custom formatter that passes through structlog formatted messages."""
    
    def format(self, record):
        # If the message is already formatted by structlog, return it as-is
        if hasattr(record, '_structlog'):
            return record.getMessage()
        # Otherwise, use default formatting
        return super().format(record)


def configure_logging(settings_obj: Optional[Any] = None):
    """Configure logging for the entire application."""
    
    # Import settings lazily to avoid circular imports
    if settings_obj is None:
        from app.core.config import settings
        settings_obj = settings
    
    # Disable SQLAlchemy echo logging if not explicitly enabled
    if not settings_obj.LOG_SQL:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.dialects").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.orm").setLevel(logging.WARNING)
    
    # Configure structlog based on format setting
    if settings_obj.LOG_FORMAT == "json":
        # JSON format - use structlog's native JSON rendering
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso", key="timestamp"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.dict_tracebacks,
                structlog.processors.JSONRenderer(),
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
    else:
        # Console format - human-readable output
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.dev.ConsoleRenderer(colors=True),
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
    
    # Python logging configuration
    logging_config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": "%(asctime)s [%(levelname)s] %(name)s [%(filename)s:%(lineno)d]: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "structlog_plain": {
                "()": StructlogFormatter,
                "format": "%(message)s",
            },
        },
        "filters": {
            "sqlalchemy_filter": {
                "()": SQLAlchemyFilter,
                "settings": settings_obj,
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings_obj.LOG_LEVEL,
                # Use structlog_plain formatter for JSON format to avoid double formatting
                "formatter": "structlog_plain" if settings_obj.LOG_FORMAT == "json" else "default",
                "stream": sys.stdout,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": settings_obj.LOG_LEVEL,
                "formatter": "detailed",
                "filename": "logs/app.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8",
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filename": "logs/error.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8",
            },
        },
        "loggers": {
            "app": {
                "level": settings_obj.LOG_LEVEL,
                "handlers": ["console", "file", "error_file"],
                "propagate": False,
            },
            "uvicorn": {
                "level": settings_obj.LOG_LEVEL,
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn.error": {
                "level": "ERROR",
                "handlers": ["console", "error_file"],
                "propagate": False,
            },
            "sqlalchemy": {
                "level": "WARNING" if not settings_obj.LOG_SQL else "INFO",
                "handlers": ["console"] if settings_obj.LOG_SQL else [],
                "propagate": False,
                "filters": ["sqlalchemy_filter"],
            },
            "sqlalchemy.engine": {
                "level": "WARNING" if not settings_obj.LOG_SQL else "INFO",
                "handlers": ["console"] if settings_obj.LOG_SQL else [],
                "propagate": False,
            },
            "sqlalchemy.pool": {
                "level": "WARNING" if not settings_obj.LOG_SQL else "DEBUG",
                "handlers": ["console"] if settings_obj.LOG_SQL else [],
                "propagate": False,
            },
        },
        "root": {
            "level": settings_obj.LOG_LEVEL,
            "handlers": ["console", "file"],
        },
    }
    
    # Create logs directory if it doesn't exist
    Path("logs").mkdir(exist_ok=True)
    
    # Apply logging configuration
    logging.config.dictConfig(logging_config)