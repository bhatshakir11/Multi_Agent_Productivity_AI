"""Centralized logging configuration for the productivity AI system."""

from __future__ import annotations

import logging
import sys


def setup_logger(name: str = "productivity_ai") -> logging.Logger:
    """Set up and return a configured logger with standard formatting."""
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers if setup is called multiple times
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


# Global logger instance
logger = setup_logger()
