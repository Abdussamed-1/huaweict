"""
Centralized logging configuration for cloud deployment.
Supports structured logging and cloud log services.
"""
import logging
import sys
import os
from datetime import datetime

def setup_logging(log_level: str = "INFO", log_format: str = "structured"):
    """
    Setup logging configuration for cloud deployment.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Log format type ("structured" or "simple")
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    if log_format == "structured":
        # Structured logging format (JSON-like for cloud log services)
        log_format_str = (
            '%(asctime)s | %(levelname)-8s | %(name)s | '
            '%(funcName)s:%(lineno)d | %(message)s'
        )
    else:
        # Simple format
        log_format_str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format=log_format_str,
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.StreamHandler(sys.stdout)  # Cloud-friendly: stdout
        ]
    )
    
    # Set specific logger levels
    logging.getLogger("pymilvus").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured: level={log_level}, format={log_format}")
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)
