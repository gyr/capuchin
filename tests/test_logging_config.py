"""Tests for logging configuration."""

import logging
from pathlib import Path

import pytest

from src.logging_config import setup_logging


class TestSetupLogging:
    """Test logging configuration setup."""

    def test_default_setup_creates_info_logger(self) -> None:
        """Test default setup creates INFO level logger."""
        setup_logging()

        logger = logging.getLogger("src")
        assert logger.level == logging.INFO

    def test_verbose_mode_sets_debug_level(self) -> None:
        """Test verbose mode sets DEBUG level."""
        setup_logging(verbose=True)

        logger = logging.getLogger("src")
        assert logger.level == logging.DEBUG

    def test_quiet_mode_suppresses_console_handler(self) -> None:
        """Test quiet mode suppresses console handler."""
        setup_logging(quiet=True)

        logger = logging.getLogger("src")
        # Should have no handlers when quiet
        assert len(logger.handlers) == 0

    def test_console_handler_uses_rich_handler(self) -> None:
        """Test console handler uses RichHandler."""
        from rich.logging import RichHandler

        setup_logging()

        logger = logging.getLogger("src")
        # Should have one handler (console)
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], RichHandler)

    def test_log_file_creates_file_handler(self, tmp_path: Path) -> None:
        """Test log file creates file handler."""
        log_file = tmp_path / "test.log"

        setup_logging(log_file=log_file)

        logger = logging.getLogger("src")
        # Should have 2 handlers: console + file
        assert len(logger.handlers) == 2

        # Check file handler exists
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) == 1
        # File should be created (even if empty initially)
        assert log_file.exists()

    def test_quiet_with_log_file_only_file_handler(self, tmp_path: Path) -> None:
        """Test quiet mode with log file only creates file handler."""
        log_file = tmp_path / "test.log"

        setup_logging(quiet=True, log_file=log_file)

        logger = logging.getLogger("src")
        # Should have only file handler (no console)
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.FileHandler)

    def test_file_handler_always_debug_level(self, tmp_path: Path) -> None:
        """Test file handler always uses DEBUG level."""
        log_file = tmp_path / "test.log"

        # Even without verbose, file handler should be DEBUG
        setup_logging(verbose=False, log_file=log_file)

        logger = logging.getLogger("src")
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        assert file_handlers[0].level == logging.DEBUG

    def test_handlers_cleared_on_repeated_setup(self) -> None:
        """Test that repeated setup clears previous handlers."""
        setup_logging()
        logger = logging.getLogger("src")
        initial_handler_count = len(logger.handlers)

        # Setup again
        setup_logging()

        # Should not accumulate handlers
        assert len(logger.handlers) == initial_handler_count

    def test_logging_hierarchy_works(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test that child loggers inherit configuration."""
        setup_logging()

        # Get child logger
        child_logger = logging.getLogger("src.analyzer")

        with caplog.at_level(logging.INFO):
            child_logger.info("Test message from child")

        assert "Test message from child" in caplog.text

    def test_verbose_logging_includes_debug_messages(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test verbose mode includes DEBUG messages."""
        setup_logging(verbose=True)

        logger = logging.getLogger("src.test")

        with caplog.at_level(logging.DEBUG):
            logger.debug("Debug message")
            logger.info("Info message")

        assert "Debug message" in caplog.text
        assert "Info message" in caplog.text

    def test_non_verbose_logging_excludes_debug_messages(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test non-verbose mode excludes DEBUG messages."""
        setup_logging(verbose=False)

        logger = logging.getLogger("src.test")

        with caplog.at_level(logging.DEBUG):
            logger.debug("Debug message")
            logger.info("Info message")

        # Debug should not appear at INFO level
        assert "Debug message" not in caplog.text
        assert "Info message" in caplog.text
