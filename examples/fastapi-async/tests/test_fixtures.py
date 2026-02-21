import pytest
from sqlalchemy import text


@pytest.mark.asyncio
async def test_db_connection(db_connection):
    """Test that db_connection fixture works."""
    result = await db_connection.execute(text("SELECT 1"))
    assert result.fetchone()[0] == 1


@pytest.mark.asyncio
async def test_db_session(db_session):
    """Test that db_session fixture works."""
    result = await db_session.execute(text("SELECT 1"))
    assert result.fetchone()[0] == 1
