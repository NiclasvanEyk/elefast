> [!WARNING]  
> Not even alpha-level software, that hasn't even made its way to PyPi yet.

# Elefast 🐘⚡

Using an actual database for testing is nice, but setting everything up can be a pain.
Generating the schema, isolating the state, and supporting parallel execution while keeping everything reasonably quick.
Elefast helps you by providing utilities for all of these tasks

## Context

- You use Postgres and SQLAlchemy
- Your database schema can be created using `YourBaseClass.metadata.create_all`
- (optional but recommended) you use Docker to spawn your database server

## Installation

```shell
uv add 'elefast[docker]'
```

## Getting Started

Elefast does not come with an integration for e.g. pytest out of the box.

However, it makes it extremely easy to create your own set of fixtures with only a few lines of code.
Below is a starter setup to get you up and running.

> TODO: Double-check with example tests

```python
import os
import pytest
import elefast
import sqlalchemy

# TODO: Replace this with your own import.
from your_app.database.models import Base


@pytest.fixture(scope="session")
def postgres():
    # If we already have easy access to a postgres db server (e.g. through
    # GitHub CI service containers), we'll just that one. Can be dramatically
    # easier than configuring docker-in-docker in CI to then use the elefast one.
    url = os.getenv("TESTING_DB_URL") or elefast.docker.postgres(driver="psycopg")
    # The next line provides a utility class that creates the right DB schema for
    # us when we want to use a database in a test. It will live for the remainder
    # of the Pytest session.
    return elefast.DatabaseServer(url, metadata=Base.metadata)


@pytest.fixture
def db(postgres: elefast.DatabaseServer, monkeypatch: pytest.MonkeyPath):
    # This fixture is what you'll mainly interact with in your tests.
    # It uses the previously configured database server to create an
    # isolated and fresh database for each test. This enables you to
    # conveniently run your tests in parallel, while not having to worry
    # about running migrations, cleaning up test data, or properly resetting
    # a shared database between test runs. It is all handled by Elefast.
    with postgres.create_database() as database:
        # The next two lines can be extremely helpful when your application
        # code reads credentials from an environment variable. Feel free
        # to delete or adjust them based on your needs
        db_url = database.url.render_as_string(hide_password=False)
        monkeypatch.setenv("DB_URL", db_url)
        yield database


# The next two fixtures are (in my opinition) useful shortcuts. They enable
# you to have a fully migrated database.
@pytest.fixture
def db_connection(db: elefast.Database):
    with db.engine.begin() as connection:
        yield connection
@pytest.fixture
def db_session(db: elefast.Database):
    with db.session() as session:
        yield session
```

Then use them in your tests.
No need to manually start any Docker containers before the test, they'll be started for you and kept around for faster test execution in the future.

```python
def test_with_connect_fixture(db_connection: sqlalchemy.Connection):
    result, _ = db_connection.execute("select 1+1").fetch_one()
    assert result == 2


def test_with_session_fixture(db_session: sqlalchemy.orm.Session):
    admin = User(name="Admin", email="admin@root.com")
    db_session.add(admin)
    db_session.commit()
    # Act & assert based on business logic

  
def test_with_elefast(db: elefast.Database):
    # Accessing the raw db can make sense, too. Maybe you cache some stuff in your database
    # and test concurrent access.
    connection_a = db.connection.begin()
    connection_b = db.connection.begin()
    # Spawn threads that use both connections to connect to the DB at the same time
```

There are also async variants you can use when you use async drivers such as [asyncpg](https://github.com/MagicStack/asyncpg)
