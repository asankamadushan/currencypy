# Python currency conversion
This is wrapper for currancylayer API

## Development

Install [uv](https://docs.astral.sh/uv/), then create a virtual environment and install the project with dev dependencies:

```bash
uv sync --all-extras
```

Or only runtime dependencies:

```bash
uv sync
```

### Optional: export requirements files for pip-only workflows

If you need `requirements.txt` files (for example legacy CI), generate them from the lockfile:

```bash
uv export --no-dev -o requirements.txt
uv export --extra dev -o requirements_dev.txt
```

### Linting and formatting (Ruff)

[Ruff](https://docs.astral.sh/ruff/) checks and formats Python code (replacing Black, Flake8, and Pylint in this repo):

```bash
uv run ruff check src tests
uv run ruff format --check src tests
```

To apply formatting:

```bash
uv run ruff format src tests
```

### Type checking (mypy)

Static type checking is separate from Ruff:

```bash
uv run mypy src
```

### How to use pre-commit

Pre-commit runs Ruff and mypy (and file hygiene hooks):

```bash
uv run pre-commit run --all-files
```

### How to run tests

```bash
uv run pytest
```

Set `CL_API_KEY` in the environment (or `.env`) when exercising the API client.

Or use tox:

```bash
uv run tox -e pytest
```
