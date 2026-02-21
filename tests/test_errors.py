"""Tests for error handling in elefast."""

import pytest

from elefast.errors import ElefastError, DatabaseNotReadyError


class TestElefastError:
    """Tests for the base ElefastError class."""

    def test_elefast_error_is_exception(self):
        """Test that ElefastError is an Exception subclass."""
        assert issubclass(ElefastError, Exception)

    def test_elefast_error_can_be_raised(self):
        """Test that ElefastError can be raised and caught."""
        with pytest.raises(ElefastError):
            raise ElefastError("Test error")

    def test_elefast_error_message(self):
        """Test ElefastError message preservation."""
        msg = "Custom error message"
        try:
            raise ElefastError(msg)
        except ElefastError as e:
            assert str(e) == msg


class TestDatabaseNotReadyError:
    """Tests for the DatabaseNotReadyError class."""

    def test_database_not_ready_error_is_elefast_error(self):
        """Test that DatabaseNotReadyError is an ElefastError subclass."""
        assert issubclass(DatabaseNotReadyError, ElefastError)

    def test_database_not_ready_error_can_be_raised(self):
        """Test that DatabaseNotReadyError can be raised and caught."""
        with pytest.raises(DatabaseNotReadyError):
            raise DatabaseNotReadyError("Database not ready")

    def test_database_not_ready_error_message(self):
        """Test DatabaseNotReadyError message preservation."""
        msg = "Failed to connect after 30 seconds"
        try:
            raise DatabaseNotReadyError(msg)
        except DatabaseNotReadyError as e:
            assert str(e) == msg

    def test_database_not_ready_error_with_cause(self):
        """Test DatabaseNotReadyError with exception chaining."""
        original_error = ConnectionError("Connection refused")
        try:
            raise DatabaseNotReadyError("Database timeout") from original_error
        except DatabaseNotReadyError as e:
            assert e.__cause__ is original_error
            assert str(e.__cause__) == "Connection refused"

    def test_catch_as_elefast_error(self):
        """Test that DatabaseNotReadyError can be caught as ElefastError."""
        with pytest.raises(ElefastError):
            raise DatabaseNotReadyError("Test")


class TestErrorInheritance:
    """Tests for error class inheritance hierarchy."""

    def test_all_errors_inherit_from_base(self):
        """Test that all custom errors inherit from ElefastError."""
        errors = [DatabaseNotReadyError]
        for error_class in errors:
            assert issubclass(error_class, ElefastError), (
                f"{error_class} should inherit from ElefastError"
            )

    def test_all_errors_inherit_from_exception(self):
        """Test that all custom errors inherit from Exception."""
        errors = [ElefastError, DatabaseNotReadyError]
        for error_class in errors:
            assert issubclass(error_class, Exception), (
                f"{error_class} should inherit from Exception"
            )
