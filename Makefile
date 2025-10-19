.PHONY: help install lint test coverage clean docker-build docker-run docs docs-serve docs-build

# ==============================================================================
# Venv
# ==============================================================================

UV := $(shell command -v uv 2> /dev/null)
VENV_DIR?=.venv
PYTHON := $(VENV_DIR)/bin/python

# ==============================================================================
# Targets
# ==============================================================================

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  install      Install dependencies"
	@echo "  lint         Run linter and type checker"
	@echo "  test         Run tests"
	@echo "  coverage     Run tests with coverage reporting"
	@echo "  docs-serve   Serve documentation locally with live reload"
	@echo "  docs-build   Build documentation site"
	@echo "  docs         Alias for docs-serve"
	@echo "  docker-build Build Docker image for examples"
	@echo "  docker-run   Run example in Docker (use EXAMPLE='core_api')"
	@echo "  clean        Clean up temporary files"

install:
	@echo ">>> Installing dependencies"
	@$(UV) sync --all-extras

lint:
	@echo ">>> Running linter"
	@$(UV) run ruff format .
	@$(UV) run ruff check . --fix
	@echo ">>> Running type checker"
	@$(UV) run mypy --exclude 'examples/old' src examples
	@$(UV) run pyright

test:
	@echo ">>> Running tests"
	@$(UV) run pytest -q

coverage:
	@echo ">>> Running tests with coverage"
	@$(UV) run coverage run -m pytest -q
	@$(UV) run coverage report
	@$(UV) run coverage xml

docs-serve:
	@echo ">>> Serving documentation at http://127.0.0.1:8000"
	@$(UV) run mkdocs serve

docs-build:
	@echo ">>> Building documentation site"
	@$(UV) run mkdocs build

docs: docs-serve

docker-build:
	@echo ">>> Building Docker image"
	@docker build -t servicekit-examples .

docker-run:
	@echo ">>> Running Docker container with example: $(EXAMPLE)"
	@if [ -z "$(EXAMPLE)" ]; then \
		echo "Error: EXAMPLE not specified. Usage: make docker-run EXAMPLE=core_api"; \
		exit 1; \
	fi
	@docker run --rm -p 8000:8000 \
		-e EXAMPLE_MODULE=examples.$(EXAMPLE):app \
		servicekit-examples

clean:
	@echo ">>> Cleaning up"
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
	@find . -type d -name ".pytest_cache" -delete
	@find . -type d -name ".ruff_cache" -delete

# ==============================================================================
# Default
# ==============================================================================

.DEFAULT_GOAL := help
