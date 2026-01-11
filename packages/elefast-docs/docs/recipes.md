---
icon: lucide/chef-hat
---

# Recipes

Since Elefast is very flexible, there is no one-size-fits-all solution.
This page describes several copy-paste friendly examples to get you up and running regardless of your setup.

## How to keep a database around after the test ends?

- Can be useful for debugging

## Optimizations

### Not Dropping Test DBs

- If we don't use a context manager to clean up our DBs, we can save a few milliseconds.
  Since we run in a dockerized environment anyways, the whole server will vanish after our test session, so we could be lazy here.
  Maybe one needs to tweak the size of the memoryfs though, or use the actual disk instead.

## FastApi Example Project

## Supporting More Setups

### Async

### Monorepos

- Repo-local plugins for sharing fixtures

### Multiple Servers Or Databases

