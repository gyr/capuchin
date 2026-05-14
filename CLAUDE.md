# CLAUDE.md

Guide for Claude Code working this repo.

## Testing

```bash
uv run pytest                                          # All tests with coverage
uv run pytest tests/test_analyzer.py                   # Single file
uv run pytest tests/test_analyzer.py::TestAnalyzePackages::test_analyze_multiple_packages
uv run pytest -v --cov=src --cov-report=html           # Verbose + HTML report
```

**Test Isolation:** Always mock `setup_logging()` in tests calling `analyze_main()` - pattern: `@patch("src.commands.analyze.setup_logging")`. Why: Logging global state persist across tests, break `caplog`.

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
source_packages.json → capuchin analyze → Capuchin → subprocess (monkey buildinfo/ex) → MonkeyParser → SourcePackageData/BinaryPackageData → packages.json
```

**Components:**
- `cli.py`: Main CLI entry, argparse subparsers, routes to commands
- `commands/analyze.py`: Analyze command, argparse (--output-dir, --monkey-path, --verbose, --quiet, --log-file), logging setup, Rich progress bar
- `Capuchin` (analyzer.py): Main orchestration, subprocess execution, write packages.json
- `MonkeyParser` (monkey_parser.py): Parse `monkey buildinfo` → BinaryPackage list, `monkey ex` → (included, required_by_rpm)
- `models.py`: BinaryPackageData, SourcePackageData, to_dict() for JSON
- `commands/query.py`: Query command, search packages.json (source first, then binary), human/JSON output

**Subprocess pattern:** `cwd=self.monkey_path`, `capture_output=True`, `check=True`, wrapped in try/except. **CRITICAL:** `monkey ex` output to stderr not stdout.

## Logging Patterns (Project-Specific)

- **Long-running tools** (analyze): logger ONLY (`logger.info/error/debug`), NO print (conflict --quiet)
- **Query tools** (query): print to stdout (enable piping), logger.error for errors, keep stdout clean for `| jq`

Flags: `--verbose` (DEBUG), `--quiet` (suppress console), `--log-file PATH` (DEBUG to file)
