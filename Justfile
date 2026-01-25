# Serves the documentation locally
docs:
    uv run zensical serve

# Runs all pytest tests. Requires Docker!
test:
    uv run pytest

# Applies automated fixes and formatting, then runs static analysis and type checking
check:
    ruff check --fix
    ruff format
    ty check
