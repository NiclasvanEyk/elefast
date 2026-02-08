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

## Sync And Async

You might need to support both async and sync drivers.
Lets pretend you are using `psycopg`, which allows both!

First we define a single fixture which spawns our docker container and provides us with a connection URL.

```python
@pytest.fixture(scope="session")
def db_url() -> sqlalchemy.URL:
    return start_and_get_postgres_container_url(driver="psycopg")
```

Then we request the fixture in two fixtures to connect to the server, once in a sync and in an async way.

```python
@pytest.fixture(scope="session")
def postgres(db_url: sqlalchemy.URL):
    server = DatabaseServer(db_url, metadata=None)
    server.ensure_is_ready()
    return server

@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def async_postgres(db_url: sqlalchemy.URL):
    server = AsyncDatabaseServer(db_url, metadata=None)
    await server.ensure_is_ready()
    return server
```

Then add the usual fixtures for connecting to the db (use `elefast init` to see method bodies)

```python
@pytest.fixture
def db(postgres: DatabaseServer): ...

@pytest.fixture
def db_connection(db: Database): ...

@pytest.fixture
def db_session(db: Database): ...
```

Then everything again, but prefixed with `async_` and using the async components ((use `elefast init --async` to see method bodies)):

```python
@pytest_asyncio.fixture
async def async_db(async_postgres: AsyncDatabaseServer): ...

@pytest_asyncio.fixture
async def async_db_connection(async_db: AsyncDatabase): ...

@pytest_asyncio.fixture
async def async_db_session(async_db: AsyncDatabase): ... 
```

If you are using two different drivers, the setup is a bit more tricky.

Have the `db_url` use your sync driver, then create

```python
@pytest.fixture(scope="session")
def async_db_url(db_url: URL):
    return URL(
        drivername="asyncpg",  # Or whatever driver you use
        username=db_url.username,
        password=db_url.password,
        host=db_url.host,
        port=db_url.port,
        database=db_url.database,
        query=db_url.query,
    )
```

and request it in the `async_postgres` fixture instead of the `db_url` one.

## Monorepos

[The `elefast-example-uv-monorepo` example](https://github.com/NiclasvanEyk/elefast-example-uv-monorepo) shows you how you can create a repo-local Pytest plugin in your `uv` workspace.

<!-- ### Multiple Servers Or Databases -->

