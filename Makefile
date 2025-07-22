.PHONY: dev test lint type format lock
dev:      ## Install + run first‑time setup
	uv pip install -e ".[dev]"
	pre-commit install

test:     ## Run all tests
	uv pip run pytest -q

lint:     ## Ruff + Black (check‑only)
	uv pip run ruff check .
	uv pip run black --check .

type:     ## Mypy static analysis
	uv pip run mypy --strict .

format:   ## Auto‑format
	uv pip run black .
	uv pip run ruff --fix .

lock:     ## Regenerate deterministic lock‑file
	uv pip freeze > requirements.txt   # optional
