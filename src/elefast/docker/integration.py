from pathlib import Path
from tempfile import gettempdir
from filelock import FileLock
from docker import DockerClient
from elefast.docker.orchestration import ensure_db_server_started
from elefast.docker.configuration import Configuration
from sqlalchemy import URL


def postgres(
    driver: str,
    docker: DockerClient | None = None,
    config: Configuration | None = None,
    keep_container_around: bool = True,
) -> URL:
    docker = docker if docker else DockerClient.from_env()
    config = config if config else Configuration()

    with FileLock(Path(gettempdir()) / "elefast-docker.lock"):
        ensure_db_server_started(
            docker=docker, config=config, keep_container_around=keep_container_around
        )
    return URL.create(
        drivername=f"postgresql+{driver}",
        username=config.credentials.user,
        password=config.credentials.password,
        host=config.credentials.host,
        port=config.credentials.port,
    )
