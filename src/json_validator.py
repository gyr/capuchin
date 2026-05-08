"""JSON validation using validate_json.sh script."""

import subprocess  # nosec B404 - subprocess needed for external script validation
from pathlib import Path


class ValidationError(Exception):
    """Raised when JSON validation fails."""

    pass


class JsonValidator:
    """Validates JSON files using the validate_json.sh script."""

    def __init__(self, script_path: Path | str = "validate_json.sh") -> None:
        """Initialize the validator.

        Args:
            script_path: Path to the validate_json.sh script.
                        Defaults to "validate_json.sh" in the current directory.
        """
        self.script_path = Path(script_path)

    def validate(self, json_file: Path | str) -> None:
        """Validate a JSON file.

        Args:
            json_file: Path to the JSON file to validate.

        Raises:
            ValidationError: If validation fails for any reason.
        """
        json_path = Path(json_file)

        # Check if script exists
        if not self.script_path.exists():
            raise ValidationError(f"Validation script not found: {self.script_path}")

        # Check if JSON file exists
        if not json_path.exists():
            raise ValidationError(f"JSON file not found: {json_path}")

        # Run the validation script
        try:
            result = subprocess.run(  # nosec B603 - controlled input, validation script path
                [str(self.script_path), str(json_path)],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                raise ValidationError(f"Validation failed: {error_msg}")

        except subprocess.SubprocessError as e:
            raise ValidationError(f"Subprocess error: {e}") from e
