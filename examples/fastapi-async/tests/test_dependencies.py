from unittest.mock import MagicMock
import pytest

from elefast_example_fastapi_async.database import DatabaseContext
from elefast_example_fastapi_async.dependencies import get_db_context, get_engine


def test_get_db_context_raises_when_app_not_fastapi():
    """Test that get_db_context raises TypeError when app is not FastAPI."""
    request = MagicMock()
    request.app = MagicMock()

    with pytest.raises(TypeError):
        get_db_context(request)


def test_get_db_context_raises_when_database_not_db_context():
    """Test that get_db_context raises TypeError when database is not DatabaseContext."""
    from fastapi import FastAPI

    app = FastAPI()
    app.state.database = MagicMock()

    request = MagicMock()
    request.app = app

    with pytest.raises(TypeError):
        get_db_context(request)


def test_get_engine_returns_engine_from_context():
    """Test that get_engine returns the engine from the database context."""
    mock_engine = MagicMock()
    db_context = DatabaseContext(engine=mock_engine, sessionmaker=MagicMock())

    result = get_engine(db_context)

    assert result is mock_engine
