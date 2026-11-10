.PHONY: help install dev-install test lint format type-check pre-commit clean run-init

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install package
	uv pip install -e .

dev-install: ## Install package with development dependencies
	uv pip install -e ".[dev]"
	playwright install chromium

test: ## Run tests
	pytest

test-cov: ## Run tests with coverage
	pytest --cov=aipentester --cov-report=html --cov-report=term

lint: ## Run ruff linter
	ruff check src/ tests/

format: ## Format code with ruff
	ruff format src/ tests/

type-check: ## Run mypy type checker
	mypy src/

pre-commit: ## Run all pre-commit checks
	ruff check src/ tests/
	ruff format src/ tests/ --check
	mypy src/
	pytest

clean: ## Clean build artifacts and cache
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

run-init: ## Initialize a new project
	aipentester init

run-validate: ## Validate engagement manifest
	aipentester validate-scope

run-version: ## Show version
	aipentester version

# Development targets
watch-test: ## Run tests in watch mode
	pytest-watch

build: ## Build distribution packages
	uv build

publish-test: ## Publish to TestPyPI
	uv publish --repository testpypi

publish: ## Publish to PyPI
	uv publish
