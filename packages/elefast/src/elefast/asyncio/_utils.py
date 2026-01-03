from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


async def prepare_async_database(
    engine: AsyncEngine, encoding: str = "utf8"
) -> AsyncEngine:
    database = f"pytest-elephantastic-{uuid4()}"
    async with engine.begin() as connection:
        statement = (
            f"CREATE DATABASE \"pytest-elephantastic-{database}\" ENCODING '{encoding}'"
        )
        await connection.execute(text(statement))
    return create_async_engine(engine.url.set(database=database))
