# Python currency conversion
This is wrapper for currancylayer API

## Runtime

- **Python 3.10+**
- **cachetools** (pinned in `pyproject.toml`) for in-memory rate caching: **live** quotes use a `TTLCache` (default TTL five minutes); **historical** quotes use an `LRUCache` (fixed calendar-day rates are reused without a time limit until evicted by size).
- Tune via `CurrencyConvertor(..., live_rate_ttl_seconds=..., rate_cache_maxsize=...)` (keyword-only).

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

### Logging

The package logs under the `currencypy` namespace (for example `currencypy.currency_convertor`). The library does not configure handlers; enable debug output in your application:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("currencypy").setLevel(logging.DEBUG)
```

Or raise the level only for the convertor module:

```python
logging.getLogger("currencypy.currency_convertor").setLevel(logging.DEBUG)
```

Or use tox:

```bash
uv run tox -e pytest
```
