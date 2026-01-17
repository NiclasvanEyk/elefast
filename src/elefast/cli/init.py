from elefast.cli.types import ParentParser


def install_init_command(commands: ParentParser) -> None:
    init_command_parser = commands.add_parser(
        "init",
        help="Helps you the recommended default fixtures",
        description="Helps you get started with the recommended default fixtures by printing them to the screen. The output of this command is intended to be redirected into a file (e.g. `elefast init > conftest.py && mv conftest.py tests/`) If you omit the flags, you'll be prompted for values.",
    )
    init_command_parser.set_defaults(func=init_command)
    init_command_parser.add_argument(
        "--driver", help="The name of the driver you intend to use."
    )
    init_command_parser.add_argument(
        "--async",
        action="store_true",
        help="If you intend to use sync or async tests. Can also be inferred from the driver name.",
    )
    init_command_parser.add_argument(
        "--base",
        help="The fully qualified path to the module + name of your ORM base or metadata that defines your schema.",
    )


def init_command(args):
    print(args)
