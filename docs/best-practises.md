---
icon: lucide/award
---

# Best Practises

In the [Getting Started](./getting-started.md) guide you built a starting point which allowed you to run a simple `SELECT 1+1` query.
This is nice and gets you 95% there, but you probably have existing code that needs to connect to the testing database, as well as (hopefully) tests running in CI that might not be able to run Docker containers.

The remaining 5% are now covered by this guide.

!!! info

    If you've created your `tests/conftest.py` with `elefast init` you should already see some of these examples in your code.
    It still does not hurt to read up on why they might be useful, but you don't need to adjust your fixtures in some of the cases.

## Application Code

Previously we mostly focused on test code, but test code is worthless without the actual application code that should be tested.
If you integrate Elefast into an existing application, you may have wondered how to get your code to also connect to the test database created by our fixtures.

### Environment Variables

A solid solution is to have our application code read from environment variables, as described in ["The Twelve-Factor App"](https://12factor.net/).

```python
import os
from sqlalchemy import Engine, create_engine

def get_engine() -> Engine:
    db_url = os.getenv("DB_URL")
    if not db_url:
        raise ValueError("We expect a DB_URL environment variable to be present")
    return create_engine(db_url)
```

and then adjust your `db` fixture as follows:

```python
@pytest.fixture
def db(db_server: DatabaseServer, monkeypatch: pytest.MonkeyPatch):
    with db_server.create_database() as database:
        db_url = database.url.render_as_string(hide_password=False)
        monkeypatch.setenv("DB_URL", db_url)
        yield database
```

This will fill the `DB_URL` environment variable with a proper connection string that is different for each test.

!!! warning

    This will not work if you have a global `engine` variable laying around in your code.
    You might have heard that global variables are an anti-pattern, and this highlights one example why that is the case.
    In this case you can use the monkeypatching approach outlined in the next section.
    Alternatively you can also store your engine in your application state (our [async FastAPI example](https://github.com/NiclasvanEyk/elefast/tree/main/packages/elefast-example-fastapi-async/src/elefast_example_fastapi_async/app.py) shows you how), or use something like the `get_engine` function in the entrypoint of your application and pass it down through function arguments.

### Monkeypatching

Another approach is swapping out a global `engine` variable that might exist in your code.
This can look like this

```python title="tests/conftest.py"
# Add this import
from sqlalchemy import create_engine

@pytest.fixture
def db(db_server: DatabaseServer, monkeypatch: pytest.MonkeyPatch):
    with db_server.create_database() as database:
        engine = create_engine(database.url)
        monkeypatch.setenv("your_app.database", "engine", engine) # (1)!
        yield database
```

1. Replace "your_app.database" with the module that contains the global `engine` variable.

## Supporting Existing Database Servers

For some reasons it might be preferable to not always spawn a Docker container for your tests.
Maybe your colleague does not like Docker and prefers running Postgres directly on their computer.
Maybe your company policy prevents you from spawning Docker containers.
Or maybe getting a Docker access in CI is more cumbersome than just spawning a Postgres through your CI provider (see the related section of this page).

If only one of these reasons is true, you should provide a way to override the behavior in the `db_server` fixture.
Again we can use environment variables:

```python title="tests/conftest.py"
import os
from elefast import DatabaseServer, Database, docker

@pytest.fixture(scope="session")
def db_server() -> DatabaseServer:
    db_url = os.getenv("TESTING_DB_URL")
    if not db_url:
        db_url = docker.postgres()
    return DatabaseServer(db_url)
```

Now we try to read a database connection string from the `TESTING_DB_URL` environment variable.
If it is not present we still start a Docker container.

!!! tip
    Use `.env` files and [`pytest-dotenv`](https://pypi.org/project/pytest-dotenv) to have an easier time setting `TESTING_DB_URL` when running `pytest`.

## Continuus Integration (CI) Environments

- Examples for GitHub Actions or Gitlab CI
- Using existing servers

## Parallelizing Using pytest-xdist

This is more of a tip than a necessary adjustment, but since we create a database for each test, our tests are perfectly isolated.
As a consequence, we can run them in parallel through [`pytest-xdist`](https://pypi.org/project/pytest-xdist).
For smaller test suites this might actually increase the time required to run your tests.
But once you approach 100+ test cases that need a database, running them in parallel can easily cut your total testing time in half.

!!! note
    While the database site is perfectly isolated, there still may be other parts of your test suite that relies on global variables or test execution order.
    If your tests fail when run with `-n auto`, then you probably require more architectural effort to be able to parallelize your tests.

<!-- ## Seed Data -->

<!-- ## Migrations / Alembic -->


