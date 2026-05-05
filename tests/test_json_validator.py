"""Tests for JSON validator module."""

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.json_validator import JsonValidator, ValidationError


class TestJsonValidator:
    """Test suite for JsonValidator."""

    @pytest.fixture
    def validator(self, tmp_path: Path) -> JsonValidator:
        """Create a JsonValidator instance with a temporary directory."""
        return JsonValidator(script_path=tmp_path / "validate_json.sh")

    @pytest.fixture
    def mock_script(self, tmp_path: Path) -> Path:
        """Create a mock validation script."""
        script_path = tmp_path / "validate_json.sh"
        script_path.write_text("#!/bin/bash\nexit 0")
        script_path.chmod(0o755)
        return script_path

    def test_init_default_script_path(self) -> None:
        """Test initialization with default script path."""
        validator = JsonValidator()
        assert validator.script_path == Path("validate_json.sh")

    def test_init_custom_script_path(self) -> None:
        """Test initialization with custom script path."""
        custom_path = Path("/custom/path/validate.sh")
        validator = JsonValidator(script_path=custom_path)
        assert validator.script_path == custom_path

    def test_validate_success(self, tmp_path: Path, mock_script: Path) -> None:
        """Test successful validation."""
        validator = JsonValidator(script_path=mock_script)
        json_file = tmp_path / "test.json"
        json_file.write_text('{"key": "value"}')

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            validator.validate(json_file)
            mock_run.assert_called_once_with(
                [str(mock_script), str(json_file)],
                capture_output=True,
                text=True,
                check=False,
            )

    def test_validate_script_not_found(self, tmp_path: Path) -> None:
        """Test validation when script doesn't exist."""
        validator = JsonValidator(script_path=tmp_path / "nonexistent.sh")
        json_file = tmp_path / "test.json"
        json_file.write_text('{"key": "value"}')

        with pytest.raises(ValidationError, match="Validation script not found"):
            validator.validate(json_file)

    def test_validate_file_not_found(self, tmp_path: Path, mock_script: Path) -> None:
        """Test validation when JSON file doesn't exist."""
        validator = JsonValidator(script_path=mock_script)
        json_file = tmp_path / "nonexistent.json"

        with pytest.raises(ValidationError, match="JSON file not found"):
            validator.validate(json_file)

    def test_validate_script_failure(self, tmp_path: Path, mock_script: Path) -> None:
        """Test validation when script returns non-zero exit code."""
        validator = JsonValidator(script_path=mock_script)
        json_file = tmp_path / "test.json"
        json_file.write_text('{"key": "value"}')

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stderr="Error: Invalid JSON"
            )
            with pytest.raises(
                ValidationError, match="Validation failed: Error: Invalid JSON"
            ):
                validator.validate(json_file)

    def test_validate_subprocess_error(
        self, tmp_path: Path, mock_script: Path
    ) -> None:
        """Test validation when subprocess raises an exception."""
        validator = JsonValidator(script_path=mock_script)
        json_file = tmp_path / "test.json"
        json_file.write_text('{"key": "value"}')

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.SubprocessError("Process failed")
            with pytest.raises(ValidationError, match="Subprocess error: Process failed"):
                validator.validate(json_file)

    def test_validate_path_types(self, tmp_path: Path, mock_script: Path) -> None:
        """Test validation accepts both str and Path types."""
        validator = JsonValidator(script_path=mock_script)
        json_file = tmp_path / "test.json"
        json_file.write_text('{"key": "value"}')

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            # Test with Path
            validator.validate(json_file)
            assert mock_run.call_count == 1

            # Test with str
            validator.validate(str(json_file))
            assert mock_run.call_count == 2

    def test_validate_array_json(self, tmp_path: Path, mock_script: Path) -> None:
        """Test validation of JSON array."""
        validator = JsonValidator(script_path=mock_script)
        json_file = tmp_path / "array.json"
        json_file.write_text('[1, 2, 3]')

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            validator.validate(json_file)
            # Should succeed for arrays too
            assert mock_run.call_count == 1

    def test_validate_object_json(self, tmp_path: Path, mock_script: Path) -> None:
        """Test validation of JSON object."""
        validator = JsonValidator(script_path=mock_script)
        json_file = tmp_path / "object.json"
        json_data = {"source_package": "test", "binary_packages": []}
        json_file.write_text(json.dumps(json_data))

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            validator.validate(json_file)
            assert mock_run.call_count == 1

    def test_validation_error_message(self) -> None:
        """Test ValidationError can be instantiated with a message."""
        error = ValidationError("Custom error message")
        assert str(error) == "Custom error message"


class TestValidationError:
    """Test suite for ValidationError exception."""

    def test_inheritance(self) -> None:
        """Test that ValidationError inherits from Exception."""
        assert issubclass(ValidationError, Exception)

    def test_raise_and_catch(self) -> None:
        """Test raising and catching ValidationError."""
        with pytest.raises(ValidationError):
            raise ValidationError("Test error")
