from os import getenv

from sqlalchemy import Engine, create_engine


def get_db_url() -> str:
    return getenv(
        "DB_URL", "postgresql+psycopg://postgres:elefast@127.0.0.1/alembic_example"
    )


def get_engine() -> Engine:
    return create_engine(get_db_url())


_ENGINE: Engine | None = None


def get_engine_singleton() -> Engine:
    global _ENGINE
    if _ENGINE is not None:
        return _ENGINE
    _ENGINE = get_engine()
    return _ENGINE


def clear_engine_singleton() -> None:
    global _ENGINE
    if _ENGINE is None:
        return
    _ENGINE.dispose()
    _ENGINE = None
