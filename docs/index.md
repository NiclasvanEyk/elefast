---
icon: lucide/home
---

# About

Elefast is an opiniated database testing toolkit that integrates [Postgres](https://www.postgresql.org), [SQLAlchemy](https://www.sqlalchemy.org).
It provides first-class features and documentation for using [Docker](https://www.docker.com) containers to automatically start your database with your tests and [Pytest](https://pytest.org) to run them and manage their setup logic.
Our guiding principles are:

- **Ease of use** 🌴
  You should not need to hand-roll hundreds of lines of code, just because you want your tests to cover actual database interaction.
  SQLAlchemy and Docker are not niche technologies, they are used by thousands of developers around the world.
- **Speed** ⏱️
  Using an actual database in your tests can slow them down significantly.
  E.g. launching a Postgres container using [Testcontainers](https://github.com/testcontainers/testcontainers-python#getting-started) takes almost 30 seconds[^1].
  With elefast, we'll ensure you'll pay as little startup costs as possible, while making it easy to avoid such waiting time all together by keeping the container around for future test runs.
- **Less magic** 🪄
  Pytest fixtures can be quite magical.
  Instead of providing ready-made fixtures with exotic configuration mechanisms, Elefast makes you write your fixtures yourself.
  A tiny bit of effort, but you have full control and visibility.

The result is readable and performant test code like the following:

```python
from elefast import Database
from sqlalchemy import Connection, text, orm, select
from my_app import models


# Conveniently use a raw sqlalchemy.Connection
def test_raw_connection(db_connection: Connection):  # (1)!
    result = db_connection.execute(text("1 + 1"))
    assert 2 == result

# Or an orm session
def test_orm(db_session: orm.Session):
    posts = db_session.scalars(select(models.Post)).all()
    assert posts[0].title == "Test Title Defined In Fixture"

# Or both!
def test_elefast(db: Database):
    with db.session() as session:
        posts = db_session.scalars(select(models.Post)).all()
        assert posts[0].title == "Test Title Defined In Fixture"
    with db.connection() as connection:
        result = db_connection.execute(text("1 + 1"))
        assert 2 == result
```

When you run your tests with `pytest`, Elefast will

1. _(optional)_ Start an optimized Postgres container if one is not already running.
2. Create a fresh database, just for the test.
3. _(optional)_ Create the necessary table structures. (Either via [sqlalchemy](./integrations.md#sqlalchemy))
4. Pass the `Connection` object to the test.

This saves you from mocking DB logic, coming up with your own way of doing all of this.
Head over to the [Getting Started](./getting-started.md) to learn more.

[^1]: An anecdotal test run on my Intel MacBook Pro. It is probably faster on newer or more powerful hardware but it still does not seem to be optimized for speed, at least not enough for an impatient user like me.
