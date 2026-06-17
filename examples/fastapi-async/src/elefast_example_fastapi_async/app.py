from contextlib import asynccontextmanager
from typing import AsyncIterator, TypedDict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from elefast_example_fastapi_async.database import DatabaseContext, Post, get_db
from elefast_example_fastapi_async.dependencies import DbSessionDep


class LifespanState(TypedDict):
    database: DatabaseContext


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[LifespanState]:
    db = get_db()
    yield {"database": db}
    await db.engine.dispose()


app = FastAPI(
    title="Elefast Test Backend",
    summary="A test backend showcasing how to use Elefast with FastAPI",
    lifespan=lifespan,
)


class PostExcerpt(BaseModel):
    slug: str
    headline: str
    excerpt: str


@app.get("/posts")
async def get_posts(db: DbSessionDep) -> list[PostExcerpt]:
    posts = await db.scalars(select(Post).order_by(Post.slug))
    excerpts: list[PostExcerpt] = []
    for post in posts:
        item = PostExcerpt(
            slug=post.slug, headline=post.headline, excerpt=post.body[:100]
        )
        excerpts.append(item)
    return excerpts


class FullPost(BaseModel):
    headline: str
    body: str


@app.get("/posts/{slug}")
async def get_post(slug: str, db: DbSessionDep) -> FullPost:
    post = await db.get(Post, slug)
    if post is None:
        raise HTTPException(
            status_code=404, detail=f"Post with slug '{slug}' was not found"
        )
    return FullPost(headline=post.headline, body=post.body)
