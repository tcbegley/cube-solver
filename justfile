python_version := "3.12"

lint:
    uv run ruff check
    uv run ruff format --check
    uv run ty check

format:
    uv run ruff check --fix
    uv run ruff format

test:
    uv run --python {{ python_version }} pytest tests/
