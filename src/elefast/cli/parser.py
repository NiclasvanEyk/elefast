from elefast.cli.docker import install_docker_command_if_available
from elefast.cli.init import install_init_command
from argparse import ArgumentParser

DESCRIPTION = """
A helpful description
""".strip()


def build_parser() -> ArgumentParser:
    cli = ArgumentParser(prog="elefast", description=DESCRIPTION)
    commands = cli.add_subparsers(required=True, title="subcommands")

    install_init_command(commands)
    install_docker_command_if_available(commands)

    return cli
