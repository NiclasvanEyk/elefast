> [!WARNING]  
> Alpha-level software.

# Elefast 🐘⚡

Using an actual database for testing is nice, but setting everything up can be a pain.
Generating the schema, isolating the state, and supporting parallel execution while keeping everything reasonably quick.
Elefast helps you by providing utilities for all of these tasks

To learn more, visit [the documentation](https://niclasvaneyk.github.io/elefast/getting-started) or run through the quickstart guide below.

## Quickstart

Install the package from PyPi through your package manager

```shell
uv add 'elefast[docker]'
```

add the recommended set of fixtures to your `conftest.py`

```shell
mkdir tests/ && uv run elefast init >> tests/conftest.py
```

create a test using your new set of fixtures

```python
# tests/test_something_with_the_database.py
from sqlalchemy import Connection, text

def test_database_math(db_connection: Connection):
    result = db_connection.execute(text("SELECT 1 + 1")).scalar_one()
    assert result == 2
```

When you now run `pytest`, we'll automatically start a Docker container (if one is not already running), and pass a database connection into the test
