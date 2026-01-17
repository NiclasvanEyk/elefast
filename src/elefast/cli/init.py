from argparse import Namespace
from sys import stderr

from elefast.cli.types import ParentParser

# NOTE: psycopg can do both, so we cannot infer anything.
STRICTLY_ASYNC_DRIVERS = ["asyncpg", "aiopg"]
STRICTLY_SYNC_DRIVERS = ["psycopg2", "pg8000"]


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
        action="append_const",
        dest="async_preference",
        const=True,
        help="Use async methods and classes where necessary. Inferred from the driver if not passed explicitly.",
    )
    init_command_parser.add_argument(
        "--sync",
        action="append_const",
        dest="async_preference",
        const=False,
        help="Use sync methods and classes. Inferred from the driver if not passed explicitly.",
    )
    init_command_parser.add_argument(
        "--no-interaction",
        action="store_true",
        help="Use defaults instead of asking interactive questions for options",
    )


def init_command(args: Namespace):
    _init_command(
        driver=args.driver,
        allow_interaction=not args.no_interaction,
        async_preference=args.async_preference or [],
    )


def _init_command(
    driver: str | None,
    allow_interaction: bool,
    async_preference: list[bool],
):
    driver = _figure_out_driver(driver)
    use_async = _figure_out_if_we_should_use_async(
        driver, async_preference, allow_interaction
    )

    class_prefix = "Async" if use_async else ""
    maybe_async = "async " if use_async else ""
    maybe_await = "await " if use_async else ""
    template = f'''
import os
    
import pytest
from elefast import {class_prefix}Database, {class_prefix}DatabaseServer, docker


@pytest.fixture(scope="session")
def db_server() -> {class_prefix}DatabaseServer:
    explicit_url = os.getenv("TESTING_DB_URL")
    db_url = explicit_url if explicit_url else docker.postgres("{driver}")
    # If you have a shared Base-class, import it above and use
    # `metadata=YourBaseClass.metadata` below.
    return {class_prefix}DatabaseServer(db_url, metadata=None)


@pytest.fixture
{maybe_async}def db(db_server: {class_prefix}DatabaseServer): 
    {maybe_async}with {maybe_await}db_server.create_database() as database:
        yield database


@pytest.fixture
{maybe_async}def db_connection(db: {class_prefix}Database):
    {maybe_async}with db.engine.begin() as connection:
        yield connection


@pytest.fixture
{maybe_async}def db_session(db: {class_prefix}Database):
    {maybe_async}with db.session() as session:
        yield session
    '''
    print(template.strip() + "\n")


def _figure_out_driver(driver: str | None) -> str:
    if driver:
        return driver

    for name in STRICTLY_SYNC_DRIVERS + STRICTLY_ASYNC_DRIVERS + ["psycopg"]:
        from importlib.util import find_spec

        if find_spec(name):
            print(
                f"Using '{name}' as the driver, since no explit --driver argument was passed, and {name} is installed.",
                file=stderr,
            )
            return name

    print(
        "No --driver was passed and no popular one was found in installed packages. Falling back to psycopg2...",
        file=stderr,
    )
    return "psycopg2"


def _figure_out_if_we_should_use_async(
    driver: str, async_preference: list[bool], allow_interaction: bool
) -> bool:
    if async_preference == []:
        if driver in STRICTLY_ASYNC_DRIVERS:
            return True
        elif driver in STRICTLY_SYNC_DRIVERS:
            return False
        elif not allow_interaction:
            return False
        else:
            print("Are you intending to use asyncio? [y/N]: ", file=stderr)
            return "y" in input()

    return any(async_preference)
