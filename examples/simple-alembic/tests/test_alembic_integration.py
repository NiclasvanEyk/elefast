from simple_alembic.models import Post
from sqlalchemy import select
from sqlalchemy.orm import Session


def test_alembic_integration(db_session: Session):
    posts = db_session.scalars(select(Post)).all()
    assert len(posts) == 1

    dummy_post = posts[0]
    assert dummy_post.slug == "dummy-post"
    assert dummy_post.headline == "A dummy post"
