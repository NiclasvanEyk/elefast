"""Shared fixtures and mocks for elefast tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy import URL, Column, Engine, Integer, MetaData, String, Table
from sqlalchemy.ext.asyncio import AsyncEngine


@pytest.fixture
def mock_engine() -> Generator[Engine, None, None]:
    """Create a mock SQLAlchemy Engine."""
    engine = MagicMock(spec=Engine)
    engine.url = URL.create(
        drivername="postgresql+psycopg2",
        username="test",
        password="test",
        host="localhost",
        port=5432,
        database="test_db",
    )
    engine.begin.return_value.__enter__ = MagicMock()
    engine.begin.return_value.__exit__ = MagicMock()
    yield engine


@pytest.fixture
def mock_async_engine() -> Generator[AsyncEngine, None, None]:
    """Create a mock SQLAlchemy AsyncEngine."""
    engine = MagicMock(spec=AsyncEngine)
    engine.url = URL.create(
        drivername="postgresql+asyncpg",
        username="test",
        password="test",
        host="localhost",
        port=5432,
        database="test_db",
    )
    engine.begin.return_value.__aenter__ = AsyncMock()
    engine.begin.return_value.__aexit__ = AsyncMock()
    engine.dispose = AsyncMock()
    yield engine


@pytest.fixture
def sample_metadata() -> MetaData:
    """Create a sample SQLAlchemy MetaData with tables."""
    metadata = MetaData()
    Table(
        "users",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("name", String(100)),
        Column("email", String(100)),
    )
    Table(
        "posts",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("title", String(200)),
        Column("user_id", Integer),
    )
    return metadata


@pytest.fixture
def sample_metadata_with_schema() -> MetaData:
    """Create a sample SQLAlchemy MetaData with tables in different schemas."""
    metadata = MetaData()
    Table(
        "users",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("name", String(100)),
        schema="app",
    )
    Table(
        "posts",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("title", String(200)),
        schema="app",
    )
    Table(
        "public_table",
        metadata,
        Column("id", Integer, primary_key=True),
        schema="public",
    )
    return metadata


@pytest.fixture
def mock_docker_container() -> Generator[MagicMock, None, None]:
    """Create a mock Docker container."""
    container = MagicMock()
    container.name = "elefast"  # Matches default Configuration.container.name
    container.status = "running"
    container.attrs = {"Config": {"Env": ["ELEFAST_POSTGRES_HOST_PORT=54321"]}}
    yield container


@pytest.fixture
def mock_docker_client(
    mock_docker_container: MagicMock,
) -> Generator[MagicMock, None, None]:
    """Create a mock Docker client."""
    client = MagicMock()
    client.containers.list.return_value = [mock_docker_container]
    client.containers.run.return_value = mock_docker_container
    yield client


@pytest.fixture(autouse=True)
def clear_template_cache():
    """Clear template database cache between tests."""
    yield
    # Clean up any cached template DB names after each test
