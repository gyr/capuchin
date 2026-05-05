"""CLI tool to analyze source packages and generate binary package data."""

import argparse
import json
import sys
from pathlib import Path

from src.config import Config
from src.package_analyzer import PackageAnalyzer


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        args: List of command-line arguments. If None, uses sys.argv[1:].

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Analyze source packages and generate binary package data."
    )

    parser.add_argument(
        "source_packages_file",
        help="Path to JSON file containing list of source package names",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path.cwd(),
        help="Directory to write output JSON files (default: current directory)",
    )

    parser.add_argument(
        "--monkey-path",
        type=str,
        help="Path to monkey executable directory (overrides PACKAGE_MONKEY_PATH env var)",
    )

    return parser.parse_args(args)


def main() -> int:
    """Main entry point for the analyze_packages CLI.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    args = parse_args()

    try:
        # Read source packages from JSON file
        source_packages_path = Path(args.source_packages_file)
        if not source_packages_path.exists():
            print(
                f"Error: Source packages file not found: {source_packages_path}",
                file=sys.stderr,
            )
            return 1

        try:
            with open(source_packages_path) as f:
                source_packages = json.load(f)
        except json.JSONDecodeError as e:
            print(
                f"Error: Failed to parse source packages file: {e}",
                file=sys.stderr,
            )
            return 1

        # Validate that it's a list
        if not isinstance(source_packages, list):
            print(
                "Error: Source packages file must contain a JSON array of package names",
                file=sys.stderr,
            )
            return 1

        # Get monkey path (from CLI arg or config)
        monkey_path = args.monkey_path or str(Config.get_package_monkey_path())

        # Create analyzer and run analysis
        analyzer = PackageAnalyzer(
            monkey_path=monkey_path, output_dir=args.output_dir
        )
        analyzer.analyze_and_write(source_packages)

        print(f"Analysis complete. Results written to {args.output_dir}")
        return 0

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
