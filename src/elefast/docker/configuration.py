from dataclasses import dataclass


@dataclass(frozen=True, slots=True, kw_only=True)
class Optimizations:
    """
    Configuration overrides that make Postgres more suitable for fast testing runs.

    These optimizations reduce disk I/O, memory overhead, and background work at the cost
    of durability guarantees and crash recovery. They're safe for isolated test databases
    that don't need to survive container restarts.

    See `elefast.docker.optimization_docs.OPTIMIZATION_DOCS` for detailed information about
    each setting, including performance gains, risks, and when to disable them.
    """

    tmpfs_size_mb: int | None = 512
    fsync_off: bool = True
    synchronous_commit_off: bool = True
    full_page_writes_off: bool = True
    wal_level_minimal: bool = True
    disable_wal_senders: bool = True
    disable_archiving: bool = True
    autovacuum_off: bool = False
    jit_off: bool = True
    no_locale: bool = True
    shared_buffers_mb: int | None = 128
    work_mem_mb: int | None = None
    maintenance_work_mem_mb: int | None = None
    checkpoint_timeout_seconds: int | None = 1800
    disable_statement_logging: bool = True


@dataclass(frozen=True, slots=True, kw_only=True)
class Container:
    """Configuration for the Docker container running PostgreSQL."""

    name: str = "elefast"
    """Name of the Docker container."""

    image: str = "postgres"
    """Docker image name to use."""

    version: str = "latest"
    """Docker image version/tag."""

    database_port: tuple[int, int | None] | None = None
    """Port mapping for the PostgreSQL database connection.

    Specifies which container port the database runs on and which host port to map it to.

    - `None`: Use default container port 5432 with a random free host port (default)
    - `tuple[int, int]` (e.g., (5432, 5432)): Explicit container and host port mapping
    - `tuple[int, None]` (e.g., (3306, None)): Container port with a random free host port
    """


@dataclass(frozen=True, slots=True, kw_only=True)
class Credentials:
    user: str = "postgres"
    password: str = "elefast"
    host: str = "127.0.0.1"


@dataclass(frozen=True, slots=True, kw_only=True)
class Configuration:
    container: Container = Container()
    credentials: Credentials = Credentials()
    optimizations: Optimizations = Optimizations()
