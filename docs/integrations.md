---
icon: lucide/blocks
---

# Integrations

## SQLAlchemy

Elefast can read `sqlalchemy.MetaData` objects to create your database schema.
Just use the `elefast.MetadataMigrator` and pass it your metadata object:

=== ":fontawesome-brands-python: tests/conftest.py"

    ```python hl_lines="2 7"
    from elefast import DatabaseServer, MetadataMigrator
    from my_app.models import Base

    def db_server() -> DatabaseServer:
        server = DatabaseServer(
            engine=getenv("TESTING_DB_URL"), 
            schema=MetadataMigrator(Base.metadata),
        )  
        await server.ensure_is_ready()
        return server
    ```

=== ":fontawesome-brands-python: my_app/models.py"

    ```python hl_lines="3"
    from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, mapped_column

    class Base(MappedAsDataclass, DeclarativeBase):
        pass


    class Post(Base):
        __tablename__ = "posts"

        slug: Mapped[str] = mapped_column(primary_key=True)
        headline: Mapped[str]
        body: Mapped[str]
    ```

## Alembic

If you want to build your schema using your migrations, just use the `AlembicMigrator` and pass it the path to your alembic config file.

=== ":fontawesome-brands-python: tests/conftest.py"

    ```python hl_lines="2 6 9"
    from elefast import DatabaseServer
    from elefast.extras.alembic import AlembicMigrator
    from pathlib import Path

    def db_server() -> DatabaseServer:
        alembic_config = Path(__file__).parent.parent / "alembic.ini"
        server = DatabaseServer(
            engine=getenv("TESTING_DB_URL"), 
            schema=AlembicMigrator(alembic_config),
        )  
        await server.ensure_is_ready()
        return server
    ```

## Docker

!!! note "Extra Dependency"

    This functionality requires you to install elefast with the `docker` extra:
    ```
    pip install 'elefast[docker]'
    ```

### Sticky Container

TODO: Compare to testcontainers
As mentioned previously, you 

### Optimizations

- tmpfs
- io stuff
- turning optimizations off

## FastAPI

We have [an example project](https://github.com/NiclasvanEyk/elefast/tree/main/examples/fastapi-async) demonstrating the use of the async API.
It also uses `pytest_asyncio` in [its fixtures](https://github.com/NiclasvanEyk/elefast/tree/main/examples/fastapi-async).

## uv

[The `elefast-example-uv-monorepo` example](https://github.com/NiclasvanEyk/elefast-example-uv-monorepo) shows you how you can create a repo-local Pytest plugin in your `uv` workspace.

