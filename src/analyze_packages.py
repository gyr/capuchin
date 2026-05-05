"""CLI tool to analyze source packages and generate binary package data."""

import argparse
import json
import logging
import sys
from pathlib import Path

from src.config import Config
from src.logging_config import setup_logging
from src.package_analyzer import PackageAnalyzer

logger = logging.getLogger(__name__)


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        args: List of command-line arguments. If None, uses sys.argv[1:].

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Analyze source packages and generate packages.json output file."
    )

    parser.add_argument(
        "source_packages_file",
        help="Path to JSON file containing list of source package names",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path.cwd(),
        help="Directory to write packages.json file (default: current directory)",
    )

    parser.add_argument(
        "--monkey-path",
        type=str,
        help="Path to monkey executable directory (overrides PACKAGE_MONKEY_PATH env var)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        default=False,
        help="Enable verbose (DEBUG level) logging",
    )

    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        default=False,
        help="Suppress progress bar and console output (logging to file still works)",
    )

    parser.add_argument(
        "--log-file",
        type=Path,
        default=None,
        help="Write logs to specified file",
    )

    return parser.parse_args(args)


def main() -> int:
    """Main entry point for the analyze_packages CLI.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    args = parse_args()

    # Setup logging early
    setup_logging(verbose=args.verbose, log_file=args.log_file, quiet=args.quiet)

    try:
        # Read source packages from JSON file
        source_packages_path = Path(args.source_packages_file)
        if not source_packages_path.exists():
            logger.error("Source packages file not found: %s", source_packages_path)
            return 1

        try:
            with open(source_packages_path) as f:
                source_packages = json.load(f)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse source packages file: %s", e)
            return 1

        # Validate that it's a list
        if not isinstance(source_packages, list):
            logger.error(
                "Source packages file must contain a JSON array of package names"
            )
            return 1

        # Get monkey path (from CLI arg or config)
        monkey_path = args.monkey_path or str(Config.get_package_monkey_path())

        # Create analyzer and run analysis
        analyzer = PackageAnalyzer(
            monkey_path=monkey_path, output_dir=args.output_dir
        )
        analyzer.analyze_and_write(source_packages, show_progress=not args.quiet)

        output_file = args.output_dir / "packages.json"
        print(f"Analysis complete. Results written to {output_file}")
        return 0

    except ValueError as e:
        logger.error("%s", e)
        return 1
    except RuntimeError as e:
        logger.error("%s", e)
        return 1
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
