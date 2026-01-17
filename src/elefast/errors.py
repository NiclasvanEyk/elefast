class ElefastError(Exception):
    """The base class for errors of elefat"""


class DatabaseNotReadyError(ElefastError):
    """We tried to connect to the DB, but even after lots of attempts we could not run a simple query."""
