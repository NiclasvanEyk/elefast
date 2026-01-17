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


