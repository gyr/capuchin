# Contributing to Package Analyzer

Thank you for your interest in contributing! This document provides guidelines and instructions for development.

## Development Setup

### Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Git
- `monkey` CLI tool
- `jq` for JSON validation

### Initial Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd package-analyzer
```

2. Install dependencies:
```bash
uv sync
```

3. Configure environment (optional):
```bash
cp .env.example .env
# Edit .env to set PACKAGE_MONKEY_PATH if needed
```

## Development Workflow

### Test-Driven Development (TDD)

This project follows TDD practices:

1. Write tests first
2. Run tests (they should fail)
3. Implement the feature
4. Run tests again (they should pass)
5. Refactor if needed
6. Commit changes

### Local Development (Optional)

While all quality checks run automatically in CI, you can optionally run them locally for immediate feedback:

#### Recommended: Use Validation Scripts

Scripts guarantee exact match with CI validation:

```bash
# Run all CI validation steps:
./scripts/check.sh

# Auto-fix issues, then validate:
./scripts/fix.sh
```

See `scripts/README.md` for details and sync requirements.

#### Alternative: Run Individual Commands

```bash
# Format code
uv run ruff format src/ tests/

# Lint code
uv run ruff check src/ tests/ --fix

# Type check
uv run mypy src/

# Security scan
uv run bandit -r src/

# Run tests with coverage
uv run pytest -v --cov=src --cov-report=term --cov-report=xml
```

#### One-Liner for All Checks

```bash
# Same as ./scripts/check.sh but without the progress messages:
uv run ruff format src/ tests/ && \
uv run ruff check src/ tests/ && \
uv run mypy src/ && \
uv run bandit -r src/ && \
uv run pytest -v --cov=src --cov-report=term --cov-report=xml
```

**Note:** These checks are optional for local development. The CI pipeline will automatically run all checks on every push and pull request, so you don't need to run them manually unless you want immediate feedback.

## Code Style

### Formatting and Linting

- **Formatter**: Ruff (configured in `pyproject.toml`)
- **Line length**: 100 characters
- **Linting rules**: E (pycodestyle), F (pyflakes), I (isort), N (pep8-naming), UP (pyupgrade), B (bugbear), etc.

### Type Hints

- All functions must have type hints
- Use strict mode (configured in `pyproject.toml`)
- Run `mypy` to check type correctness

### Testing

- Write tests for all new features
- Maintain >90% code coverage
- Use fixtures for test data
- Mock external dependencies (subprocess calls)

**Test Isolation:**
- Always use `@patch("src.analyze_packages.setup_logging")` when testing `main()`
- Prevents logging side effects that break subsequent tests
- `tests/conftest.py` provides automatic cleanup (defense-in-depth)
- See commit bd6388c for details on logging test pollution fix

## Commit Message Conventions

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

### Format

```
<type>: <subject>

[optional body]

[optional footer]
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **test**: Adding or updating tests
- **refactor**: Code refactoring
- **chore**: Build process, dependencies, tooling
- **ci**: CI/CD changes

### Examples

```bash
feat: add support for parsing multiple inclusion paths

fix: handle empty required_by field in buildinfo output

docs: update README with new query options

test: add tests for monkey parser edge cases
```

### Commit Principles

- **Small, atomic commits**: Each commit represents one logical change
- **Descriptive messages**: Clear subject line, detailed body if needed
- **No huge blobs**: Break large changes into logical steps

## Pull Request Process

1. **Create a feature branch**:
```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes** following TDD and code style guidelines

3. **Run tests locally** (optional):
```bash
uv run pytest -v
```

4. **Commit your changes** with conventional commit messages:
```bash
git add .
git commit -m "feat: add new feature"
```

5. **Push to your fork**:
```bash
git push origin feature/your-feature-name
```

6. **Create a Pull Request**:
   - Provide a clear description of changes
   - Reference any related issues
   - Ensure CI checks pass

7. **Address review feedback** if needed

8. **Merge** once approved

## CI/CD Pipeline

All pull requests and pushes trigger the CI pipeline, which runs:

1. **Code formatting check** (ruff format)
2. **Linting** (ruff check)
3. **Type checking** (mypy)
4. **Security scanning** (bandit)
5. **Tests with coverage** (pytest)

The CI pipeline must pass before merging.

## Project Structure

```
package-analyzer/
├── src/               # Source code
│   ├── models.py      # Data models
│   ├── config.py      # Configuration
│   ├── monkey_parser.py
│   ├── package_analyzer.py
│   └── ...
├── tests/             # Test files
│   ├── fixtures/      # Test data
│   └── test_*.py      # Test modules
├── docs/              # Documentation
└── output/            # Generated files (gitignored)
```

## Adding New Features

### Adding a New Parser

1. Create test file: `tests/test_new_parser.py`
2. Add fixtures: `tests/fixtures/sample_output.txt`
3. Write tests
4. Implement parser: `src/new_parser.py`
5. Run tests and ensure they pass

### Extending Data Models

1. Update `src/models.py`
2. Add type hints
3. Update tests
4. Update documentation

## Getting Help

- Check existing issues
- Read the [architecture documentation](docs/architecture.md)
- Ask questions in pull requests or issues

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the code, not the person

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.
