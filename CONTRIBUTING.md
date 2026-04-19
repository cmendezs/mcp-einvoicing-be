# Contributing to mcp-einvoicing-be

Thank you for your interest in contributing. This document explains the workflow and expectations.

## Development setup

```bash
git clone https://github.com/cmendezs/mcp-einvoicing-be.git
cd mcp-einvoicing-be
uv sync --all-extras
```

## Running the test suite

```bash
uv run pytest
```

Run with verbose output:

```bash
uv run pytest -v
```

## Linting and type checking

```bash
uv run ruff check src tests
uv run ruff format --check src tests
uv run mypy src
```

To auto-fix lint issues:

```bash
uv run ruff check --fix src tests
uv run ruff format src tests
```

## Pull request checklist

- [ ] All tests pass (`pytest`)
- [ ] No lint errors (`ruff check`)
- [ ] No type errors (`mypy src`)
- [ ] New or changed behaviour is covered by tests
- [ ] Validation fixes reference the relevant rule ID (e.g. `PINT-BE-R001`)
- [ ] `CHANGELOG.md` updated under `[Unreleased]`

## Commit style

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add validate_pint_be tool
fix: normalize BE VAT numbers with leading zeros
docs: update README with Mercurius configuration
test: add fixture for PINT-BE credit note
```

## Reporting issues

Please open an issue at https://github.com/cmendezs/mcp-einvoicing-be/issues and include:

- The tool name and input you used
- The expected result
- The actual result (full error message or unexpected output)
- The Belgian e-invoicing standard or rule ID involved, if known
