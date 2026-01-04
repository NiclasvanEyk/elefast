from uuid import uuid4

from sqlalchemy import text, URL, NullPool
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
    engine: AsyncEngine, encoding: str = "utf8"
) -> AsyncEngine:
    database = f"pytest-elephantastic-{uuid4()}"
    async with engine.begin() as connection:
        statement = (
            f"CREATE DATABASE \"{database}\" ENCODING '{encoding}' TEMPLATE template0"
        )
        await connection.execute(text(statement))
        await connection.commit()
    return create_async_engine(engine.url.set(database=database))


async def drop_async_database(engine: AsyncEngine, name: str) -> None:
    async with engine.begin() as connection:
        statement = f'DROP DATABASE "{name}"'
        await connection.execute(text(statement))
