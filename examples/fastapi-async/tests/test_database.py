from unittest.mock import patch
import pytest


def test_get_db_raises_without_db_url():
    """Test that get_db raises ValueError when DB_URL is not set."""
    with patch.dict("os.environ", {}, clear=True):
        from elefast_example_fastapi_async.database import get_db

        with pytest.raises(ValueError, match="No DB_URL environment variable"):
            get_db()
