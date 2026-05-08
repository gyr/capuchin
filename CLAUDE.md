# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Package Analyzer is a Python CLI tool that analyzes source packages and their binary dependencies using the external `monkey` CLI tool. It extracts binary packages, reverse dependencies, and media inclusion data, outputting structured JSON.

## External Dependencies

**Critical:** This project requires external tools that must be pre-configured:

1. **monkey CLI tool** (package_monkey)
   - External dependency, not managed by this project
   - Must be installed and configured before running
   - Location configured via `PACKAGE_MONKEY_PATH` environment variable
   - Default: `/home/user/work/repos/monkey/package_monkey`
   - The analyzer executes `monkey buildinfo` and `monkey ex` commands via subprocess

2. **jq** (JSON processor)
   - Required for JSON validation
   - Install via system package manager: `zypper install jq` or `apt-get install jq`

## Development Setup

### Install Dependencies

```bash
# Install all dependencies (creates .venv)
uv sync

# Install package for CLI commands (analyze-packages, query-package)
uv pip install -e .
```

### Environment Configuration

Create `.env` file (optional, use `.env.example` as template):
```bash
PACKAGE_MONKEY_PATH=/path/to/package_monkey
```

## Testing

### Run Tests

```bash
# All tests with coverage (default configuration)
uv run pytest

# Single test file
uv run pytest tests/test_package_analyzer.py

# Single test class
uv run pytest tests/test_package_analyzer.py::TestAnalyzePackages

# Single test function
uv run pytest tests/test_package_analyzer.py::TestAnalyzePackages::test_analyze_multiple_packages

# Verbose output
uv run pytest -v

# Coverage report
uv run pytest --cov=src --cov-report=html
```

**Test Configuration:**
- pytest config in `pyproject.toml` includes coverage by default
- Coverage target: >90%
- HTML coverage report generated in `htmlcov/`

### Test Structure

```
tests/
├── fixtures/              # Sample monkey command outputs for testing
├── test_analyze_packages.py
├── test_config.py
├── test_json_validator.py
├── test_logging_config.py
├── test_models.py
├── test_monkey_parser.py
├── test_package_analyzer.py
└── test_query_package.py
```

**Testing Pattern:**
- Mock `subprocess.run` to avoid calling real monkey commands
- Use fixtures for sample monkey outputs
- Test both success and error paths
- Verify logging behavior with `caplog` fixture

## Code Quality

### Formatting and Linting

```bash
# Format code
uv run ruff format src/ tests/

# Lint with auto-fix
uv run ruff check src/ tests/ --fix

# Type checking
uv run mypy src/

# All checks in sequence (matches CI exactly)
uv run ruff format src/ tests/ && \
uv run ruff check src/ tests/ && \
uv run mypy src/ && \
uv run bandit -r src/ && \
uv run pytest -v --cov=src --cov-report=term --cov-report=xml
```

**Configuration:**
- Line length: 100 characters
- Python version: 3.12+
- Ruff rules: E, F, I, N, UP, B, C4, SIM, TCH
- mypy: strict mode enabled

## Architecture

### Data Flow

```
source_packages.json
    ↓
analyze_packages.py (CLI entry point)
    ↓
PackageAnalyzer (orchestration)
    ↓
subprocess → monkey buildinfo <package>  } For each source package
subprocess → monkey ex <binary>          } For each binary
    ↓
MonkeyParser (parse command outputs)
    ↓
SourcePackageData / BinaryPackageData (data models)
    ↓
packages.json (single output file, source-keyed)
```

### Key Components

**analyze_packages.py**
- CLI entry point for analysis
- Argument parsing (--output-dir, --monkey-path, --verbose, --quiet, --log-file)
- Logging setup via `logging_config.py`
- Progress bar display (Rich library)

**PackageAnalyzer** (`package_analyzer.py`)
- Main orchestration class
- Executes monkey commands via subprocess (in monkey_path directory)
- Coordinates parsing and data aggregation
- Writes single `packages.json` output

**MonkeyParser** (`monkey_parser.py`)
- Parses `monkey buildinfo` output → list of BinaryPackage
- Parses `monkey ex` output → (included: bool, required_by_rpm: list[str])
- Handles "not found" cases and malformed output

**Data Models** (`models.py`)
- `BinaryPackageData`: required_by, included, required_by_rpm
- `SourcePackageData`: source_name, binaries dict
- `to_dict()` methods for JSON serialization

**query_package.py**
- CLI entry point for querying
- Searches packages.json (source package first, then binary package)
- Human-readable or JSON output

### Subprocess Execution Pattern

All monkey commands run with:
- `cwd=self.monkey_path` (must execute in monkey directory)
- `capture_output=True` (get stdout/stderr)
- `check=True` (raise on non-zero exit)
- Wrapped in try/except to catch `CalledProcessError`

**Important:** `monkey ex` outputs to **stderr**, not stdout.

## Running the CLI

### Development Mode (without installation)

```bash
python -m src.analyze_packages source_packages.json
python -m src.query_package bash
```

### Installed Mode

```bash
analyze-packages source_packages.json --verbose --log-file debug.log
query-package bash --json | jq .
```

## Logging

This project uses Python's standard `logging` module with Rich for enhanced console output.

### CLI Logging Flags

- **--verbose / -v**: DEBUG level (shows exact commands)
- **--quiet / -q**: Suppress console output (file logging still works)
- **--log-file PATH**: Write logs to file (always DEBUG level)

### Logging Setup

`logging_config.py` configures:
- Console handler: RichHandler with colors
- File handler: Plain text, DEBUG level
- Root logger: "src" namespace

### In Code

```python
import logging
logger = logging.getLogger(__name__)

logger.debug("Running: %s", command)
logger.info("Analyzed %d packages", count)
logger.error("Failed to parse: %s", error)
```

## Output Format

**packages.json** structure:
```json
{
  "source_package_name": {
    "binary_package_name": {
      "required_by": ["dep1", "dep2"],
      "included": true,
      "required_by_rpm": ["rpm1"]
    }
  }
}
```

Top-level keys match input `source_packages.json`. Each source package maps to its binary packages with reverse dependency data.

## Common Patterns

### Adding a New CLI Flag

1. Update `parse_args()` in `analyze_packages.py`
2. Add test in `test_analyze_packages.py::TestParseArgs`
3. Pass argument through to `PackageAnalyzer` or relevant component
4. Add integration test in `TestMain`

### Extending MonkeyParser

1. Add test with sample monkey output in `tests/fixtures/`
2. Write failing test in `test_monkey_parser.py`
3. Implement parsing logic in `monkey_parser.py`
4. Run tests to verify

### Adding New Data Fields

1. Update `models.py` (add field to dataclass)
2. Update `to_dict()` if needed
3. Update tests: `test_models.py`
4. Update parser to populate new field
5. Update README documentation

## Troubleshooting

### "Command not found: monkey"

Ensure `PACKAGE_MONKEY_PATH` is set correctly and points to directory containing the `monkey` executable:

```bash
export PACKAGE_MONKEY_PATH=/path/to/package_monkey
# Or create .env file
```

### Tests Failing with subprocess errors

Tests should mock `subprocess.run`. If seeing real subprocess calls:
- Check that `@patch("subprocess.run")` decorator is present
- Ensure mock is configured: `mock_run.return_value = MagicMock(stdout="...", returncode=0)`

### Coverage Below 90%

Run coverage report to identify untested lines:
```bash
uv run pytest --cov=src --cov-report=term-missing
```

## Development Workflow

### Test-Driven Development (MANDATORY)

**This project requires strict TDD adherence.** No exceptions.

**Process:**
1. **Write test FIRST** - even if you know the implementation
2. **Run test** - verify it fails (red phase)
3. **Implement** minimal code to pass test (green phase)
4. **Run test** - verify it passes
5. **Refactor** if needed (while keeping tests green)
6. **Show changes** to user for review
7. **Only then** proceed to commit

**Why:** Tests document expected behavior, prevent regressions, and ensure correctness.

**Example:**
```bash
# 1. Write test (should fail)
uv run pytest tests/test_feature.py::test_new_feature -v
# FAILED ✓ (expected)

# 2. Implement feature
# ... edit src/feature.py ...

# 3. Test again (should pass)
uv run pytest tests/test_feature.py::test_new_feature -v
# PASSED ✓

# 4. Review changes with user before committing
```

### Commit Approval (MANDATORY)

**All commits require explicit user approval.** No autonomous commits.

**Process:**
1. Implement changes following TDD
2. Organize work into atomic commits
3. Show each commit to user:
   - `git diff` output
   - Clear description of what changed and why
4. Wait for user approval
5. Only commit after explicit "yes" from user

**Never commit without approval.** If unsure, ask: "May I create this commit?"

### Git Best Practices

**Atomic Commits:**
- One logical change per commit
- Each commit should be independently cherry-pickable
- Break large changes into focused commits

**Commit Messages:**
Follow Conventional Commits format:
```
<type>: <subject>

[optional body]

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

**Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `refactor:` - Code restructuring
- `test:` - Add/update tests
- `docs:` - Documentation

**Good Examples:**
```bash
fix: use logger.info for success message instead of print
feat: add logging to query_package.py
refactor: extract magic strings to constants in MonkeyParser
```

**Bad Examples:**
```bash
fix stuff                    # Too vague
huge changes to everything   # Not atomic
WIP                          # Never commit WIP
```

### Code Consistency Standards

When making any code changes, apply industry best practices **comprehensively**:

**Before changing code:**
1. Review ALL files for similar patterns
2. Identify ALL instances of the issue (not just one)
3. Create a plan showing everything that needs fixing
4. Group related fixes into atomic commits

**Example:** If fixing logging in one file, search entire codebase for print() usage and fix ALL inconsistencies together.

**Industry Standards to Follow:**

1. **Logging Patterns (Critical):**
   - **Long-running tools** (analyze-packages): Use logging framework ONLY
     - `logger.info()` for status
     - `logger.error()` for errors
     - `logger.debug()` for verbose output
     - NO `print()` statements (conflicts with --quiet mode)
   
   - **Query tools** (query-package): Mix strategically
     - `print()` to stdout for primary output (enables piping)
     - `logger.error()` for errors (NOT print to stderr)
     - Keep stdout clean for `| jq` piping

2. **Exception Handling (PEP 3134):**
   - Always use explicit chaining: `raise CustomError() from e`
   - Or explicit non-chaining: `raise CustomError() from None`
   - Document why when using `from None`

3. **Type Hints (PEP 484):**
   - Use specific types when possible
   - Use `typing.Any` for truly mixed types (add comment explaining why)
   - Avoid vague `object` type

4. **Code Quality:**
   - Delete dead code immediately (version control preserves history)
   - Extract magic strings to named constants
   - Follow PEP 8 import order: stdlib → third-party → local

**Testing Consistency:**
- Test new behavior, not just happy path
- Verify error cases and edge cases
- Use `caplog` for logging tests
- Use `capsys` for stdout/stderr tests

### Memory System and Long Sessions

This project uses Claude's persistent memory system to maintain context across sessions and prevent hallucinations.

**Why Save/Reload:** Long context windows (>10 interactions) can cause hallucinations. Regular save/restart/reload workflow keeps context fresh and maintains accuracy.

**Workflow:**
1. Save context to memory (at trigger points below)
2. Restart session (use `/new` command)
3. Load memory by asking: "continue where we left off"

**When to Save - Shared Responsibility:**

**User manages (micro-level):**
- After approximately **10 interactions** (count messages back-and-forth)
- End of work session

**Claude manages (macro-level):**
Claude will proactively suggest saving after completing:
- Major feature implementation
- Refactoring sessions
- Architectural decisions or planning
- Series of related commits
- Code consistency reviews
- When user signals end: "that's it for now"

**Memory captures:**
- Development workflow requirements (TDD, commit approval)
- Code consistency standards
- CLI logging patterns
- Architectural decisions
- Implementation progress
- User feedback on practices

**How to save:** User or Claude asks "save context to memory" at trigger points.

**How to load:** Start new session and ask "continue where we left off" or "load memory from previous session".

See CONTRIBUTING.md for additional details on commit conventions and pull request process.
