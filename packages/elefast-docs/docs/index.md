---
icon: lucide/home
---

# Elefast

Elefast is an opiniated database testing toolkit that integrates [Postgres](https://www.postgresql.org), [SQLAlchemy](https://www.sqlalchemy.org).
It provides first-class features and documentation for using [Docker](https://www.docker.com) containers to automatically start your database with your tests and [Pytest](https://pytest.org) to run them and manage their setup logic.
Our guiding principles are:

- **Ease of use** 🌴
  You should not need to hand-roll hundreds of lines of code, just because you want your tests to cover actual database interaction.
  SQLAlchemy and Docker are not niche technologies, they are used by thousands of developers around the world.
- **Speed** ⏱️
  Using an actual database in your tests can slow thekm down significantly.
  E.g. launching a Postgres container using [Testcontainers](https://github.com/testcontainers/testcontainers-python#getting-started) takes almost 30 seconds[^1].
  With elefast, we'll ensure you'll pay as little startup costs as possible, while making it easy to avoid such waiting time alltogether by keeping the container around for future test runs.
- **Less magic** 🪄
  Pytest fixtures can be quite magical.
  Instead of providing ready-made fixtures with exotic configuration mechansims, Elefast makes you write your fixtures yourself.
  A tiny bit of effort, but you have full control and visibility.

The result is readable and performant test code like the following:

```python hl_lines="3"
from sqlalchemy import Connection, text

def test_that_uses_the_database(db_connection: Connection):  # (1)!
    result = db_connection.execute(text("1 + 1"))
    assert 2 == result
```

1. The `db_connection` fixture is written by you, but with the help of Elefast utility functions

When you run your tests with `pytest`, Elefast will

1. _(optional)_ Start an optimized Postgres container if one is not already running.
2. Create a fresh database, just for the test.
3. _(optional)_ Create the necessary table structures.
4. Pass the `Connection` object to the test.

This saves you from mocking DB logic, coming up with your own way of doing all of this.
Head over to the [Getting Started](./getting-started.md) to learn more.

[^1]: An anecdotal test run on my Intel MacBook Pro. It is probably faster on newer or more powerful hardware but it still does not seem to be optimized for speed, at least not enough for an impatient user like me.
