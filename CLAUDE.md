# CLAUDE.md

Guide for Claude Code working this repo.

## Project

Package Analyzer - Python CLI analyze source packages + binary deps using external `monkey` CLI. Output structured JSON.

## Dependencies

**monkey CLI** (package_monkey) - External tool. Must pre-configure. Location: `PACKAGE_MONKEY_PATH` env var (default `/home/user/work/repos/monkey/package_monkey`). Execute `monkey buildinfo` + `monkey ex` via subprocess.

**jq** - JSON processor. Install: `zypper install jq` or `apt-get install jq`

## Setup

```bash
uv sync                    # Install deps, create .venv
uv pip install -e .        # Install for CLI commands
```

Optional `.env`: `PACKAGE_MONKEY_PATH=/path/to/package_monkey`

## Testing

```bash
uv run pytest                                          # All tests with coverage
uv run pytest tests/test_package_analyzer.py           # Single file
uv run pytest tests/test_package_analyzer.py::TestAnalyzePackages::test_analyze_multiple_packages
uv run pytest -v --cov=src --cov-report=html           # Verbose + HTML report
```

**Test Isolation:** Always mock `setup_logging()` in tests calling `main()` - pattern: `@patch("src.analyze_packages.setup_logging")`. Why: Logging global state persist across tests, break `caplog`.

## Code Quality

**Recommended:** `./scripts/check.sh` (run all 5 CI steps), `./scripts/fix.sh` (auto-fix + validate)

**CI commands:**
```bash
uv run ruff format src/ tests/
uv run ruff check src/ tests/ --fix
uv run mypy src/
uv run bandit -r src/
uv run pytest -v --cov=src --cov-report=term --cov-report=xml
```

**Source of Truth:** `scripts/check.sh` + `.github/workflows/ci.yml` must stay in sync. See `scripts/README.md`.

## Python Standards

**Style:**
- PEP 8: snake_case funcs/vars, PascalCase classes, 4 spaces
- Type hints all signatures; use `|` syntax (3.10+); avoid `Any`
- Docstrings: Google/NumPy style (summary/Args/Returns)

**Idioms:**
- f-strings (not %, format)
- List comps over map/filter
- Context managers (`with`) for files/locks/resources
- Truthiness: `if items:` not `if len(items) > 0:`
- Early returns, avoid deep nesting
- dataclasses over raw dicts
- Generator expressions for large datasets
- `async`/`await` for I/O-bound tasks

**Error Handling:**
- EAFP style: try/except over LBYL (Look Before You Leap)
- Catch specific exceptions, never bare `Exception`
- Early returns for error cases

**Performance:**
- `cProfile` for bottlenecks
- dict/set lookups O(1) over list scans O(n)

## Architecture

**Data Flow:**
```
source_packages.json → analyze_packages.py → PackageAnalyzer → subprocess (monkey buildinfo/ex) → MonkeyParser → SourcePackageData/BinaryPackageData → packages.json
```

**Components:**
- `analyze_packages.py`: CLI entry, argparse (--output-dir, --monkey-path, --verbose, --quiet, --log-file), logging setup, Rich progress bar
- `PackageAnalyzer` (package_analyzer.py): Main orchestration, subprocess execution, write packages.json
- `MonkeyParser` (monkey_parser.py): Parse `monkey buildinfo` → BinaryPackage list, `monkey ex` → (included, required_by_rpm)
- `models.py`: BinaryPackageData, SourcePackageData, to_dict() for JSON
- `query_package.py`: CLI query, search packages.json (source first, then binary), human/JSON output

**Subprocess pattern:** `cwd=self.monkey_path`, `capture_output=True`, `check=True`, wrapped in try/except. **CRITICAL:** `monkey ex` output to stderr not stdout.

## CLI

```bash
# Dev mode
python -m src.analyze_packages source_packages.json
python -m src.query_package bash

# Installed
analyze-packages source_packages.json --verbose --log-file debug.log
query-package bash --json | jq .
```

## Logging Patterns (Project-Specific)

- **Long-running tools** (analyze-packages): logger ONLY (`logger.info/error/debug`), NO print (conflict --quiet)
- **Query tools** (query-package): print to stdout (enable piping), logger.error for errors, keep stdout clean for `| jq`

Flags: `--verbose` (DEBUG), `--quiet` (suppress console), `--log-file PATH` (DEBUG to file)

## Output

packages.json structure: `{"source_package_name": {"binary_package_name": {"required_by": [], "included": bool, "required_by_rpm": []}}}`

Top-level keys match input source_packages.json.