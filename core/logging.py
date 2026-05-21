"""
Structured logging configuration for the second-hand research agent.

Provides JSON-formatted structured logging for all modules.
"""

import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional
import json


class JSONFormatter(logging.Formatter):
    """
    Custom log formatter that outputs JSON.
    
    Each log record is formatted as a JSON object on a single line.
    """
    
    def __init__(self, include_timestamp: bool = True, include_level: bool = True):
        super().__init__()
        self.include_timestamp = include_timestamp
        self.include_level = include_level
    
    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as JSON."""
        log_data: Dict[str, Any] = {
            "message": record.getMessage(),
        }
        
        if self.include_timestamp:
            log_data["timestamp"] = datetime.utcnow().isoformat() + "Z"
        
        if self.include_level:
            log_data["level"] = record.levelname
        
        # Add module name
        if hasattr(record, 'module_name') and record.module_name:
            log_data["module"] = record.module_name
        else:
            # Extract module from pathname
            log_data["module"] = record.module
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in (
                'name', 'msg', 'args', 'created', 'filename', 'funcName',
                'levelname', 'levelno', 'lineno', 'module', 'msecs',
                'message', 'pathname', 'process', 'processName',
                'relativeCreated', 'stack_info', 'exc_info', 'exc_text',
                'thread', 'threadName', 'taskName', 'module_name'
            ):
                try:
                    # Ensure value is JSON serializable
                    if isinstance(value, (dict, list, str, int, float, bool, type(None))):
                        log_data[key] = value
                    else:
                        log_data[key] = str(value)
                except (TypeError, ValueError):
                    log_data[key] = str(value)
        
        # Handle exception info
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
            }
        
        return json.dumps(log_data, default=str)


def setup_logger(
    name: str,
    level: int = logging.INFO,
    json_format: bool = True,
    module_name: Optional[str] = None,
) -> logging.Logger:
    """
    Set up a logger with structured (JSON) or standard formatting.
    
    Args:
        name: Logger name (typically __name__)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: If True, use JSON formatter; otherwise use standard
        module_name: Optional module name to include in logs
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    # Set formatter
    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Set module name for JSON formatter
    if module_name:
        logger.module_name = module_name
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


def get_logger(name: str, module_name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger with JSON formatting for module logging.
    
    This is the main function to use for getting loggers in modules.
    
    Args:
        name: Logger name (typically __name__)
        module_name: Optional module name to include in logs
        
    Returns:
        Configured logger with JSON formatting
    """
    return setup_logger(name, json_format=True, module_name=module_name)


def get_console_logger(name: str = "console") -> logging.Logger:
    """
    Get a logger for console output (non-JSON, human-readable).
    
    Use this for user-facing messages.
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger with standard formatting
    """
    return setup_logger(name, json_format=False)


# Configure root logger to use JSON formatting by default
root_logger = logging.getLogger()
if not root_logger.handlers:
    root_logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root_logger.addHandler(handler)
