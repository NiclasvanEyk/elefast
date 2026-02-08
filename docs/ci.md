---
icon: lucide/cloud-check
---

# Continuous Integration

Running your tests locally is nice, but it can be a pain to setup a continuus integration process that runs them on `git push`.
On this site we list a few examples for popular providers.
Note that we assume that you use the `docker` extra to automatically start a Postgres container when you run your tests.

!!! abstract "Contributions Welcome!"

    If your favorite CI provider is missing, feel free to contribute!
    This section of the documentation can benefit from a few more examples.

## Github Actions

GitHub makes it really easy, since they natively support Docker in their CI product.
Just install your dependencies and run `pytest`:

```yaml
name: Pytest
on: [push]
jobs:
  pytest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5

      # This step might be different if you use pip instead of uv
      - name: Install the latest version of uv
        uses: astral-sh/setup-uv@v7
        with:
          enable-cache: true
          activate-environment: true
      - run: uv sync --all-packages --all-extras

      # We only need to run pytest. Docker is available 
      - run: pytest
```

Elefast also runs test on GitHub actions, so feel free to take a look at [our workflows](https://github.com/NiclasvanEyk/elefast/tree/main/.github/workflows) if you are looking for a real-world example.

## GitLab CI

Getting Docker to be accessible in your CI scripts can be a pain.
However, Gitlab supports [services](https://docs.gitlab.com/ci/services/), which can be used to start a Postgres container for a specific stage.
Combine that with [supporting existing database services](./best-practises.md#supporting-existing-database-servers), e.g. by setting a `TESTING_DB_URL` environment variable, and you can get your tests to run pretty easily.

```yaml
stages:
  - testing

Pytest:
  stage: testing
  services:
    - postgres # See https://docs.gitlab.com/ci/services/postgres
  variables:
    POSTGRES_PASSWORD: "elefast"
    TESTING_DB_URL: "postgresql+psycopg2://postgres:elefast@127.0.0.1" # NOTE: You may need to replace "psycopg2" with your installed driver
  script:
    - curl -LsSf https://astral.sh/uv/install.sh | sh
    - uv sync --all-packages --all-extras
    - uv run pytest
```

While this uses a plain Docker PostgreSQL container without any testing optimizations like tmpfs, slow tests are better than no tests.
