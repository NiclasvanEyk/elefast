from dataclasses import dataclass
from os import getenv

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, mapped_column


@dataclass
class DatabaseContext:
    engine: AsyncEngine
    sessionmaker: async_sessionmaker[AsyncSession]


def get_db() -> DatabaseContext:
    db_url = getenv("DB_URL")
    if not db_url:
        raise ValueError("No DB_URL environment variable set!")
    engine = create_async_engine(db_url)
    sessionmaker = async_sessionmaker(engine)
    return DatabaseContext(engine, sessionmaker)


class Base(MappedAsDataclass, DeclarativeBase):
    pass


class Post(Base):
    __tablename__ = "posts"

    slug: Mapped[str] = mapped_column(primary_key=True)
    headline: Mapped[str]
    body: Mapped[str]
