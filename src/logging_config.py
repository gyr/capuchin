"""Logging configuration for package analyzer."""

import logging
import sys
from pathlib import Path

from rich.logging import RichHandler


def setup_logging(
    verbose: bool = False,
    log_file: Path | None = None,
    quiet: bool = False,
) -> None:
    """Configure application logging.

    Uses Python's standard logging module with rich for enhanced console output.

    Args:
        verbose: Enable DEBUG level logging (default: INFO level).
        log_file: Optional file path for log output. File always uses DEBUG level.
        quiet: Suppress console output. File logging still works if log_file provided.
    """
    # Get root logger for the application
    root_logger = logging.getLogger("src")

    # Set level based on verbosity
    level = logging.DEBUG if verbose else logging.INFO
    root_logger.setLevel(level)

    # Remove existing handlers to avoid duplicates on repeated setup
    root_logger.handlers.clear()

    # Console handler (unless quiet mode)
    if not quiet:
        console_handler = RichHandler(
            rich_tracebacks=True,
            show_time=True,
            show_path=verbose,  # Only show file paths in verbose mode
        )
        console_handler.setLevel(level)
        console_formatter = logging.Formatter(
            "%(message)s",
            datefmt="[%X]",
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)  # Always DEBUG level in files
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
