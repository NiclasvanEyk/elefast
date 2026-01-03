# Elefast

Using an actual database for testing is nice, but setting everything up can be a pain.
Generating the schema, isolating the state, and supporting parallel execution while keeping everything reasonably quick.
Elefast helps you by providing utilities for all of these tasks

## Opinions

- You use Postgres and SQLAlchemy
- Your database schema can be created using `YourBaseClass.metadata.create_all`
- (optional but recommended) you use Docker to spawn your database server

Given all of this, you can simply run

```shell
uv add 'elefast[pytest,docker]'
```

and you can start tests

```python
import pytest
import elefast
import sqlalchemy

from your_app.database.models import Base

# -----------------------------------------------------------------------------
# Use elefast to define your own datbase fixtures.
# No magic, everything is under your control and you are free to name your
# fixtures as you please. Below are some suggestions.
# -----------------------------------------------------------------------------

# This fixture creates a database server, which may host several databases,
# one for each test.
@pytest.fixture(scope="session")
def postgres():
    return elefast.dockerized_postgres()

# This fixture creates a fresh database for each test.
@pytest.fixture
def db(postgres: elefast.DatabaseServer, monkeypatch: pytest.MonkeyPath):
    with postgres.create_database(schema=Base.metadta) as database:
        db_url = database.engine.url.render_as_string(hide_password=False)
        monkeypatch.setenv("DB_URL", db_url)
        yield database

# (optional) The `elefast.Database` expose some utilities you may use.
@pytest.fixture
def db_connection(db: elefast.Database):
    with db.engine.begin() as connection:
        yield connection

# -----------------------------------------------------------------------------
# Then use them in your tests. No need to manually start any Docker containers
# before the test, they'll be started for you and kept around for faster test
# execution in the future.
# -----------------------------------------------------------------------------

def test_with_connect_fixture(db_connection: sqlalchemy.Connection):
    result, _ = db_connection.execute("select 1+1").fetch_one()
    assert result == 2
```
