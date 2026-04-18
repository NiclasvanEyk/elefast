import os
from collections.abc import Iterator
from contextlib import contextmanager
from logging.config import fileConfig

from alembic import context
from sqlalchemy import Connection, engine_from_config, pool

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config
config.set_main_option(
    "sqlalchemy.url", os.environ["ELEFAST_ALEMBIC_EXAMPLE_TESTING_DB_URL"]
)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = None

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

@contextmanager
def get_connection() -> Iterator[Connection]:
    connection = config.attributes.get("connection") 
    if isinstance(connection, Connection):
        yield connection
    else:
        connectable = engine_from_config(
            config.get_section(config.config_ini_section, {}), 
            prefix="sqlalchemy.", 
            poolclass=pool.NullPool,
        )
        yield connectable.connect()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    with get_connection() as connection:
        # Connection provided directly - use it (no context manager)
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
            return


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
