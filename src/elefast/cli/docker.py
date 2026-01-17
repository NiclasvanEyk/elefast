from elefast.cli.types import ParentParser


def install_docker_command_if_available(commands: ParentParser) -> None:
    try:
        import elefast.docker  # noqa: F401
    except Exception:
        return

    parser = commands.add_parser(
        "docker",
        help="Utilities for managing elefasts docker container",
        description="A helpful description.",  # TODO
    )
    parser.add_argument("--reuse", action="store_true")
    parser.set_defaults(func=docker_command)


def docker_command(args) -> None:
    print(args)
