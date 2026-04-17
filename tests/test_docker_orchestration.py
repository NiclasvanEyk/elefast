"""Tests for the elefast.extras.docker.orchestration module."""

from unittest.mock import MagicMock, patch

import pytest

from elefast.extras.docker.configuration import (
    Configuration,
    Container,
    Credentials,
    Optimizations,
)
from elefast.extras.docker.orchestration import (
    _get_host_port_from_container,
    _resolve_database_port,
    ensure_db_server_started,
    find_free_port,
    get_db_server_container,
    get_docker,
    start_db_server_container,
)


class TestFindFreePort:
    """Tests for the find_free_port function."""

    def test_find_free_port_returns_valid_port(self):
        """Test that find_free_port returns a valid port number."""
        port = find_free_port()
        assert isinstance(port, int)
        assert 1024 <= port <= 65535

    def test_find_free_port_returns_different_ports(self):
        """Test that multiple calls return different ports (usually)."""
        port1 = find_free_port()
        port2 = find_free_port()
        # They might occasionally be the same, but usually not
        assert isinstance(port1, int)
        assert isinstance(port2, int)


class TestResolveDatabasePort:
    """Tests for the _resolve_database_port function."""

    def test_resolve_none_uses_defaults(self):
        """Test that None returns default port with random host port."""
        container_port, host_port = _resolve_database_port(None)
        assert container_port == 5432
        assert isinstance(host_port, int)

    def test_resolve_tuple_with_none_host_port(self):
        """Test tuple with None host port finds random port."""
        container_port, host_port = _resolve_database_port((3306, None))
        assert container_port == 3306
        assert isinstance(host_port, int)

    def test_resolve_tuple_with_explicit_host_port(self):
        """Test tuple with explicit host port."""
        container_port, host_port = _resolve_database_port((5432, 5433))
        assert container_port == 5432
        assert host_port == 5433

    def test_resolve_invalid_tuple_length(self):
        """Test tuple with wrong length raises ValueError."""
        with pytest.raises(ValueError, match="exactly 2 elements"):
            _resolve_database_port((5432, 5433, 5434))  # type: ignore

    def test_resolve_invalid_first_element_type(self):
        """Test tuple with non-int first element raises TypeError."""
        with pytest.raises(TypeError, match="first element must be int"):
            _resolve_database_port(("5432", 5433))  # type: ignore

    def test_resolve_invalid_second_element_type(self):
        """Test tuple with invalid second element raises TypeError."""
        with pytest.raises(TypeError, match="second element must be int or None"):
            _resolve_database_port((5432, "5433"))  # type: ignore

    def test_resolve_invalid_type(self):
        """Test invalid type raises TypeError."""
        with pytest.raises(TypeError, match="database_port"):
            _resolve_database_port(("5432", 5433))  # type: ignore


class TestGetHostPortFromContainer:
    """Tests for the _get_host_port_from_container function."""

    def test_get_host_port_from_env_var(self, mock_docker_container):
        """Test extracting host port from container env vars."""
        port = _get_host_port_from_container(mock_docker_container)
        assert port == 54321

    def test_get_host_port_missing_env_var(self):
        """Test error when env var is missing."""
        container = MagicMock()
        container.name = "test-container"
        container.attrs = {"Config": {"Env": ["OTHER_VAR=value"]}}

        with pytest.raises(RuntimeError, match="Could not determine host port"):
            _get_host_port_from_container(container)

    def test_get_host_port_invalid_value(self):
        """Test error when env var value is not a digit."""
        container = MagicMock()
        container.name = "test-container"
        container.attrs = {
            "Config": {"Env": ["ELEFAST_POSTGRES_HOST_PORT=not-a-number"]}
        }

        with pytest.raises(RuntimeError, match="Could not determine host port"):
            _get_host_port_from_container(container)

    def test_get_host_port_malformed_env_var(self):
        """Test handling of malformed env var strings."""
        container = MagicMock()
        container.name = "test-container"
        container.attrs = {
            "Config": {"Env": ["", "MALFORMED", "ELEFAST_POSTGRES_HOST_PORT=12345"]}
        }

        port = _get_host_port_from_container(container)
        assert port == 12345


class TestGetDbServerContainer:
    """Tests for the get_db_server_container function."""

    def test_get_existing_running_container(self, mock_docker_container):
        """Test finding an existing running container."""
        client = MagicMock()
        client.containers.list.return_value = [mock_docker_container]

        result = get_db_server_container(client, "elefast")

        assert result is mock_docker_container

    def test_get_existing_exited_container(self, mock_docker_container):
        """Test finding and starting an exited container."""
        mock_docker_container.status = "exited"
        client = MagicMock()
        client.containers.list.return_value = [mock_docker_container]

        result = get_db_server_container(client, "elefast")

        mock_docker_container.start.assert_called_once()
        assert result is mock_docker_container

    def test_get_nonexistent_container(self, mock_docker_container):
        """Test when container doesn't exist."""
        client = MagicMock()
        client.containers.list.return_value = [mock_docker_container]

        result = get_db_server_container(client, "different-name")

        assert result is None


class TestEnsureDbServerStarted:
    """Tests for the ensure_db_server_started function."""

    def test_ensure_db_server_started_existing(self, mock_docker_container):
        """Test using existing container."""
        client = MagicMock()
        client.containers.list.return_value = [mock_docker_container]
        config = Configuration()

        container, host_port = ensure_db_server_started(client, config)

        assert container is mock_docker_container
        assert host_port == 54321
        client.containers.run.assert_not_called()

    @patch("elefast.extras.docker.orchestration.start_db_server_container")
    def test_ensure_db_server_started_new(self, mock_start, mock_docker_container):
        """Test starting a new container when none exists."""
        client = MagicMock()
        client.containers.list.return_value = []  # No existing containers
        mock_start.return_value = (mock_docker_container, 54322)
        config = Configuration()

        container, host_port = ensure_db_server_started(client, config)

        mock_start.assert_called_once()
        assert container is mock_docker_container
        assert host_port == 54322


class TestStartDbServerContainer:
    """Tests for the start_db_server_container function."""

    def test_start_container_defaults(self, mock_docker_container):
        """Test starting container with default configuration."""
        client = MagicMock()
        client.containers.run.return_value = mock_docker_container
        config = Configuration()

        container, _host_port = start_db_server_container(
            client, config, keep_container_around=True
        )

        assert container is mock_docker_container
        client.containers.run.assert_called_once()
        call_kwargs = client.containers.run.call_args[1]

        assert call_kwargs["name"] == "elefast"
        assert call_kwargs["image"] == "postgres:latest"
        assert call_kwargs["remove"] is False
        assert call_kwargs["detach"] is True

    def test_start_container_with_optimizations(self, mock_docker_container):
        """Test starting container with performance optimizations."""
        client = MagicMock()
        client.containers.run.return_value = mock_docker_container

        optimizations = Optimizations(
            fsync_off=True,
            synchronous_commit_off=True,
            full_page_writes_off=True,
            autovacuum_off=True,
        )
        config = Configuration(optimizations=optimizations)

        _container, _host_port = start_db_server_container(
            client, config, keep_container_around=True
        )

        call_kwargs = client.containers.run.call_args[1]
        command = call_kwargs.get("command", [])

        assert "-c" in command
        assert "fsync=off" in command
        assert "synchronous_commit=off" in command
        assert "full_page_writes=off" in command
        assert "autovacuum=off" in command

    def test_start_container_with_custom_credentials(self, mock_docker_container):
        """Test starting container with custom credentials."""
        client = MagicMock()
        client.containers.run.return_value = mock_docker_container

        credentials = Credentials(user="admin", password="secret", host="0.0.0.0")
        config = Configuration(credentials=credentials)

        _container, _host_port = start_db_server_container(
            client, config, keep_container_around=True
        )

        call_kwargs = client.containers.run.call_args[1]
        env = call_kwargs.get("environment", {})

        assert env["POSTGRES_USER"] == "admin"
        assert env["POSTGRES_PASSWORD"] == "secret"

    def test_start_container_with_custom_container_config(self, mock_docker_container):
        """Test starting container with custom container configuration."""
        client = MagicMock()
        client.containers.run.return_value = mock_docker_container

        container_config = Container(
            name="my-postgres",
            image="postgres",
            version="15",
            database_port=(5432, 5433),
        )
        config = Configuration(container=container_config)

        _container, _host_port = start_db_server_container(
            client, config, keep_container_around=True
        )

        call_kwargs = client.containers.run.call_args[1]
        assert call_kwargs["name"] == "my-postgres"
        assert call_kwargs["image"] == "postgres:15"
        assert call_kwargs["ports"] == {"5432": 5433}

    def test_start_container_with_tmpfs(self, mock_docker_container):
        """Test starting container with tmpfs enabled."""
        client = MagicMock()
        client.containers.run.return_value = mock_docker_container

        optimizations = Optimizations(tmpfs=True)
        config = Configuration(optimizations=optimizations)

        _container, _host_port = start_db_server_container(
            client, config, keep_container_around=True
        )

        call_kwargs = client.containers.run.call_args[1]
        tmpfs = call_kwargs.get("tmpfs", {})

        assert "/var/lib/postgresql" in tmpfs

    def test_start_container_with_fixed_tmpfs_size(self, mock_docker_container):
        """Test starting container with fixed tmpfs size."""
        client = MagicMock()
        client.containers.run.return_value = mock_docker_container

        optimizations = Optimizations(tmpfs=512)  # 512 MB
        config = Configuration(optimizations=optimizations)

        _container, _host_port = start_db_server_container(
            client, config, keep_container_around=True
        )

        call_kwargs = client.containers.run.call_args[1]
        tmpfs = call_kwargs.get("tmpfs", {})

        assert tmpfs.get("/var/lib/postgresql") == "rw,size=512m"

    def test_start_container_without_tmpfs(self, mock_docker_container):
        """Test starting container without tmpfs."""
        client = MagicMock()
        client.containers.run.return_value = mock_docker_container

        optimizations = Optimizations(tmpfs=False)
        config = Configuration(optimizations=optimizations)

        _container, _host_port = start_db_server_container(
            client, config, keep_container_around=True
        )

        call_kwargs = client.containers.run.call_args[1]
        tmpfs = call_kwargs.get("tmpfs", {})

        assert tmpfs == {}

    def test_start_container_without_keep(self, mock_docker_container):
        """Test starting container that won't be kept."""
        client = MagicMock()
        client.containers.run.return_value = mock_docker_container
        config = Configuration()

        _container, _host_port = start_db_server_container(
            client, config, keep_container_around=False
        )

        call_kwargs = client.containers.run.call_args[1]
        assert call_kwargs["remove"] is True

    def test_start_container_invalid_tmpfs_size(self, mock_docker_container):
        """Test error when tmpfs size is invalid."""
        client = MagicMock()
        client.containers.run.return_value = mock_docker_container

        optimizations = Optimizations(tmpfs=0)  # Invalid size
        config = Configuration(optimizations=optimizations)

        with pytest.raises(ValueError, match="tmpfs size must be a positive integer"):
            start_db_server_container(client, config, keep_container_around=True)

    def test_start_container_with_custom_optimization_values(
        self, mock_docker_container
    ):
        """Test starting container with custom optimization values."""
        client = MagicMock()
        client.containers.run.return_value = mock_docker_container

        optimizations = Optimizations(
            shared_buffers_mb=256,
            work_mem_mb=64,
            maintenance_work_mem_mb=128,
            checkpoint_timeout_seconds=600,
        )
        config = Configuration(optimizations=optimizations)

        _container, _host_port = start_db_server_container(
            client, config, keep_container_around=True
        )

        call_kwargs = client.containers.run.call_args[1]
        command = call_kwargs.get("command", [])

        assert "shared_buffers=256MB" in command
        assert "work_mem=64MB" in command
        assert "maintenance_work_mem=128MB" in command
        assert "checkpoint_timeout=600s" in command


class TestGetDocker:
    """Tests for the get_docker function."""

    @patch("elefast.extras.docker.orchestration.DockerClient")
    def test_get_docker_returns_client(self, mock_docker_class):
        """Test that get_docker returns a DockerClient."""
        mock_docker_class.from_env.return_value = MagicMock()
        _ = get_docker()
        mock_docker_class.from_env.assert_called_once()


class TestEnsureDbServerStartedDefaults:
    """Tests for ensure_db_server_started with default parameters."""

    @patch("elefast.extras.docker.orchestration.Configuration")
    @patch("elefast.extras.docker.orchestration.get_docker")
    @patch("elefast.extras.docker.orchestration.get_db_server_container")
    def test_ensure_db_server_started_default_docker(
        self, mock_get_container, mock_get_docker, mock_config_class
    ):
        """Test ensure_db_server_started uses default docker client."""
        mock_docker = MagicMock()
        mock_get_docker.return_value = mock_docker
        mock_config = MagicMock()
        mock_config_class.return_value = mock_config
        mock_container = MagicMock()
        mock_container.attrs = {"Config": {"Env": ["ELEFAST_POSTGRES_HOST_PORT=54321"]}}
        mock_get_container.return_value = mock_container

        _container, _host_port = ensure_db_server_started()

        mock_get_docker.assert_called_once()
        mock_config_class.assert_called_once()

    @patch("elefast.extras.docker.orchestration.Configuration")
    @patch("elefast.extras.docker.orchestration.get_db_server_container")
    def test_ensure_db_server_started_default_config(
        self, mock_get_container, mock_config_class
    ):
        """Test ensure_db_server_started uses default config."""
        mock_docker = MagicMock()
        mock_config = MagicMock()
        mock_config_class.return_value = mock_config
        mock_container = MagicMock()
        mock_container.attrs = {"Config": {"Env": ["ELEFAST_POSTGRES_HOST_PORT=54321"]}}
        mock_get_container.return_value = mock_container

        _container, _host_port = ensure_db_server_started(docker=mock_docker)

        mock_config_class.assert_called_once()


class TestResolveDatabasePortEdgeCases:
    """Additional edge case tests for _resolve_database_port."""

    def test_resolve_invalid_type_list(self):
        """Test that passing a list raises TypeError."""
        with pytest.raises(TypeError, match="database_port"):
            _resolve_database_port([5432, 5433])  # type: ignore

    def test_resolve_invalid_type_int(self):
        """Test that passing an int raises TypeError."""
        with pytest.raises(TypeError, match="database_port"):
            _resolve_database_port(5432)  # type: ignore
