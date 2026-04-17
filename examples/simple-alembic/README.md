# Simple Alembic Example

This example contains a simple project that uses [Alembic](https://alembic.sqlalchemy.org).

It doesn't use `alembic.ini` and instead stores configuration in `pyproject.toml` under the `tool.alembic` table.

## Running Migrations

To get started, you can just run the repo-level tests using `pytest`.

> ![NOTE]
> If you already started elefast in the past, make sure to stop and remove any existing containers:
> ```shell
> docker stop elefast
> docker rm elefast
> ```

Then start the tests and set the `ELEFAST_HOST_PORT` environment variable, so we'll start the container on port 5432:

```shell
cd ../../ && ELEFAST_HOST_PORT=5432 pytest -n auto && cd -
```

This should start a sticky elefast container, which we can use to create a database:

```shell
docker exec -it elefast psql -U postgres -c 'CREATE DATABASE alembic_example'
```



