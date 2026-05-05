"""Tests for configuration module."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from src.config import Config


class TestConfig:
    """Tests for Config class."""

    def test_get_default_package_monkey_path(self) -> None:
        """Test getting default PACKAGE_MONKEY_PATH."""
        # Clear environment variable if set
        with patch.dict(os.environ, {}, clear=True):
            # Mock path existence check
            with patch("pathlib.Path.is_dir", return_value=True):
                path = Config.get_package_monkey_path()
                assert isinstance(path, Path)
                assert str(path) == Config.DEFAULT_PACKAGE_MONKEY_PATH

    def test_get_package_monkey_path_from_env(self) -> None:
        """Test getting PACKAGE_MONKEY_PATH from environment variable."""
        custom_path = "/custom/path/to/package_monkey"
        with patch.dict(os.environ, {"PACKAGE_MONKEY_PATH": custom_path}):
            with patch("pathlib.Path.is_dir", return_value=True):
                path = Config.get_package_monkey_path()
                assert str(path) == custom_path

    def test_env_var_takes_precedence_over_default(self) -> None:
        """Test that environment variable takes precedence over default."""
        custom_path = "/env/override/path"
        with patch.dict(os.environ, {"PACKAGE_MONKEY_PATH": custom_path}):
            with patch("pathlib.Path.is_dir", return_value=True):
                path = Config.get_package_monkey_path()
                assert str(path) == custom_path
                assert str(path) != Config.DEFAULT_PACKAGE_MONKEY_PATH

    def test_raises_error_if_path_does_not_exist(self) -> None:
        """Test that ValueError is raised if path doesn't exist."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("pathlib.Path.is_dir", return_value=False):
                with pytest.raises(ValueError, match="PACKAGE_MONKEY_PATH does not exist"):
                    Config.get_package_monkey_path()

    def test_raises_error_if_custom_path_does_not_exist(self) -> None:
        """Test that ValueError is raised for non-existent custom path."""
        custom_path = "/nonexistent/path"
        with patch.dict(os.environ, {"PACKAGE_MONKEY_PATH": custom_path}):
            with patch("pathlib.Path.is_dir", return_value=False):
                with pytest.raises(
                    ValueError, match=f"PACKAGE_MONKEY_PATH does not exist: {custom_path}"
                ):
                    Config.get_package_monkey_path()
