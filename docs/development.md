# Development Guide

## Project Structure

```
package-analyzer/
├── .github/
│   └── workflows/
│       └── ci.yml            # CI/CD pipeline
├── .gitignore                # Git ignore rules (.env, output/, etc.)
├── .python-version           # Python version (3.12)
├── .env.example              # Environment variable template
├── docs/
│   ├── architecture.md       # Architecture documentation
│   └── development.md        # This file
├── src/
│   ├── __init__.py
│   ├── config.py             # Configuration with ENV var handling
│   ├── models.py             # Data models (dataclasses)
│   ├── monkey_parser.py      # Parse monkey command outputs
│   ├── package_analyzer.py   # Main orchestration logic
│   ├── package_query.py      # Query tool
│   └── json_validator.py     # JSON validation
├── tests/
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_monkey_parser.py
│   ├── test_package_analyzer.py
│   ├── test_package_query.py
│   ├── test_json_validator.py
│   └── fixtures/
│       ├── buildinfo_*.txt   # Sample monkey buildinfo outputs
│       └── ex_*.txt          # Sample monkey ex outputs
├── output/                   # Generated files (gitignored)
│   ├── binary_packages.json
│   └── media_inclusion.json
├── source_packages.json      # Input: list of source packages
├── validate_json.sh          # JSON validation script
├── pyproject.toml            # Project config with all tools
├── README.md                 # Main documentation
├── CONTRIBUTING.md           # Contribution guidelines
└── CHANGELOG.md              # Version history
```

## Development Workflow

### 1. Setup Development Environment

```bash
# Clone repository
git clone <repository-url>
cd package-analyzer

# Install dependencies
uv sync

# Create .env file (optional)
cp .env.example .env
# Edit .env to set PACKAGE_MONKEY_PATH if different from default
```

### 2. Test-Driven Development (TDD)

This project follows TDD:

```bash
# 1. Write test first
# Create/edit tests/test_*.py

# 2. Run tests (they should fail)
uv run pytest tests/test_your_module.py -v

# 3. Implement feature
# Create/edit src/*.py

# 4. Run tests (they should pass)
uv run pytest tests/test_your_module.py -v

# 5. Refactor if needed

# 6. Run all tests
uv run pytest -v

# 7. Check coverage
uv run pytest --cov=src --cov-report=html
# Open htmlcov/index.html in browser
```

### 3. Local Quality Checks (Optional)

While CI runs all checks automatically, you can run them locally:

```bash
# Format code
uv run ruff format src/ tests/

# Lint
uv run ruff check src/ tests/ --fix

# Type check
uv run mypy src/

# Security scan
uv run bandit -r src/

# Run all tests
uv run pytest -v --cov=src
```

**One-liner:**
```bash
uv run ruff format src/ tests/ && \
uv run ruff check src/ tests/ && \
uv run mypy src/ && \
uv run pytest -v
```

### 4. Commit Changes

```bash
# Stage changes
git add <files>

# Commit with conventional commit message
git commit -m "feat: add new feature"

# Push (CI will run automatically)
git push
```

## Adding New Features

### Adding a New Parser

**Example: Adding a parser for a new monkey command**

1. **Create test file** with fixtures:

```python
# tests/test_new_parser.py
import pytest
from src.new_parser import NewParser

def test_parse_basic_output():
    """Test parsing basic output."""
    with open("tests/fixtures/new_command_output.txt") as f:
        output = f.read()
    
    parser = NewParser()
    result = parser.parse(output)
    
    assert result is not None
    assert len(result) > 0
```

2. **Create fixture file**:

```bash
# Capture real command output
cd /path/to/package_monkey
monkey new-command package-name > /path/to/project/tests/fixtures/new_command_output.txt
```

3. **Implement parser**:

```python
# src/new_parser.py
from typing import List
from src.models import NewModel

class NewParser:
    def parse(self, output: str) -> List[NewModel]:
        """Parse new command output."""
        # Implementation
        pass
```

4. **Run tests**:

```bash
uv run pytest tests/test_new_parser.py -v
```

### Extending Data Models

1. **Update models**:

```python
# src/models.py
from dataclasses import dataclass
from typing import List

@dataclass
class NewModel:
    """New data model."""
    field1: str
    field2: List[str]
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "field1": self.field1,
            "field2": self.field2
        }
```

2. **Update tests**:

```python
# tests/test_models.py
from src.models import NewModel

def test_new_model_creation():
    model = NewModel(field1="value", field2=["item1", "item2"])
    assert model.field1 == "value"
    assert len(model.field2) == 2

def test_new_model_to_dict():
    model = NewModel(field1="value", field2=["item1"])
    result = model.to_dict()
    assert result["field1"] == "value"
    assert result["field2"] == ["item1"]
```

3. **Run type checker**:

```bash
uv run mypy src/models.py
```

## Testing Guidelines

### Test Organization

- One test file per source file: `test_<module>.py`
- Group related tests in classes: `TestMonkeyParser`
- Use descriptive test names: `test_parse_buildinfo_with_multiple_packages`

### Test Fixtures

Place sample data in `tests/fixtures/`:

```
tests/fixtures/
├── buildinfo_fwts.txt          # Single binary package
├── buildinfo_gettext.txt       # Multiple binary packages
├── ex_fwts.txt                 # Direct inclusion
└── ex_libopenjph0_25.txt       # RPM dependency inclusion
```

### Mocking External Dependencies

Mock subprocess calls to avoid running actual monkey commands:

```python
from unittest.mock import patch, MagicMock

@patch('subprocess.run')
def test_run_monkey_command(mock_run):
    """Test monkey command execution."""
    mock_run.return_value = MagicMock(
        stdout="mocked output",
        stderr="",
        returncode=0
    )
    
    analyzer = PackageAnalyzer()
    result = analyzer.run_monkey_buildinfo("test-package")
    
    assert result == "mocked output"
    mock_run.assert_called_once()
```

### Coverage Requirements

- Maintain >90% code coverage
- Focus on critical paths and edge cases
- Exclude defensive code from coverage if appropriate

## Debugging Tips

### Debugging Parsers

1. **Capture real output**:

```bash
cd /path/to/package_monkey
monkey buildinfo package-name > debug_output.txt
```

2. **Test parser interactively**:

```python
from src.monkey_parser import MonkeyParser

with open("debug_output.txt") as f:
    output = f.read()

parser = MonkeyParser()
result = parser.parse_buildinfo(output)

# Inspect result
print(result)
```

3. **Add debug logging**:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# In parser code
logging.debug(f"Parsing line: {line}")
```

### Debugging Test Failures

```bash
# Run specific test with verbose output
uv run pytest tests/test_monkey_parser.py::test_specific_test -vv

# Drop into debugger on failure
uv run pytest tests/test_monkey_parser.py --pdb

# Show print statements
uv run pytest tests/test_monkey_parser.py -s
```

### Debugging Type Errors

```bash
# Run mypy with more verbose output
uv run mypy src/ --show-error-codes --show-traceback

# Check specific file
uv run mypy src/monkey_parser.py
```

## Common Issues and Solutions

### Issue: `ModuleNotFoundError`

**Solution**: Ensure you're running commands with `uv run`:

```bash
# Wrong
python -m src.analyze_packages

# Correct
uv run python -m src.analyze_packages
```

### Issue: `PACKAGE_MONKEY_PATH does not exist`

**Solutions**:
1. Set environment variable:
   ```bash
   export PACKAGE_MONKEY_PATH=/correct/path
   ```
2. Create `.env` file with correct path
3. Check that path exists and is a directory

### Issue: Tests fail with "fixture not found"

**Solution**: Ensure fixture files exist in `tests/fixtures/`:

```bash
ls tests/fixtures/
# Should show: buildinfo_*.txt, ex_*.txt
```

### Issue: CI fails but tests pass locally

**Common causes**:
1. Missing type hints (mypy strict mode)
2. Formatting issues (run `ruff format`)
3. Linting issues (run `ruff check`)
4. Security issues (run `bandit`)

**Solution**: Run all checks locally before pushing:
```bash
uv run ruff format src/ tests/ && \
uv run ruff check src/ tests/ && \
uv run mypy src/ && \
uv run pytest -v
```

## CI/CD Pipeline

The CI pipeline runs automatically on:
- Push to `master` or `develop` branches
- Pull requests to `master` or `develop`

### CI Steps

1. **Setup**: Install uv, Python 3.12, dependencies
2. **Lint**: `ruff check src/ tests/`
3. **Format Check**: `ruff format --check src/ tests/`
4. **Type Check**: `mypy src/`
5. **Security Scan**: `bandit -r src/`
6. **Tests**: `pytest -v --cov=src`
7. **Coverage Upload**: Upload to Codecov (optional)

### Viewing CI Results

- Go to repository → Actions tab
- Click on the workflow run
- Review logs for each step

## Release Process

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md` with changes
3. Commit changes:
   ```bash
   git commit -m "chore: bump version to X.Y.Z"
   ```
4. Tag release:
   ```bash
   git tag -a vX.Y.Z -m "Release vX.Y.Z"
   git push origin vX.Y.Z
   ```

## Useful Commands

```bash
# Run specific test file
uv run pytest tests/test_monkey_parser.py -v

# Run tests matching pattern
uv run pytest -k "test_parse" -v

# Show test coverage for specific file
uv run pytest --cov=src.monkey_parser --cov-report=term-missing

# Run tests in parallel (faster)
uv run pytest -n auto

# Update dependencies
uv sync --upgrade

# Add new dependency
# Edit pyproject.toml, then:
uv sync

# Check for security vulnerabilities
uv run bandit -r src/
```

## Resources

- [uv documentation](https://github.com/astral-sh/uv)
- [Ruff documentation](https://docs.astral.sh/ruff/)
- [pytest documentation](https://docs.pytest.org/)
- [MyPy documentation](https://mypy.readthedocs.io/)
- [Conventional Commits](https://www.conventionalcommits.org/)
