"""
Tests for logging configuration module.

Tests logging setup, handlers, formatters, and file/console output.

Author: Harsh
"""

import pytest
import logging
import os
from pathlib import Path
from common.logging_config import setup_logging


@pytest.mark.unit
class TestLoggingSetup:
    """Test logging setup and configuration."""

    def test_setup_logging_basic(self, reset_logging):
        """Test basic logging setup with default parameters."""
        logger_name = f"test_logger_{id(self)}"
        logger = setup_logging(logger_name)

        assert logger is not None
        assert isinstance(logger, logging.Logger)
        assert logger.name == logger_name

    def test_setup_logging_returns_configured_logger(self, reset_logging):
        """Test logging setup returns a properly configured logger."""
        logger_name = f"test_logger_{id(self)}"
        logger = setup_logging(logger_name, level="INFO")

        assert logger.level >= logging.INFO or logger.level == logging.NOTSET


@pytest.mark.unit
class TestLoggingHandlers:
    """Test logging handler configuration."""

    def test_console_handler_enabled_by_default(self, reset_logging):
        """Test that console handler is enabled by default."""
        logger_name = f"test_console_handler_{id(self)}"
        logger = setup_logging(logger_name, console=True)

        # Check that at least one StreamHandler exists
        stream_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
        assert len(stream_handlers) > 0

    def test_file_handler_enabled(self, reset_logging, temp_log_file):
        """Test that file handler is created when enabled."""
        logger_name = f"test_file_handler_{id(self)}"
        logger = setup_logging(
            logger_name,
            log_file=str(temp_log_file),
            file_logging=True,
            console=False
        )

        # Check that FileHandler exists
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) > 0

    def test_file_handler_creates_log_file(self, reset_logging, temp_log_file):
        """Test that file handler actually creates the log file."""
        logger_name = f"test_file_creation_{id(self)}"
        logger = setup_logging(
            logger_name,
            log_file=str(temp_log_file),
            file_logging=True,
            console=False
        )

        # Write a log message
        logger.info("Test message")

        # Flush handlers to ensure write
        for handler in logger.handlers:
            handler.flush()

        # Check that file was created
        assert temp_log_file.exists()


@pytest.mark.unit
class TestLoggingFormat:
    """Test logging format configuration."""

    def test_custom_format_string(self, reset_logging, temp_log_file):
        """Test logging with custom format string."""
        logger_name = f"test_format_{id(self)}"
        custom_format = "%(levelname)s - %(message)s"
        logger = setup_logging(
            logger_name,
            log_format=custom_format,
            log_file=str(temp_log_file),
            file_logging=True,
            console=False
        )

        # Check that handlers have correct formatter
        for handler in logger.handlers:
            assert handler.formatter is not None
            assert handler.formatter._fmt == custom_format

    def test_default_format_includes_timestamp(self, reset_logging):
        """Test that default format includes timestamp."""
        logger_name = f"test_timestamp_{id(self)}"
        logger = setup_logging(logger_name, console=True)

        # Check default format includes asctime
        for handler in logger.handlers:
            if handler.formatter:
                assert '%(asctime)s' in handler.formatter._fmt


@pytest.mark.unit
class TestLoggingBehavior:
    """Test logging behavior and output."""

    def test_logger_propagation_disabled(self, reset_logging):
        """Test that logger propagation is disabled to avoid duplicate logs."""
        logger_name = f"test_propagation_{id(self)}"
        logger = setup_logging(logger_name)

        assert logger.propagate is False

    def test_prevent_duplicate_handlers(self, reset_logging):
        """Test that calling setup_logging multiple times doesn't add duplicate handlers."""
        logger_name = f"test_duplicates_{id(self)}"
        logger1 = setup_logging(logger_name, console=True)
        initial_handler_count = len(logger1.handlers)

        # Call setup_logging again with same logger name
        logger2 = setup_logging(logger_name, console=True)

        # Should return same logger without adding new handlers
        assert logger1 is logger2
        assert len(logger2.handlers) == initial_handler_count

    def test_log_message_written_to_file(self, reset_logging, temp_log_file):
        """Test that log messages are actually written to file."""
        logger_name = f"test_file_write_{id(self)}"
        logger = setup_logging(
            logger_name,
            log_file=str(temp_log_file),
            file_logging=True,
            console=False
        )

        test_message = "This is a test log message"
        logger.info(test_message)

        # Flush handlers to ensure write
        for handler in logger.handlers:
            handler.flush()

        # Read file and check message is present
        with open(temp_log_file, 'r') as f:
            content = f.read()

        assert test_message in content

    def test_different_log_levels(self, reset_logging, temp_log_file):
        """Test that different log levels are written correctly."""
        logger_name = f"test_levels_{id(self)}"
        logger = setup_logging(
            logger_name,
            level="DEBUG",
            log_file=str(temp_log_file),
            file_logging=True,
            console=False
        )

        # Log at different levels
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

        # Flush handlers
        for handler in logger.handlers:
            handler.flush()

        # Read file
        with open(temp_log_file, 'r') as f:
            content = f.read()

        # All levels should be present
        assert "Debug message" in content
        assert "Info message" in content
        assert "Warning message" in content
        assert "Error message" in content


@pytest.mark.unit
class TestLoggingErrorHandling:
    """Test error handling in logging setup."""

    def test_invalid_log_file_path_handles_gracefully(self, reset_logging, caplog):
        """Test that invalid log file path is handled gracefully."""
        logger_name = f"test_invalid_path_{id(self)}"
        invalid_path = "/nonexistent/directory/app.log"

        with caplog.at_level(logging.WARNING):
            logger = setup_logging(
                logger_name,
                log_file=invalid_path,
                file_logging=True,
                console=True  # Fallback to console
            )

        # Should still create logger (with console handler)
        assert logger is not None
        assert len(logger.handlers) > 0

        # Should log warning about failed file creation
        assert any("Could not create log file" in record.message for record in caplog.records)

    def test_invalid_log_level_falls_back_to_info(self, reset_logging):
        """Test that invalid log level falls back to INFO."""
        logger_name = f"test_invalid_level_{id(self)}"
        logger = setup_logging(logger_name, level="INVALID_LEVEL")

        # Should default to INFO level
        assert logger.level == logging.INFO


@pytest.mark.unit
class TestLoggingWithBothHandlers:
    """Test logging with both console and file handlers enabled."""

    def test_both_handlers_work_simultaneously(self, reset_logging, temp_log_file):
        """Test that both console and file logging work together."""
        logger_name = f"test_both_handlers_{id(self)}"
        logger = setup_logging(
            logger_name,
            log_file=str(temp_log_file),
            file_logging=True,
            console=True
        )

        # Should have both handlers
        stream_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)
                          and not isinstance(h, logging.FileHandler)]
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]

        assert len(stream_handlers) > 0
        assert len(file_handlers) > 0

        # Log message
        test_message = "Message to both handlers"
        logger.info(test_message)

        # Flush handlers
        for handler in logger.handlers:
            handler.flush()

        # Check file contains message
        with open(temp_log_file, 'r') as f:
            content = f.read()
        assert test_message in content
