from elefast_example_fastapi_async.database import DatabaseContext
from fastapi import Depends, Request, FastAPI
from typing import Annotated

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession


# This relies on the logic in the lifespan
def get_db_context(request: Request) -> DatabaseContext:
    app = request.app
    if not isinstance(app, FastAPI):
        raise TypeError()
    database = app.state.database
    if not isinstance(database, DatabaseContext):
        raise TypeError()
    return database


DbContextDep = Annotated[DatabaseContext, Depends(get_db_context)]


def get_engine(db: DbContextDep) -> AsyncEngine:
    return db.engine


DbEngineDep = Annotated[AsyncEngine, Depends(get_engine)]


async def get_session(db: DbContextDep):
    async with db.sessionmaker() as session:
        yield session


DbSessionDep = Annotated[AsyncSession, Depends(get_session)]
