from argparse import ArgumentParser

from elefast.cli.init import install_init_command


def build_parser() -> ArgumentParser:
    cli = ArgumentParser(prog="elefast")
    commands = cli.add_subparsers(required=True, title="subcommands")

    install_init_command(commands)

    return cli
