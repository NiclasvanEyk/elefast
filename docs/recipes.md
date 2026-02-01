---
icon: lucide/chef-hat
---

# Recipes

Since Elefast is very flexible, there is no one-size-fits-all solution.
This page describes several copy-paste friendly examples to get you up and running regardless of your setup.

## Persistent Databases

The `elefast init` command generates code that roughly looks like the following

```python
# Setup code for the database server...

@pytest.fixture
def db(db_server: DatabaseServer):
    with db_server.create_database() as database:
        yield database

# Utilities for connection to the database...
```

As you can see, we use the context manager API provided by the `elefast.Database` instance that is returned from `db_server.create_database()`,
This ensures that our databases that get created for each test are properly cleaned up after each test runs, even if it throws an exception.

However, this behavior might not be what you want.
In this case, just return the new database object.

```python
@pytest.fixture
def db(db_server: DatabaseServer):
    return db_server.create_database()
```

For one, this makes the test run a tiny bit faster.
Deleting data takes some time, and if we e.g. run in a CI environment, the container and all its data will be deleted anyways.
Just be aware that this may fill up your RAM or disk if your test suite is large.

Another good reason is debugging.
Maybe you want to inspect the database state that your failing test generated.
In that case, it can be helpful to prefix the databases with the test name that it belongs to.

```python
@pytest.fixture
def db(db_server: DatabaseServer, request: pytest.FixtureRequest):
    return db_server.create_database(prefix=request.node.name)
```

Now you can connect to the testing database with your datbabase explorer or `psql` and look for a database that starts with the name of your test case.
Note that the name will be suffixed by a UUID to ensure uniqueness.

## Async

Async/await can enable nice performance gains, especially when paired with a ASGI framework like FastAPI.
Elefast supports `async` out of the box.
Just prefix all classes with `Async*` and you should be fine.

If you want to see examples, run the following command in your activated virtual environment

```shell
elefast init --async --driver=asyncpg
```

Alternatively we have [an example project](https://github.com/NiclasvanEyk/elefast/tree/main/examples/fastapi-async) demonstrating the use of the async API.
It also uses `pytest_asyncio` in [its fixtures](https://github.com/NiclasvanEyk/elefast//examples/fastapi-async).

## Monorepos

[The `elefast-example-uv-monorepo` example](https://github.com/NiclasvanEyk/elefast-example-uv-monorepo) shows you how you can create a repo-local Pytest plugin in your `uv` workspace.

<!-- ### Multiple Servers Or Databases -->

