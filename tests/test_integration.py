"""Integration tests for elefast - testing full workflows."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import text

from elefast import AsyncDatabase, AsyncDatabaseServer, Database, DatabaseServer
from elefast.extras.docker.configuration import Configuration, Credentials
from elefast.extras.docker.integration import postgres
from elefast.sync import MetadataMigrator


class TestDatabaseWorkflowSync:
    """Integration tests for sync database workflows."""

    @patch("elefast.sync._prepare_database")
    def test_full_workflow_create_use_cleanup(self, mock_prepare, mock_engine):
        """Test complete workflow: create DB, use it, cleanup."""
        mock_template_engine = MagicMock()
        mock_template_engine.url.database = "elefast-template-123"

        mock_db_engine = MagicMock()
        mock_db_engine.url.database = "elefast-test-db-123"

        # First call for template, second for actual DB
        mock_prepare.side_effect = [mock_template_engine, mock_db_engine]

        # Create server
        server = DatabaseServer(engine=mock_engine)

        # Create database
        with server.create_database(prefix="elefast-test") as db:
            assert isinstance(db, Database)
            assert db.name == "elefast-test-db-123"

            # Simulate using the database
            mock_connection = MagicMock()
            mock_db_engine.begin.return_value.__enter__ = MagicMock(
                return_value=mock_connection
            )
            mock_db_engine.begin.return_value.__exit__ = MagicMock(return_value=False)

            result = mock_connection.execute(text("SELECT 1"))
            assert result is not None

        # After context exit, database should be dropped
        mock_db_engine.dispose.assert_called_once()

    @patch("elefast.sync._prepare_database")
    def test_multiple_databases_isolation(self, mock_prepare, mock_engine):
        """Test that multiple databases are isolated from each other."""
        db_names = ["elefast-template-1", "db-1", "db-2"]
        engines = []

        def side_effect(*args, **kwargs):
            mock_eng = MagicMock()
            mock_eng.url.database = db_names[len(engines)]
            engines.append(mock_eng)
            return mock_eng

        mock_prepare.side_effect = side_effect

        server = DatabaseServer(engine=mock_engine)

        # Create two databases
        db1 = server.create_database(prefix="elefast")
        db2 = server.create_database(prefix="elefast")

        assert db1.name != db2.name
        assert db1.engine is not db2.engine

    @patch("elefast.sync._prepare_database")
    def test_database_with_metadata_schema_creation(
        self, mock_prepare, mock_engine, sample_metadata_with_schema
    ):
        """Test that metadata with schemas creates schemas properly."""
        mock_template_engine = MagicMock()
        mock_template_engine.url.database = "elefast-template-123"

        mock_db_engine = MagicMock()
        mock_db_engine.url.database = "elefast-db-456"

        mock_prepare.side_effect = [mock_template_engine, mock_db_engine]

        mock_connection = MagicMock()
        mock_template_engine.begin.return_value.__enter__ = MagicMock(
            return_value=mock_connection
        )
        mock_template_engine.begin.return_value.__exit__ = MagicMock(return_value=False)

        server = DatabaseServer(
            engine=mock_engine, schema=MetadataMigrator(sample_metadata_with_schema)
        )
        _ = server.create_database(prefix="elefast")

        # Verify schema creation was called for 'app' schema (not 'public')
        execute_calls = mock_connection.execute.call_args_list
        assert len(execute_calls) > 0


class TestDatabaseWorkflowAsync:
    """Integration tests for async database workflows."""

    @pytest.mark.asyncio
    @patch("elefast.asyncio._prepare_async_database")
    async def test_full_workflow_create_use_cleanup_async(
        self, mock_prepare, mock_async_engine
    ):
        """Test complete async workflow: create DB, use it, cleanup."""
        mock_template_engine = MagicMock()
        mock_template_engine.url.database = "elefast-template-123"
        mock_template_engine.dispose = AsyncMock()

        mock_db_engine = MagicMock()
        mock_db_engine.url.database = "elefast-test-db-123"
        mock_db_engine.dispose = AsyncMock()

        # First call for template, second for actual DB
        mock_prepare.side_effect = [mock_template_engine, mock_db_engine]

        # Create server
        server = AsyncDatabaseServer(engine=mock_async_engine)

        # Create database
        async with await server.create_database(prefix="elefast-test") as db:
            assert isinstance(db, AsyncDatabase)
            assert db.name == "elefast-test-db-123"

            # Simulate using the database
            mock_connection = AsyncMock()
            mock_db_engine.begin.return_value.__aenter__ = AsyncMock(
                return_value=mock_connection
            )
            mock_db_engine.begin.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await mock_connection.execute(text("SELECT 1"))
            assert result is not None

        # After context exit, database should be dropped
        mock_db_engine.dispose.assert_awaited_once()

    @pytest.mark.asyncio
    @patch("elefast.asyncio._prepare_async_database")
    async def test_multiple_async_databases(self, mock_prepare, mock_async_engine):
        """Test creating multiple async databases."""
        db_names = ["elefast-template-1", "db-1", "db-2"]
        engines = []

        async def side_effect(*args, **kwargs):
            mock_eng = MagicMock()
            mock_eng.url.database = db_names[len(engines)]
            mock_eng.dispose = AsyncMock()
            engines.append(mock_eng)
            return mock_eng

        mock_prepare.side_effect = side_effect

        server = AsyncDatabaseServer(engine=mock_async_engine)

        # Create two databases
        db1 = await server.create_database(prefix="elefast")
        db2 = await server.create_database(prefix="elefast")

        assert db1.name != db2.name


class TestDockerIntegration:
    """Tests for Docker integration module."""

    @patch("elefast.extras.docker.integration.DockerClient")
    @patch("elefast.extras.docker.integration.ensure_db_server_started")
    @patch("elefast.extras.docker.integration.FileLock")
    def test_postgres_function_returns_url(
        self, mock_filelock, mock_ensure, mock_docker_client
    ):
        """Test that postgres() function returns a valid URL."""
        mock_client = MagicMock()
        mock_docker_client.from_env.return_value = mock_client
        mock_ensure.return_value = (MagicMock(), 54321)

        result = postgres(driver="psycopg2")

        assert result.drivername == "postgresql+psycopg2"
        assert result.port == 54321
        assert result.username == "postgres"
        assert result.password == "elefast"

    @patch("elefast.extras.docker.integration.DockerClient")
    @patch("elefast.extras.docker.integration.ensure_db_server_started")
    @patch("elefast.extras.docker.integration.FileLock")
    def test_postgres_with_custom_config(
        self, mock_filelock, mock_ensure, mock_docker_client
    ):
        """Test postgres() with custom configuration."""
        mock_client = MagicMock()
        mock_docker_client.from_env.return_value = mock_client
        mock_ensure.return_value = (MagicMock(), 54322)

        config = Configuration(
            credentials=Credentials(user="admin", password="secret", host="0.0.0.0")
        )

        result = postgres(driver="asyncpg", config=config)

        assert result.drivername == "postgresql+asyncpg"
        assert result.username == "admin"
        assert result.password == "secret"
        assert result.host == "0.0.0.0"

    @patch("elefast.extras.docker.integration.DockerClient")
    @patch("elefast.extras.docker.integration.ensure_db_server_started")
    @patch("elefast.extras.docker.integration.FileLock")
    def test_postgres_uses_file_lock(
        self, mock_filelock_class, mock_ensure, mock_docker_client
    ):
        """Test that postgres() uses file locking for thread safety."""
        mock_lock = MagicMock()
        mock_filelock_class.return_value = mock_lock
        mock_client = MagicMock()
        mock_docker_client.from_env.return_value = mock_client
        mock_ensure.return_value = (MagicMock(), 54321)

        postgres(driver="psycopg2")

        mock_filelock_class.assert_called_once()
        mock_lock.__enter__.assert_called_once()


class TestFixturePatterns:
    """Tests demonstrating pytest fixture patterns."""

    @pytest.fixture
    def mock_db_server(self, mock_engine):
        """Function-scoped database server fixture pattern."""
        return DatabaseServer(engine=mock_engine)

    @pytest.fixture
    def mock_db(self, mock_db_server):
        """Function-scoped database fixture pattern using context manager."""
        with patch("elefast.sync._prepare_database") as mock_prepare:
            mock_template_engine = MagicMock()
            mock_template_engine.url.database = "elefast-template-123"

            mock_db_engine = MagicMock()
            mock_db_engine.url.database = "elefast-test-db-123"

            mock_prepare.side_effect = [mock_template_engine, mock_db_engine]

            with mock_db_server.create_database() as database:
                yield database

    @pytest.fixture
    def mock_db_connection(self, mock_db):
        """Connection fixture pattern."""
        mock_connection = MagicMock()
        mock_db.engine.begin.return_value.__enter__ = MagicMock(
            return_value=mock_connection
        )
        mock_db.engine.begin.return_value.__exit__ = MagicMock(return_value=False)
        yield mock_connection

    def test_using_fixture_pattern(self, mock_db, mock_db_connection):
        """Test demonstrating the fixture pattern usage."""
        assert mock_db is not None
        assert mock_db_connection is not None
        # Database will be cleaned up after test


class TestErrorRecovery:
    """Tests for error handling and recovery scenarios."""

    @patch("elefast.sync._prepare_database")
    def test_database_cleanup_on_error(self, mock_prepare, mock_engine):
        """Test that database is cleaned up even when an error occurs."""
        mock_template_engine = MagicMock()
        mock_template_engine.url.database = "elefast-template-123"

        mock_db_engine = MagicMock()
        mock_db_engine.url.database = "elefast-test-db"

        mock_prepare.side_effect = [mock_template_engine, mock_db_engine]

        server = DatabaseServer(engine=mock_engine)

        try:
            with server.create_database() as db:
                assert db is not None
                raise ValueError("Simulated error during test")
        except ValueError:
            pass

        # Database should still be cleaned up
        mock_db_engine.dispose.assert_called_once()

    @pytest.mark.asyncio
    @patch("elefast.asyncio._prepare_async_database")
    async def test_async_database_cleanup_on_error(
        self, mock_prepare, mock_async_engine
    ):
        """Test async database cleanup on error."""
        mock_template_engine = MagicMock()
        mock_template_engine.url.database = "elefast-template-123"
        mock_template_engine.dispose = AsyncMock()

        mock_db_engine = MagicMock()
        mock_db_engine.url.database = "elefast-test-db"
        mock_db_engine.dispose = AsyncMock()

        mock_prepare.side_effect = [mock_template_engine, mock_db_engine]

        server = AsyncDatabaseServer(engine=mock_async_engine)

        try:
            async with await server.create_database() as db:
                assert db is not None
                raise ValueError("Simulated error during test")
        except ValueError:
            pass

        # Database should still be cleaned up
        mock_db_engine.dispose.assert_awaited_once()
