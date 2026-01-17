from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True, kw_only=True)
class Optimizations:
    """
    Configuration overrides that make Postgres more suitable for fast testing runs.
    """

    tmpfs_size_mb: int | None = 512
    fsync_off: bool = True
    synchronous_commit_off: bool = True
    full_page_writes_off: bool = True
    wal_level_minimal: bool = True
    disable_wal_senders: bool = True
    disable_archiving: bool = True
    autovacuum_off: bool = True
    jit_off: bool = True
    no_locale: bool = True
    shared_buffers_mb: int | None = 128
    work_mem_mb: int | None = None
    maintenance_work_mem_mb: int | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class Container:
    name: str = "elefast"
    image: str = "postgres"
    version: str = "latest"
    ports: dict[str, str] = field(default_factory=lambda: {"5432": "5432"})


@dataclass(frozen=True, slots=True, kw_only=True)
class Credentials:
    user: str = "postgres"
    password: str = "elefast"
    host: str = "127.0.0.1"
    port: int = 5432


@dataclass(frozen=True, slots=True, kw_only=True)
class Configuration:
    container: Container = Container()
    credentials: Credentials = Credentials()
    optimizations: Optimizations = Optimizations()
