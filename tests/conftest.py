"""Pytest configuration and shared fixtures."""

import logging

import pytest


@pytest.fixture(autouse=True)
def cleanup_logging() -> None:
    """Clean up logging configuration between tests to ensure test isolation.

    This fixture ensures that logging state modified by setup_logging() in
    main() calls doesn't interfere with caplog fixtures in subsequent tests.

    Cleanup happens AFTER each test completes, resetting both:
    1. Handlers - removes console/file handlers added by setup_logging()
    2. Level - resets logger level to NOTSET so it inherits from root

    This implements defense-in-depth: primary protection is mocking
    setup_logging() in tests, this fixture provides insurance against
    any tests that forget to mock.
    """
    yield
    # Clean up all handlers from the "src" logger
    src_logger = logging.getLogger("src")
    src_logger.handlers.clear()
    # Reset level to NOTSET so it inherits from root logger
    src_logger.setLevel(logging.NOTSET)
