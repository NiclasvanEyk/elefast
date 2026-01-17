from typing import cast

from docker import DockerClient
from docker.models.containers import Container

from elefast.docker.configuration import Configuration


def get_docker() -> DockerClient:
    return DockerClient.from_env()


def ensure_db_server_started(
    docker: DockerClient | None = None,
    config: Configuration | None = None,
    keep_container_around: bool = False,
) -> Container:
    if docker is None:
        docker = get_docker()
    if config is None:
        config = Configuration()

    if container := get_db_server_container(docker, config.container.name):
        return container
    return start_db_server_container(docker, config, keep_container_around)


def get_db_server_container(docker: DockerClient, name: str) -> Container | None:
    containers = cast(list[Container], docker.containers.list())
    for container in containers:
        if container.name == name:
            return container


def start_db_server_container(
    docker: DockerClient, config: Configuration, keep_container_around: bool
) -> Container:
    optimizations = config.optimizations
    command: list[str] = []
    env: dict[str, str] = {
        "POSTGRES_USER": config.credentials.user,
        "POSTGRES_PASSWORD": config.credentials.password,
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
    if optimizations.jit_off:
        command += ["-c", "jit=off"]
    if optimizations.shared_buffers_mb is not None:
        command += ["-c", f"shared_buffers={optimizations.shared_buffers_mb}MB"]
    if optimizations.work_mem_mb is not None:
        command += ["-c", f"work_mem={optimizations.work_mem_mb}MB"]
    if optimizations.maintenance_work_mem_mb is not None:
        command += [
            "-c",
            f"maintenance_work_mem={optimizations.maintenance_work_mem_mb}MB",
        ]
    if optimizations.no_locale:
        env["POSTGRES_INITDB_ARGS"] = "--no-locale"

    return docker.containers.run(
        image=f"{config.container.image}:{config.container.version}",
        name=config.container.name,
        ports=config.container.ports,
        environment=env,
        tmpfs={"/var/lib/postgresql": f"rw,size={optimizations.tmpfs_size_mb}m"}
        if optimizations.tmpfs_size_mb is not None
        else {},
        remove=not keep_container_around,
        detach=True,
    )
