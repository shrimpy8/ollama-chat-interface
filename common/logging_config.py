"""
Logging Configuration for Ollama Chat Interface

Provides structured logging setup with file and console handlers.
All logs are formatted consistently across the application.

Author: Harsh
"""

import logging
import sys
from typing import Optional


def setup_logging(
    name: str,
    level: str = "INFO",
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    log_file: Optional[str] = None,
    console: bool = True,
    file_logging: bool = True
) -> logging.Logger:
    """
    Configure structured logging for the Ollama chat interface.

    Sets up logging with optional console and file handlers. Prevents duplicate
    handlers when called multiple times for the same logger.

    Args:
        name: Logger name (usually __name__ from calling module)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Format string for log messages
        log_file: Path to log file (if file_logging is True)
        console: Enable console logging to stdout
        file_logging: Enable file logging

    Returns:
        Configured logger instance

    Example:
        >>> logger = setup_logging(__name__, level="INFO", log_file="app.log")
        >>> logger.info("Application started")
        >>> logger.error("An error occurred", exc_info=True)
    """
    # Get or create logger
    logger = logging.getLogger(name)

    # Avoid duplicate handlers if logger already configured
    if logger.handlers:
        return logger

    # Set logging level
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Create formatter
    formatter = logging.Formatter(log_format)

    # Console handler (stdout)
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler
    if file_logging:
        file_path = log_file or "ollama_chat.log"
        try:
            file_handler = logging.FileHandler(file_path)
            file_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except (IOError, OSError) as e:
            # If file logging fails, log to console only
            logger.warning(f"Could not create log file {file_path}: {str(e)}")

    # Prevent propagation to root logger to avoid duplicate logs
    logger.propagate = False

    return logger
