"""Configuration management for Package Analyzer."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()


class Config:
    """Application configuration."""

    DEFAULT_PACKAGE_MONKEY_PATH = "/home/user/work/repos/monkey/package_monkey"

    @staticmethod
    def get_package_monkey_path() -> Path:
        """Get package_monkey path from environment variable or default.

        Returns:
            Path to package_monkey directory.

        Raises:
            ValueError: If the path does not exist.
        """
        path_str = os.getenv("PACKAGE_MONKEY_PATH", Config.DEFAULT_PACKAGE_MONKEY_PATH)
        path = Path(path_str)

        if not path.is_dir():
            raise ValueError(f"PACKAGE_MONKEY_PATH does not exist: {path}")

        return path
