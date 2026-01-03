import typer
from elefast_docker import ensure_db_server_started

app = typer.Typer(name="elefast-docker")


@app.command()
def start():
    """
    Starts the elefast test container if it is not already running.
    """

    # TODO: honor config
    container = ensure_db_server_started()
    print(f"{container.name} ({container.id})")


@app.command()
def hello(name: str):
    print(f"Hello {name}")


if __name__ == "__main__":
    app()
