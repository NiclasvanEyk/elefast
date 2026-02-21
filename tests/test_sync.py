"""Tests for the elefast.sync module."""

from unittest.mock import MagicMock, patch
import pytest
from sqlalchemy import URL

from elefast.sync import Database, DatabaseServer, _build_engine, _prepare_database
from elefast.errors import DatabaseNotReadyError


class TestBuildEngine:
    """Tests for the _build_engine function."""

    def test_build_engine_from_engine(self, mock_engine):
        """Test that _build_engine returns an Engine as-is."""
        result = _build_engine(mock_engine)
        assert result is mock_engine

    @patch("elefast.sync.create_engine")
    def test_build_engine_from_url_object(self, mock_create_engine):
        """Test _build_engine with a URL object."""
        mock_result = MagicMock()
        mock_create_engine.return_value = mock_result
        url = URL.create(
            drivername="postgresql+psycopg2",
            username="test",
            password="test",
            host="localhost",
            port=5432,
            database="test_db",
        )
        result = _build_engine(url)
        mock_create_engine.assert_called_once()
        assert result is mock_result

    @patch("elefast.sync.create_engine")
    def test_build_engine_from_string(self, mock_create_engine):
        """Test _build_engine with a connection string."""
        mock_result = MagicMock()
        mock_create_engine.return_value = mock_result
        conn_string = "postgresql+psycopg2://test:test@localhost:5432/test_db"
        result = _build_engine(conn_string)
        mock_create_engine.assert_called_once()
        assert result is mock_result

    def test_build_engine_from_invalid_type(self):
        """Test that _build_engine raises TypeError for invalid input."""
        with pytest.raises(TypeError):
            _build_engine(123)  # type: ignore


class TestDatabase:
    """Tests for the Database class."""

    def test_database_init(self, mock_engine):
        """Test Database initialization."""
        server = MagicMock(spec=DatabaseServer)
        db = Database(engine=mock_engine, server=server)

        assert db.engine is mock_engine
        assert db.server is server
        assert db.name == "test_db"

    def test_database_url_property(self, mock_engine):
        """Test Database.url property."""
        server = MagicMock(spec=DatabaseServer)
        db = Database(engine=mock_engine, server=server)

        assert db.url == mock_engine.url

    def test_database_context_manager(self, mock_engine):
        """Test Database as a context manager auto-cleans up."""
        server = MagicMock(spec=DatabaseServer)
        db = Database(engine=mock_engine, server=server)

        with db:
            pass

        server.drop_database.assert_called_once_with("test_db")
        mock_engine.dispose.assert_called_once()

    def test_database_session_creation(self, mock_engine):
        """Test Database.session() creates a session."""
        server = MagicMock(spec=DatabaseServer)
        mock_session = MagicMock()
        mock_sessionmaker = MagicMock(return_value=mock_session)
        db = Database(
            engine=mock_engine,
            server=server,
            sessionmaker_factory=lambda e: mock_sessionmaker,
        )

        session = db.session()
        assert session is mock_session

    def test_database_drop(self, mock_engine):
        """Test Database.drop() cleans up properly."""
        server = MagicMock(spec=DatabaseServer)
        db = Database(engine=mock_engine, server=server)

        db.drop()

        mock_engine.dispose.assert_called_once()
        server.drop_database.assert_called_once_with("test_db")


class TestDatabaseServer:
    """Tests for the DatabaseServer class."""

    def test_server_init_with_engine(self, mock_engine):
        """Test DatabaseServer initialization with an Engine."""
        server = DatabaseServer(engine=mock_engine)
        assert server.url == mock_engine.url

    @patch("elefast.sync._build_engine")
    def test_server_init_with_url(self, mock_build_engine):
        """Test DatabaseServer initialization with a URL."""
        mock_engine = MagicMock()
        mock_engine.url.host = "localhost"
        mock_build_engine.return_value = mock_engine
        url = URL.create(
            drivername="postgresql+psycopg2",
            username="test",
            password="test",
            host="localhost",
            port=5432,
        )
        server = DatabaseServer(engine=url)
        assert server.url.host == "localhost"

    @patch("elefast.sync._build_engine")
    def test_server_init_with_string(self, mock_build_engine):
        """Test DatabaseServer initialization with a connection string."""
        mock_engine = MagicMock()
        mock_engine.url.username = "test"
        mock_build_engine.return_value = mock_engine
        conn_string = "postgresql+psycopg2://test:test@localhost:5432/"
        server = DatabaseServer(engine=conn_string)
        assert server.url.username == "test"

    def test_server_url_property(self, mock_engine):
        """Test DatabaseServer.url property."""
        server = DatabaseServer(engine=mock_engine)
        assert server.url == mock_engine.url


class TestDatabaseServerEnsureReady:
    """Tests for DatabaseServer.ensure_is_ready()."""

    def test_ensure_ready_success(self, mock_engine):
        """Test ensure_is_ready succeeds when connection works."""
        mock_connection = MagicMock()
        mock_engine.connect.return_value.__enter__ = MagicMock(
            return_value=mock_connection
        )
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)

        server = DatabaseServer(engine=mock_engine)
        server.ensure_is_ready(timeout=0.1, interval=0.01)

        mock_connection.execute.assert_called_once()

    def test_ensure_ready_timeout(self, mock_engine):
        """Test ensure_is_ready raises DatabaseNotReadyError on timeout."""
        mock_engine.connect.side_effect = Exception("Connection refused")

        server = DatabaseServer(engine=mock_engine)
        with pytest.raises(DatabaseNotReadyError) as exc_info:
            server.ensure_is_ready(timeout=0.01, interval=0.001)

        assert "timeout" in str(exc_info.value).lower()

    def test_ensure_ready_retries_then_succeeds(self, mock_engine):
        """Test ensure_is_ready retries and eventually succeeds."""
        mock_connection = MagicMock()
        call_count = [0]

        def connect_side_effect():
            call_count[0] += 1
            if call_count[0] < 3:
                raise Exception("Connection refused")
            return mock_connection

        mock_engine.connect.side_effect = connect_side_effect

        server = DatabaseServer(engine=mock_engine)
        server.ensure_is_ready(timeout=0.5, interval=0.05)

        assert call_count[0] >= 3


class TestDatabaseServerCreateDatabase:
    """Tests for DatabaseServer.create_database()."""

    @patch("elefast.sync._prepare_database")
    def test_create_database_without_metadata(self, mock_prepare, mock_engine):
        """Test creating a database without metadata."""
        mock_new_engine = MagicMock()
        mock_new_engine.url.database = "elefast-test-123"
        mock_prepare.return_value = mock_new_engine

        server = DatabaseServer(engine=mock_engine)
        db = server.create_database(prefix="elefast-test")

        assert isinstance(db, Database)
        assert db.name == "elefast-test-123"
        assert mock_prepare.call_count == 2  # Template + actual DB

    @patch("elefast.sync._prepare_database")
    def test_create_database_with_metadata(
        self, mock_prepare, mock_engine, sample_metadata
    ):
        """Test creating a database with metadata creates template first."""
        mock_new_engine = MagicMock()
        mock_new_engine.url.database = "elefast-db-123"
        mock_prepare.return_value = mock_new_engine

        server = DatabaseServer(engine=mock_engine, metadata=sample_metadata)
        db = server.create_database(prefix="elefast-db")

        assert isinstance(db, Database)
        # First call for template, second for actual DB
        assert mock_prepare.call_count == 2

    @patch("elefast.sync._prepare_database")
    def test_create_database_uses_template(
        self, mock_prepare, mock_engine, sample_metadata
    ):
        """Test subsequent databases use the template."""
        mock_new_engine = MagicMock()
        mock_new_engine.url.database = "elefast-db-123"
        mock_prepare.return_value = mock_new_engine

        server = DatabaseServer(engine=mock_engine, metadata=sample_metadata)

        # First database - creates template
        _ = server.create_database(prefix="elefast-db")

        # Reset mock to track second call
        mock_prepare.reset_mock()
        mock_prepare.return_value = mock_new_engine

        # Second database - should reuse template
        _ = server.create_database(prefix="elefast-db")

        # Only one call for the actual DB (template already exists)
        mock_prepare.assert_called_once()
        call_kwargs = mock_prepare.call_args[1]
        assert call_kwargs.get("template") is not None


class TestDatabaseServerDropDatabase:
    """Tests for DatabaseServer.drop_database()."""

    def test_drop_database(self, mock_engine):
        """Test dropping a database."""
        mock_connection = MagicMock()
        mock_engine.begin.return_value.__enter__ = MagicMock(
            return_value=mock_connection
        )
        mock_engine.begin.return_value.__exit__ = MagicMock(return_value=False)

        server = DatabaseServer(engine=mock_engine)
        server.drop_database("test_db_to_drop")

        mock_connection.execute.assert_called_once()
        call_args = mock_connection.execute.call_args[0][0]
        assert "DROP DATABASE" in str(call_args)
        assert "test_db_to_drop" in str(call_args)


class TestPrepareDatabase:
    """Tests for the _prepare_database function."""

    @patch("elefast.sync.create_engine")
    def test_prepare_database_without_template(self, mock_create_engine, mock_engine):
        """Test _prepare_database without a template."""
        mock_connection = MagicMock()
        mock_engine.begin.return_value.__enter__ = MagicMock(
            return_value=mock_connection
        )
        mock_engine.begin.return_value.__exit__ = MagicMock(return_value=False)

        mock_new_engine = MagicMock()
        mock_create_engine.return_value = mock_new_engine

        result = _prepare_database(mock_engine, prefix="test", encoding="utf8")

        assert result is mock_new_engine
        mock_connection.execute.assert_called_once()
        call_args = mock_connection.execute.call_args[0][0]
        assert "CREATE DATABASE" in str(call_args)
        assert "TEMPLATE template0" in str(call_args)

    @patch("elefast.sync.create_engine")
    def test_prepare_database_with_template(self, mock_create_engine, mock_engine):
        """Test _prepare_database with a template."""
        mock_connection = MagicMock()
        mock_engine.begin.return_value.__enter__ = MagicMock(
            return_value=mock_connection
        )
        mock_engine.begin.return_value.__exit__ = MagicMock(return_value=False)

        mock_new_engine = MagicMock()
        mock_create_engine.return_value = mock_new_engine

        result = _prepare_database(
            mock_engine, prefix="test", encoding="utf8", template="my_template"
        )

        assert result is mock_new_engine
        call_args = mock_connection.execute.call_args[0][0]
        assert "WITH TEMPLATE" in str(call_args)
        assert "my_template" in str(call_args)
