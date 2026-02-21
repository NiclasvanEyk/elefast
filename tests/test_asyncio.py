"""Tests for the elefast.asyncio module."""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from sqlalchemy import URL

from elefast.asyncio import (
    AsyncDatabase,
    AsyncDatabaseServer,
    _build_engine,
    _prepare_async_database,
)
from elefast.errors import DatabaseNotReadyError


class TestBuildEngineAsync:
    """Tests for the _build_engine function in asyncio module."""

    def test_build_engine_from_async_engine(self, mock_async_engine):
        """Test that _build_engine returns an AsyncEngine as-is."""
        result = _build_engine(mock_async_engine)
        assert result is mock_async_engine

    @patch("elefast.asyncio.create_async_engine")
    def test_build_engine_from_url_object(self, mock_create_engine):
        """Test _build_engine with a URL object."""
        mock_result = MagicMock()
        mock_create_engine.return_value = mock_result
        url = URL.create(
            drivername="postgresql+asyncpg",
            username="test",
            password="test",
            host="localhost",
            port=5432,
        )
        result = _build_engine(url)
        mock_create_engine.assert_called_once()
        assert result is mock_result

    @patch("elefast.asyncio.create_async_engine")
    def test_build_engine_from_string(self, mock_create_engine):
        """Test _build_engine with a connection string."""
        mock_result = MagicMock()
        mock_create_engine.return_value = mock_result
        conn_string = "postgresql+asyncpg://test:test@localhost:5432/test_db"
        result = _build_engine(conn_string)
        mock_create_engine.assert_called_once()
        assert result is mock_result

    def test_build_engine_from_invalid_type(self):
        """Test that _build_engine raises TypeError for invalid input."""
        with pytest.raises(TypeError):
            _build_engine(123)  # type: ignore


class TestAsyncDatabase:
    """Tests for the AsyncDatabase class."""

    def test_database_init(self, mock_async_engine):
        """Test AsyncDatabase initialization."""
        server = MagicMock(spec=AsyncDatabaseServer)
        db = AsyncDatabase(engine=mock_async_engine, server=server)

        assert db.engine is mock_async_engine
        assert db.server is server
        assert db.name == "test_db"

    def test_database_url_property(self, mock_async_engine):
        """Test AsyncDatabase.url property."""
        server = MagicMock(spec=AsyncDatabaseServer)
        db = AsyncDatabase(engine=mock_async_engine, server=server)

        assert db.url == mock_async_engine.url

    @pytest.mark.asyncio
    async def test_database_async_context_manager(self, mock_async_engine):
        """Test AsyncDatabase as an async context manager auto-cleans up."""
        server = MagicMock(spec=AsyncDatabaseServer)
        server.drop_database = AsyncMock()
        mock_async_engine.dispose = AsyncMock()

        db = AsyncDatabase(engine=mock_async_engine, server=server)

        async with db:
            pass

        server.drop_database.assert_awaited_once_with("test_db")
        mock_async_engine.dispose.assert_awaited_once()

    def test_database_session_creation(self, mock_async_engine):
        """Test AsyncDatabase.session() creates a session."""
        server = MagicMock(spec=AsyncDatabaseServer)
        mock_session = MagicMock()
        mock_sessionmaker = MagicMock(return_value=mock_session)
        db = AsyncDatabase(
            engine=mock_async_engine,
            server=server,
            sessionmaker_factory=lambda e: mock_sessionmaker,
        )

        session = db.session()
        assert session is mock_session

    @pytest.mark.asyncio
    async def test_database_drop(self, mock_async_engine):
        """Test AsyncDatabase.drop() cleans up properly."""
        server = MagicMock(spec=AsyncDatabaseServer)
        server.drop_database = AsyncMock()
        mock_async_engine.dispose = AsyncMock()

        db = AsyncDatabase(engine=mock_async_engine, server=server)
        await db.drop()

        mock_async_engine.dispose.assert_awaited_once()
        server.drop_database.assert_awaited_once_with("test_db")


class TestAsyncDatabaseServer:
    """Tests for the AsyncDatabaseServer class."""

    def test_server_init_with_engine(self, mock_async_engine):
        """Test AsyncDatabaseServer initialization with an AsyncEngine."""
        server = AsyncDatabaseServer(engine=mock_async_engine)
        assert server.url == mock_async_engine.url

    @patch("elefast.asyncio._build_engine")
    def test_server_init_with_url(self, mock_build_engine):
        """Test AsyncDatabaseServer initialization with a URL."""
        mock_engine = MagicMock()
        mock_engine.url.host = "localhost"
        mock_build_engine.return_value = mock_engine
        url = URL.create(
            drivername="postgresql+asyncpg",
            username="test",
            password="test",
            host="localhost",
            port=5432,
        )
        server = AsyncDatabaseServer(engine=url)
        assert server.url.host == "localhost"

    @patch("elefast.asyncio._build_engine")
    def test_server_init_with_string(self, mock_build_engine):
        """Test AsyncDatabaseServer initialization with a connection string."""
        mock_engine = MagicMock()
        mock_engine.url.username = "test"
        mock_build_engine.return_value = mock_engine
        conn_string = "postgresql+asyncpg://test:test@localhost:5432/"
        server = AsyncDatabaseServer(engine=conn_string)
        assert server.url.username == "test"

    def test_server_url_property(self, mock_async_engine):
        """Test AsyncDatabaseServer.url property."""
        server = AsyncDatabaseServer(engine=mock_async_engine)
        assert server.url == mock_async_engine.url


class TestAsyncDatabaseServerEnsureReady:
    """Tests for AsyncDatabaseServer.ensure_is_ready()."""

    @pytest.mark.asyncio
    async def test_ensure_ready_success(self, mock_async_engine):
        """Test ensure_is_ready succeeds when connection works."""
        mock_connection = AsyncMock()
        mock_async_engine.connect.return_value.__aenter__ = AsyncMock(
            return_value=mock_connection
        )
        mock_async_engine.connect.return_value.__aexit__ = AsyncMock(return_value=False)

        server = AsyncDatabaseServer(engine=mock_async_engine)
        await server.ensure_is_ready(timeout=0.1, interval=0.01)

        mock_connection.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_ensure_ready_timeout(self, mock_async_engine):
        """Test ensure_is_ready raises DatabaseNotReadyError on timeout."""
        mock_async_engine.connect.side_effect = Exception("Connection refused")

        server = AsyncDatabaseServer(engine=mock_async_engine)
        with pytest.raises(DatabaseNotReadyError) as exc_info:
            await server.ensure_is_ready(timeout=0.01, interval=0.001)

        assert "timeout" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_ensure_ready_retries_then_succeeds(self, mock_async_engine):
        """Test ensure_is_ready retries and eventually succeeds."""
        mock_connection = AsyncMock()
        call_count = [0]

        class AsyncContextManagerMock:
            async def __aenter__(self):
                call_count[0] += 1
                if call_count[0] < 3:
                    raise Exception("Connection refused")
                return mock_connection

            async def __aexit__(self, *args):
                return False

        mock_async_engine.connect.return_value = AsyncContextManagerMock()

        server = AsyncDatabaseServer(engine=mock_async_engine)
        await server.ensure_is_ready(timeout=0.5, interval=0.05)

        assert call_count[0] >= 3


class TestAsyncDatabaseServerCreateDatabase:
    """Tests for AsyncDatabaseServer.create_database()."""

    @pytest.mark.asyncio
    @patch("elefast.asyncio._prepare_async_database")
    async def test_create_database_without_metadata(
        self, mock_prepare, mock_async_engine
    ):
        """Test creating a database without metadata."""
        mock_new_engine = MagicMock()
        mock_new_engine.url.database = "elefast-test-123"
        mock_new_engine.dispose = AsyncMock()
        mock_prepare.return_value = mock_new_engine

        server = AsyncDatabaseServer(engine=mock_async_engine)
        db = await server.create_database(prefix="elefast-test")

        assert isinstance(db, AsyncDatabase)
        assert db.name == "elefast-test-123"
        assert mock_prepare.call_count == 2  # Template + actual DB

    @pytest.mark.asyncio
    @patch("elefast.asyncio._prepare_async_database")
    async def test_create_database_with_metadata(
        self, mock_prepare, mock_async_engine, sample_metadata
    ):
        """Test creating a database with metadata creates template first."""
        mock_new_engine = MagicMock()
        mock_new_engine.url.database = "elefast-db-123"
        mock_new_engine.dispose = AsyncMock()
        mock_prepare.return_value = mock_new_engine

        server = AsyncDatabaseServer(engine=mock_async_engine, metadata=sample_metadata)
        db = await server.create_database(prefix="elefast-db")

        assert isinstance(db, AsyncDatabase)
        assert mock_prepare.call_count == 2

    @pytest.mark.asyncio
    @patch("elefast.asyncio._prepare_async_database")
    async def test_create_database_uses_template(
        self, mock_prepare, mock_async_engine, sample_metadata
    ):
        """Test subsequent databases use the template."""
        mock_new_engine = MagicMock()
        mock_new_engine.url.database = "elefast-db-123"
        mock_new_engine.dispose = AsyncMock()
        mock_prepare.return_value = mock_new_engine

        server = AsyncDatabaseServer(engine=mock_async_engine, metadata=sample_metadata)

        # First database - creates template
        _ = await server.create_database(prefix="elefast-db")

        # Reset mock to track second call
        mock_prepare.reset_mock()
        mock_prepare.return_value = mock_new_engine

        # Second database - should reuse template
        _ = await server.create_database(prefix="elefast-db")

        # Only one call for the actual DB (template already exists)
        mock_prepare.assert_called_once()
        call_kwargs = mock_prepare.call_args[1]
        assert call_kwargs.get("template") is not None

    @pytest.mark.asyncio
    @patch("elefast.asyncio._prepare_async_database")
    async def test_create_database_with_custom_schemas(
        self, mock_prepare, mock_async_engine, sample_metadata_with_schema
    ):
        """Test creating a database with metadata that has custom schemas."""
        mock_new_engine = MagicMock()
        mock_new_engine.url.database = "elefast-db-123"
        mock_new_engine.dispose = AsyncMock()
        mock_prepare.return_value = mock_new_engine

        server = AsyncDatabaseServer(
            engine=mock_async_engine, metadata=sample_metadata_with_schema
        )
        db = await server.create_database(prefix="elefast-db")

        assert isinstance(db, AsyncDatabase)


class TestAsyncDatabaseServerDropDatabase:
    """Tests for AsyncDatabaseServer.drop_database()."""

    @pytest.mark.asyncio
    async def test_drop_database(self, mock_async_engine):
        """Test dropping a database."""
        mock_connection = AsyncMock()
        mock_async_engine.begin.return_value.__aenter__ = AsyncMock(
            return_value=mock_connection
        )
        mock_async_engine.begin.return_value.__aexit__ = AsyncMock(return_value=False)

        server = AsyncDatabaseServer(engine=mock_async_engine)
        await server.drop_database("test_db_to_drop")

        mock_connection.execute.assert_awaited_once()
        call_args = mock_connection.execute.call_args[0][0]
        assert "DROP DATABASE" in str(call_args)
        assert "test_db_to_drop" in str(call_args)


class TestPrepareAsyncDatabase:
    """Tests for the _prepare_async_database function."""

    @pytest.mark.asyncio
    @patch("elefast.asyncio.create_async_engine")
    async def test_prepare_database_without_template(
        self, mock_create_engine, mock_async_engine
    ):
        """Test _prepare_async_database without a template."""
        mock_connection = AsyncMock()
        mock_async_engine.begin.return_value.__aenter__ = AsyncMock(
            return_value=mock_connection
        )
        mock_async_engine.begin.return_value.__aexit__ = AsyncMock(return_value=False)

        mock_new_engine = MagicMock()
        mock_create_engine.return_value = mock_new_engine

        result = await _prepare_async_database(
            mock_async_engine, prefix="test", encoding="utf8"
        )

        assert result is mock_new_engine
        mock_connection.execute.assert_awaited_once()
        call_args = mock_connection.execute.call_args[0][0]
        assert "CREATE DATABASE" in str(call_args)
        assert "TEMPLATE template0" in str(call_args)

    @pytest.mark.asyncio
    @patch("elefast.asyncio.create_async_engine")
    async def test_prepare_database_with_template(
        self, mock_create_engine, mock_async_engine
    ):
        """Test _prepare_async_database with a template."""
        mock_connection = AsyncMock()
        mock_async_engine.begin.return_value.__aenter__ = AsyncMock(
            return_value=mock_connection
        )
        mock_async_engine.begin.return_value.__aexit__ = AsyncMock(return_value=False)

        mock_new_engine = MagicMock()
        mock_create_engine.return_value = mock_new_engine

        result = await _prepare_async_database(
            mock_async_engine, prefix="test", encoding="utf8", template="my_template"
        )

        assert result is mock_new_engine
        call_args = mock_connection.execute.call_args[0][0]
        assert "WITH TEMPLATE" in str(call_args)
        assert "my_template" in str(call_args)
