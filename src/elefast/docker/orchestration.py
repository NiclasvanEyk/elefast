import socket
from typing import cast

from docker import DockerClient
from docker.models.containers import Container

from elefast.docker.configuration import Configuration


def get_docker() -> DockerClient:
    return DockerClient.from_env()


def find_free_port() -> int:
    """Find a random free port on the host system."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


def _resolve_database_port(
    database_port: tuple[int, int | None] | None,
) -> tuple[int, int]:
    if database_port is None:
        return 5432, find_free_port()
    if isinstance(database_port, tuple):
        if len(database_port) != 2:
            raise ValueError(
                f"database_port tuple must have exactly 2 elements, got {len(database_port)}"
            )
        container_port, host_port_or_none = database_port
        if not isinstance(container_port, int):
            raise TypeError(
                f"database_port tuple first element must be int, got {type(container_port).__name__}"
            )
        if host_port_or_none is None:
            return container_port, find_free_port()
        if isinstance(host_port_or_none, int):
            return container_port, host_port_or_none
        raise TypeError(
            f"database_port tuple second element must be int or None, got {type(host_port_or_none).__name__}"
        )
    raise TypeError(
        f"database_port must be tuple[int, int | None] or None, got {type(database_port).__name__}"
    )


def ensure_db_server_started(
    docker: DockerClient | None = None,
    config: Configuration | None = None,
    keep_container_around: bool = False,
) -> tuple[Container, int]:
    """Start or retrieve the database server container.

    Returns:
        Tuple of (container, host_port) where host_port is the actual exposed port on the host
    """
    if docker is None:
        docker = get_docker()
    if config is None:
        config = Configuration()

    if container := get_db_server_container(docker, config.container.name):
        # Extract the host port from existing container
        host_port = _get_host_port_from_container(container)
        return container, host_port
    return start_db_server_container(docker, config, keep_container_around)


def _get_host_port_from_container(container: Container) -> int:
    env_vars = (container.attrs or {}).get("Config", {}).get("Env", [])
    for env_var_str in env_vars:
        if (
            not isinstance(env_var_str, str)
            or not env_var_str
            or "=" not in env_var_str
        ):
            continue

        name, value = cast(tuple[str, str], env_var_str.split("=", 1))
        if name != "ELEFAST_POSTGRES_HOST_PORT" or not value.isdigit():
            continue

        return int(value)

    raise RuntimeError(f"Could not determine host port from container {container.name}")


def get_db_server_container(docker: DockerClient, name: str) -> Container | None:
    containers = cast(list[Container], docker.containers.list(all=True))
    for container in containers:
        if container.name == name:
            if container.status == "exited":
                container.start()
            return container


def start_db_server_container(
    docker: DockerClient, config: Configuration, keep_container_around: bool
) -> tuple[Container, int]:
    optimizations = config.optimizations
    command: list[str] = []
    env: dict[str, str] = {
        "POSTGRES_USER": config.credentials.user,
        "POSTGRES_PASSWORD": config.credentials.password,
        "POSTGRES_INITDB_ARGS": "--encoding=UTF8 --locale=en_US.UTF-8",
    }

    if optimizations.fsync_off:
        command += ["-c", "fsync=off"]
    if optimizations.synchronous_commit_off:
        command += ["-c", "synchronous_commit=off"]
    if optimizations.full_page_writes_off:
        command += ["-c", "full_page_writes=off"]
    if optimizations.wal_level_minimal:
        command += ["-c", "wal_level=minimal"]
    if optimizations.disable_wal_senders:
        command += ["-c", "max_wal_senders=0"]
    if optimizations.disable_archiving:
        command += ["-c", "archive_mode=off"]
    if optimizations.autovacuum_off:
        command += ["-c", "autovacuum=off"]
    else:
        # Enable autovacuum with aggressive settings to prevent table bloat
        command += ["-c", "autovacuum=on"]
        command += ["-c", "autovacuum_naptime=10s"]
        command += ["-c", "autovacuum_vacuum_scale_factor=0.01"]
        command += ["-c", "autovacuum_analyze_scale_factor=0.005"]
    if optimizations.jit_off:
        command += ["-c", "jit=off"]
    if optimizations.checkpoint_timeout_seconds is not None:
        command += [
            "-c",
            f"checkpoint_timeout={optimizations.checkpoint_timeout_seconds}s",
        ]
    if optimizations.disable_statement_logging:
        command += ["-c", "log_min_duration_statement=-1"]
    if optimizations.shared_buffers_mb is not None:
        command += ["-c", f"shared_buffers={optimizations.shared_buffers_mb}MB"]
    if optimizations.work_mem_mb is not None:
        command += ["-c", f"work_mem={optimizations.work_mem_mb}MB"]
    if optimizations.maintenance_work_mem_mb is not None:
        command += [
            "-c",
            f"maintenance_work_mem={optimizations.maintenance_work_mem_mb}MB",
        ]

    # Resolve database port configuration
    container_port, host_port = _resolve_database_port(config.container.database_port)

    # Set environment variable with the actual host port for database connection
    env["ELEFAST_POSTGRES_HOST_PORT"] = str(host_port)

    # Configure tmpfs mount
    tmpfs_config = {}
    if isinstance(optimizations.tmpfs, bool):
        if optimizations.tmpfs:
            # Auto-size: Docker will use 50% of host RAM by default
            tmpfs_config["/var/lib/postgresql"] = "rw"
        # else: False means no tmpfs, tmpfs_config stays empty
    else:
        # Must be an integer
        if optimizations.tmpfs <= 0:
            raise ValueError(
                f"tmpfs size must be a positive integer or a boolean, got {optimizations.tmpfs}"
            )
        # Fixed size in MB
        tmpfs_config["/var/lib/postgresql"] = f"rw,size={optimizations.tmpfs}m"

    container = docker.containers.run(
        image=f"{config.container.image}:{config.container.version}",
        name=config.container.name,
        ports={str(container_port): host_port},
        environment=env,
        command=command,
        tmpfs=tmpfs_config,
        remove=not keep_container_around,
        detach=True,
    )
    return container, host_port
