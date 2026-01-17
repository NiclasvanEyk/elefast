from sqlalchemy import Connection, text


def test_database_math(db_connection: Connection):
    result = db_connection.execute(text("SELECT 1 + 1")).scalar_one()
    assert result == 2
