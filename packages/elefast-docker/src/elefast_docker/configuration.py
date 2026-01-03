from dataclasses import dataclass


@dataclass(frozen=True, slots=True, kw_only=True)
class Optimizations:
    # Storage / durability
    tmpfs_size_mb: int | None = 512
    fsync_off: bool = True
    synchronous_commit_off: bool = True
    full_page_writes_off: bool = True
    # WAL / replication
    wal_level_minimal: bool = True
    disable_wal_senders: bool = True
    disable_archiving: bool = True
    # Background activity
    autovacuum_off: bool = True
    jit_off: bool = True
    # Initialization / startup
    no_locale: bool = True
    prebuilt_image: bool = False  # schema baked into image
    # Memory tuning (kept conservative)
    shared_buffers_mb: int | None = 128
    work_mem_mb: int | None = None
    maintenance_work_mem_mb: int | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class Configuration:
    container_name: str = "elefast"
    container_image: str = "postgres"
    container_version: str = "latest"

    postgres_user: str = "postgres"
    postgres_password: str = "elefast"

    optimizations: Optimizations = Optimizations()
