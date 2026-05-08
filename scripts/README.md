# CI Validation Scripts

Scripts for running CI validation locally to prevent local vs CI mismatches.

## Scripts

- **`check.sh`** - Run all CI validation steps (read-only check)
- **`fix.sh`** - Auto-fix issues, then validate

## Usage

```bash
# Before committing, validate your code:
./scripts/check.sh

# Auto-fix formatting and linting issues:
./scripts/fix.sh
```

## CRITICAL: Keeping Scripts in Sync with CI

**These scripts MUST match .github/workflows/ci.yml exactly.**

When CI workflow changes:
1. Update `.github/workflows/ci.yml` first
2. Update `scripts/check.sh` to match (same commands, same order)
3. Test locally with `./scripts/check.sh`
4. Commit both changes together

**Why:** These scripts exist to prevent local/CI validation mismatches.
If they drift from CI, they lose their value.

**Source of Truth:** `.github/workflows/ci.yml`

## What Each Script Does

### check.sh
Runs the exact same 5 validation steps as CI:
1. Ruff linting (`ruff check`)
2. Ruff format check (`ruff format --check`)
3. Mypy type checking (`mypy`)
4. Bandit security scan (`bandit -r src/`)
5. Pytest with coverage (`pytest --cov`)

Exits on first failure (`set -e`).

### fix.sh
Auto-fixes what can be automatically fixed:
1. Runs `ruff format` (auto-format)
2. Runs `ruff check --fix` (auto-fix linting)
3. Calls `check.sh` for full validation

Use this before committing to clean up formatting/linting issues.
