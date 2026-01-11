from elefast_core.errors import DatabaseNotReadyError
from sqlalchemy.exc import OperationalError
import time
from uuid import uuid4
from asyncio import sleep

from sqlalchemy import URL, NullPool, text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

type CanBeTurnedIntoAsyncEngine = AsyncEngine | URL | str


def build_engine(input: CanBeTurnedIntoAsyncEngine) -> AsyncEngine:
    if isinstance(input, AsyncEngine):
        return input
    if isinstance(input, URL | str):
        return create_async_engine(
            input, isolation_level="autocommit", poolclass=NullPool
        )
    raise TypeError()


async def prepare_async_database(
    engine: AsyncEngine, encoding: str = "utf8", template: str | None = None
) -> AsyncEngine:
    database = f"pytest-elephantastic-{uuid4()}"
    async with engine.begin() as connection:
        statement = (
            f"CREATE DATABASE \"{database}\" ENCODING '{encoding}' TEMPLATE template0"
            if template is None
            else f'CREATE DATABASE "{database}" WITH TEMPLATE "{template}"'
        )
        await connection.execute(text(statement))
        await connection.commit()
    return create_async_engine(engine.url.set(database=database))


async def drop_async_database(engine: AsyncEngine, name: str) -> None:
    async with engine.begin() as connection:
        statement = f'DROP DATABASE "{name}"'
        await connection.execute(text(statement))


async def wait_for_async_db(
    engine: AsyncEngine, timeout: int | float = 30, interval: int | float = 0.5
):
    deadline = time.monotonic() + timeout
    attempts = 0

    while True:
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return
        except Exception as error:
            attempts += 1
            if time.monotonic() >= deadline:
                raise DatabaseNotReadyError(
                    f"Reached the configured timeout of {timeout} seconds after {attempts} attempts connecting to the datbase."
                ) from error
            await sleep(interval)
