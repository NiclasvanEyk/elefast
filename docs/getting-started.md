---
icon: lucide/rocket
---

# Getting Started

This guide will walk you to the steps from installation, configuring your fixtures using Elefasts utility functions, to finally using the database in your tests.

## Installation

Elefast is available on PyPi, so you should be able to install it using your preferred package manager.
Below are some copy-pastable commands for common options.

=== "`uv`"
    ```shell
    uv add --dev 'elefast[docker]'
    ```
=== "`pip`"
    ```shell
    pip install 'elefast[docker]'
    ```

Note that they include the `docker` extra, which you can omit if you don't want to use the Docker-specific functionality.

## Setup

Once you installed the `elefast` package, you'll need to create some [Pytest fixtures](https://docs.pytest.org/en/stable/explanation/fixtures.html).
The following sections will walk you through the recommended set and explain each of them in detail.

??? tip "The Elefast CLI"

    To quickly get up and running in a new project, you can use the `init` command.
    It ask you some questions about your setup (e.g. which driver you'll use, if you use async or not, etc.) and print boilerplate code to the console.
    
    Make sure you have activated your virtual environment and run it like this:

    ```bash
    mkdir tests/ && elefast init > tests/conftest.py
    ```

### Database Server

Often times Postgres instances only consist of a single database often called `postgres`.
However, Posgres is actually a database _server_ that can house multiple databases at once.
We'll use this to our advantage, and use Elefasts utility functions to create a database per test.
This isolates our tests and makes sure that data written by `test_a` does not influence `test_b`.
At the same time, it unlocks running our tests in parallel, e.g. using [the wonderful `pytest-xdist`](https://github.com/pytest-dev/pytest-xdist).

Since you'll probably want to access your database in multiple tests, distributed across multiple files, we'll add them to [our `tests/conftest.py` file](https://docs.pytest.org/en/stable/reference/fixtures.html#conftest-py-sharing-fixtures-across-multiple-files).

!!! info

    All code snippets in this guide represent code that will be added to `tests/conftest.py`.
    We won't show the whole file contents everytime, just the stuff that you'll need to append if you want to code along.

The first fixture is already the most important one, which sets up our database server.


```python title="tests/conftest.py"
from elefast import DatabaseServer, Database, docker

from your_app.database.models import Base # (1)!

@pytest.fixture(scope="session")
def db_server() -> DatabaseServer:
    db_url = docker.postgres()
    return DatabaseServer(db_url, metadata=Base.metadata)
```

1. This is a placeholder. Adjust it to point to your SQLAlchemy base model if you use the ORM.

As you can see, we create a `session`-scoped fixture. This just means that we'll run this code _once_ during the whole lifetime of a `pytest` execution / session ([Pytest docs](https://docs.pytest.org/en/stable/how-to/fixtures.html#scope-sharing-fixtures-across-classes-modules-packages-or-session)).

We obtain a database URL from the `postgres` method of the `docker` extra, which automatically starts up a Docker container optimized for testing.
If you don't use the `docker` extra, just pass a `sqlalchemy.URL` that points enables us to connect to an existing Postgres server.

Finally, we also pass the table metadata object of our ORM base class.
This enables Elefast to automatically create all the necessary database tables you need.
If you don't use the SQLAlchemy ORM don't worry, this parameter is completely optional and you can just omit it.

### Actual Database

Now that we have a fixture that provides us with a database server, we can add another one that creates a database when we need one for a test.

```python title="tests/conftest.py"
# ...

@pytest.fixture
def db(db_server: DatabaseServer): # (1)!
    with db_server.create_database() as database:
        yield database
```

1. The argument name here is very important. It has to match the function name of the fixture we defined before!

As you can see, we don't explicitly pass a fixture scope, which just means that this code will be run for each test that uses this fixture.
Next we'll create a database in our Postgres server using a context manager and immediately `yield` it.
This just ensures that we'll delete the database after the test.

### Connection Utilities

Now we could already use the `db` fixture to connect to our database in the tests.
However, this would lead to lots of `with` blocks and indentation, which can be a bit annoying.

So while we are here creating fixtures, let's make our lives a little bit easier and create two more that will help us connect to our database.

```python title="tests/conftest.py"
# ...

@pytest.fixture
def db_connection(db: Database):
    with db.engine.begin() as connection:
        yield connection

@pytest.fixture
def db_session(db: Database):
    with db.session() as session:
        yield session
```

The first one creates a raw `sqlalchemy.Connection` object that allows us to run code inside a database transaction.
The latter creates an `sqlalchemy.orm.Session` that we can use to setup specific ORM objects that should exist before we run our test logic, or assert that they exist afterwards.

!!! info
    Feel free to adjust the names to what suits you best.
    We'll stick to the names from this example throughout the documentation, so you have an easier time cross-referencing code.
    But if you e.g. mostly interact with your database through the ORM, feel free to rename what we've named `db_session` to just `db`, and come up with another name for the fixture we named `db` (maybe the longer form `database`?).
    In the end, this all comes down to personal preference, which is one of the reasons why Elefast does not come with these fixtures out of the box.

### Usage In Tests

To then 

```python title="tests/test_database_math.py"
from sqlalchemy import Connection

def test_quick_maths(db_connection: Connection):
    pass
```

Now run `pytest` in your terminal, and you should see our test pass.
Behind the scenes, our fixtures have started a Postgres container, maybe created a table structure, and connected to it.
However, all of this does not clutter up our actual testing code.

### Recap



## Where To Go From Here

If you've coded along, you have a solid base to run your database-related tests locally.
That base can be improved even further, e.g. by allowing
If you are interested in making your fixture setup more flexible, head over to the [Best Practises](./best-practises.md).

Otherwise there is a [recipes](./recipes.md) page documenting various other adjustments and code snippets that might be useful for your use case.
They show you how to connect to your database using `async` / `await`, how you , or how to share fixtures in a monorepo.
