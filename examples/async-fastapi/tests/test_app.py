import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from elefast_example_fastapi_async.database import Post
from elefast_example_fastapi_async.app import PostExcerpt, FullPost


@pytest.mark.asyncio
async def test_get_posts(db_session: AsyncSession, backend: TestClient):
    db_session.add_all(
        [Post(slug="an-article", headline="Hello World!", body="The article content.")]
    )
    await db_session.commit()

    response = backend.get("/posts")
    assert response.status_code == 200

    json_response_content = response.json()
    assert len(json_response_content) == 1

    excerpt = PostExcerpt.model_validate(json_response_content[0])
    assert excerpt.slug == "an-article"
    assert excerpt.headline == "Hello World!"
    assert excerpt.excerpt == "The article content."


@pytest.mark.asyncio
async def test_get_missing_post(backend: TestClient):
    # NOTE: No posts in the database
    response = backend.get("/posts/non-existent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_existing_post(db_session: AsyncSession, backend: TestClient):
    db_session.add_all(
        [Post(slug="an-article", headline="Hello World!", body="The article content.")]
    )
    await db_session.commit()

    response = backend.get("/posts/an-article")
    assert response.status_code == 200

    post = FullPost.model_validate_json(response.content)
    assert post.headline == "Hello World!"
    assert post.body == "The article content."
