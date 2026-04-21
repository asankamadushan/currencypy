# Requires uv: https://docs.astral.sh/uv/
UV ?= uv

.DEFAULT_GOAL := help

.PHONY: help
help:
	@echo "Targets:"
	@echo "  sync          Install runtime deps only (uv sync)"
	@echo "  sync-all      Install project + all optional extras (uv sync --all-extras)"
	@echo "  lock          Refresh uv.lock from pyproject.toml (uv lock)"
	@echo "  test          Run pytest (set CL_API_KEY if your tests need it)"
	@echo "  tox           Run full tox envlist"
	@echo "  tox-pytest    Run tox -e pytest"
	@echo "  tox-mypy      Run tox -e mypy"
	@echo "  tox-ruff      Run tox -e ruff"
	@echo "  ruff          Run ruff check + format --check on src and tests"
	@echo "  mypy          Run mypy on src/ (via uv run)"
	@echo "  pre-commit    Run pre-commit on all files"
	@echo "  export-reqs   Write requirements.txt and requirements_dev.txt via uv export"
	@echo "  build         Build sdist and wheel (uv build)"
	@echo "  clean         Remove build artifacts and caches"

.PHONY: sync
sync:
	$(UV) sync

.PHONY: sync-all
sync-all:
	$(UV) sync --all-extras

.PHONY: lock
lock:
	$(UV) lock

.PHONY: test
test:
	$(UV) run pytest

.PHONY: tox
tox:
	$(UV) run tox

.PHONY: tox-pytest
tox-pytest:
	$(UV) run tox -e pytest

.PHONY: tox-mypy
tox-mypy:
	$(UV) run tox -e mypy

.PHONY: tox-ruff
tox-ruff:
	$(UV) run tox -e ruff

.PHONY: ruff
ruff:
	$(UV) run ruff check src tests
	$(UV) run ruff format --check src tests

.PHONY: mypy
mypy:
	$(UV) run mypy --install-types --non-interactive
	$(UV) run mypy src

.PHONY: pre-commit
pre-commit:
	$(UV) run pre-commit run --all-files

.PHONY: export-reqs
export-reqs:
	$(UV) export --no-dev -o requirements.txt
	$(UV) export --extra dev -o requirements_dev.txt

.PHONY: build
build:
	$(UV) build

.PHONY: clean
clean:
	rm -rf build dist .tox .pytest_cache .mypy_cache .ruff_cache src/currencypy.egg-info
	find src tests -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
