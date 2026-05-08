#!/bin/bash
# Run all CI validation checks locally
# This script runs the EXACT same commands as .github/workflows/ci.yml
# to ensure local validation matches CI validation.

set -e  # Exit on first error

echo "🔍 Running CI validation checks..."
echo ""

echo "Step 1/5: Linting with ruff..."
uv run ruff check src/ tests/
echo "✅ Linting passed"
echo ""

echo "Step 2/5: Format check with ruff..."
uv run ruff format --check src/ tests/
echo "✅ Format check passed"
echo ""

echo "Step 3/5: Type checking with mypy..."
uv run mypy src/
echo "✅ Type check passed"
echo ""

echo "Step 4/5: Security scanning with bandit..."
uv run bandit -r src/
echo "✅ Security scan passed"
echo ""

echo "Step 5/5: Running tests with coverage..."
uv run pytest -v --cov=src --cov-report=term --cov-report=xml
echo "✅ Tests passed"
echo ""

echo "🎉 All CI validation checks passed!"
echo "✅ Safe to commit - CI will pass"
