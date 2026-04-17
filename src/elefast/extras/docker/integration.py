from pathlib import Path
from tempfile import gettempdir

from docker import DockerClient
from filelock import FileLock
from sqlalchemy import URL

from elefast.extras.docker.configuration import Configuration
from elefast.extras.docker.orchestration import ensure_db_server_started


def postgres(
    driver: str,
    docker: DockerClient | None = None,
    config: Configuration | None = None,
    keep_container_around: bool = True,
) -> URL:
    docker = docker or DockerClient.from_env()
    config = config or Configuration()

    with FileLock(Path(gettempdir()) / "elefast-docker.lock"):
        _, host_port = ensure_db_server_started(
            docker=docker, config=config, keep_container_around=keep_container_around
        )

    return URL.create(
        drivername=f"postgresql+{driver}",
        username=config.credentials.user,
        password=config.credentials.password,
        host=config.credentials.host,
        port=host_port,
    )
