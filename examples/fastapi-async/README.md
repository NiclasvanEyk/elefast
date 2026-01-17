# Elefast + FastAPI + `asyncio`

This example shows you how to use Elefast with a FastAPI backend that makes heavy use of Pythons `asyncio` functionality.

## Setup

Run `uv sync --all-packages --all-extras` in the root of the repository (**not** in this directory).
Then run `cd examples/fastapi-async` (this directory) for all following steps.

## Usage

- Run the tests using `uv run pytest` in this directory.
- Run the backend by:
  1. Starting a local postgres server (e.g. `docker run -d -e "POSTGRES_PASSWORD=elefast" -p 5432 postgres`),
  2. Start the backend by running `DB_URL=postgresql+asyncpg://postgres:elefast@127.0.0.1:5432 uv run fastapi dev`

## Implementation Notes

- A `sqlalchemy.ext.asyncio.AsyncEngine` instance is stored in the `app`s [`state` property](https://fastapi.tiangolo.com/reference/fastapi/?h=state#fastapi.FastAPI.state).
  This way we don't rely on a global variable and can switch to our test database in the tests by using [environment variables without monkeypatching](https://niclasvaneyk.github.io/elefast/best-practises/#environment-variables).
- We artificially generate more test cases by using Pytests parameterized tests to simulate a larger test suite.
