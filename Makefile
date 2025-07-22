.PHONY: dev test test-verbose lint type format lock coverage e2e

dev:      ## Install + run first‑time setup
	uv pip install -e ".[dev]"
	pre-commit install

test:     ## Run all tests (quiet)
	uv run pytest -q

test-verbose:  ## Run all tests with verbose output
	uv run pytest -v

test-unit:  ## Run only unit tests
	uv run pytest -v tests/unit/

test-integration:  ## Run only integration tests
	uv run pytest -v tests/integration/

test-e2e:   ## Run only end-to-end tests
	uv run pytest -v tests/e2e/

lint:     ## Ruff + Black (check‑only)
	uv run ruff check .
	uv run black --check .

type:     ## Mypy static analysis
	uv run mypy --strict .

format:   ## Auto‑format
	uv run black .
	uv run ruff --fix .

lock:     ## Regenerate deterministic lock‑file
	uv pip freeze > requirements.txt   # optional

coverage: ## Run tests with coverage
	uv run pytest --cov=researchtopodcast --cov-report=html --cov-report=term

e2e:      ## Run end-to-end test (requires keys)
	uv run pytest -v --e2e tests/e2e/
