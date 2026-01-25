---
icon: lucide/wrench
---

<!-- AUTO-GENERATED FILE: DO NOT EDIT MANUALLY -->
<!-- Run `uv run docs/optimizations.py` to regenerate -->

# Optimizations

This document describes all available optimization settings for the Docker PostgreSQL container.

## Why Test Databases Are Different

Production PostgreSQL instances prioritize data durability, crash recovery, and handling
concurrent workloads from multiple applications. Test databases have fundamentally different
requirements:

- **Isolation**: Test databases are ephemeral—they're created per test run and discarded
  afterward. Data doesn't need to survive container restarts or crashes.
- **Sequential workloads**: Tests run serially within a process, not concurrent requests from
  multiple users. Heavy durability guarantees are unnecessary overhead.
- **Speed is paramount**: Slow tests mean slow feedback loops for developers. Optimizing for
  test speed directly improves developer experience.
- **No recovery requirements**: Production needs crash recovery and point-in-time restore.
  Tests just need to spin up fresh.

Elefast exploits these differences by disabling features like fsync, WAL archiving, and
replication, storing the entire database in RAM, and tuning PostgreSQL aggressively for
speed. These optimizations are **not safe for production**, but perfect for testing.

## Available Optimizations

The settings below reduce disk I/O, memory overhead, and background work at the cost
of durability guarantees and crash recovery. All are safe for isolated test databases
that don't need to survive container restarts.

## Overview

| Setting | Default | Risk | Description |
|---------|---------|------|-------------|
| `autovacuum_off` | `False` | 🔴 | Skipping this optimization (set to False) means Postgres will vacuum dead tuples, preventing table bloat. |
| `checkpoint_timeout_seconds` | `1800` | 🟡 | Reducing checkpoint frequency (~30 min for tests) means ~5-10% less overhead during test runs. |
| `disable_archiving` | `True` | 🟢 | Eliminates archiving overhead. |
| `disable_statement_logging` | `True` | 🟢 | 2-5% reduction in logging overhead. |
| `disable_wal_senders` | `True` | 🟢 | Minimal performance gain, mainly prevents unnecessary resource reservation. |
| `fsync_off` | `True` | 🔴 | 10-30% write throughput improvement. |
| `full_page_writes_off` | `True` | 🟢 | 5-10% reduction in WAL write volume. |
| `jit_off` | `True` | 🟢 | Negligible for simple queries, saves a bit of startup overhead. |
| `maintenance_work_mem_mb` | `None` | 🟢 | Using None (default) is fine for tests. |
| `no_locale` | `True` | 🟢 | 5-10% faster initialization, smaller memory footprint. |
| `shared_buffers_mb` | `128` | 🟡 | ~10-20% improvement for working sets smaller than this value. |
| `synchronous_commit_off` | `True` | 🟡 | 15-25% improvement for transactional workloads. |
| `tmpfs` | `True` | 🟢 | 10-100x improvement for I/O heavy tests. |
| `wal_level_minimal` | `True` | 🟢 | 5-8% reduction in WAL generation. |
| `work_mem_mb` | `None` | 🟢 | Using None (default) is fine for tests. |

**Risk levels:** 🟢 Low (< 0.3) | 🟡 Medium (0.3-0.6) | 🔴 High (> 0.6)

## Settings

### 🔴 `autovacuum_off`

**Risk Factor:** 0.6

**Gain**

Skipping this optimization (set to False) means Postgres will vacuum dead tuples, preventing table bloat. Matters for test suites with many updates/deletes—without vacuuming, tables grow and scans become slower over time.

**Potential Issues**

If you have very short test suites that finish in seconds, you might benefit from disabling vacuuming (set to True). For long-running suites, leave it enabled.

### 🟡 `checkpoint_timeout_seconds`

**Risk Factor:** 0.3

**Gain**

Reducing checkpoint frequency (~30 min for tests) means ~5-10% less overhead during test runs. Matters because tests finish within this window and checkpoints are pure overhead.

**Potential Issues**

If you have tests that run longer than this value, increase it or set to None to use Postgres default (5 minutes).

### 🟢 `disable_archiving`

**Risk Factor:** 0.05

**Gain**

Eliminates archiving overhead. Matters when WAL would otherwise be copied elsewhere.

**Potential Issues**

Prevents point-in-time recovery, which test databases don't need.

### 🟢 `disable_statement_logging`

**Risk Factor:** 0.15

**Gain**

2-5% reduction in logging overhead. Matters for speed-focused tests that run thousands of statements.

**Potential Issues**

Set to False if you need to debug slow queries or unexpected test failures.

### 🟢 `disable_wal_senders`

**Risk Factor:** 0.05

**Gain**

Minimal performance gain, mainly prevents unnecessary resource reservation.

**Potential Issues**

Prevents replication, which test databases don't use.

### 🔴 `fsync_off`

**Risk Factor:** 0.7

**Gain**

10-30% write throughput improvement. Matters because tests run many sequential writes during setup and teardown.

**Potential Issues**

Not suitable for tests that verify data durability. Set to False if your tests need to survive process crashes.

### 🟢 `full_page_writes_off`

**Risk Factor:** 0.2

**Gain**

5-10% reduction in WAL write volume. Matters when tests generate significant WAL.

**Potential Issues**

Only safe if the container never crashes unexpectedly (which it shouldn't in tests).

### 🟢 `jit_off`

**Risk Factor:** 0.05

**Gain**

Negligible for simple queries, saves a bit of startup overhead. Matters because test queries are usually simple and don't benefit from JIT.

**Potential Issues**

Safe to disable; only affects complex analytical queries.

### 🟢 `maintenance_work_mem_mb`

**Risk Factor:** 0.15

**Gain**

Using None (default) is fine for tests. Only tune this if you have slow CREATE INDEX or VACUUM operations during setup.

**Potential Issues**

Setting this too low can cause slow maintenance operations.

### 🟢 `no_locale`

**Risk Factor:** 0.05

**Gain**

5-10% faster initialization, smaller memory footprint. Matters for container startup time.

**Potential Issues**

Tests usually don't care about collation behavior.

### 🟡 `shared_buffers_mb`

**Risk Factor:** 0.4

**Gain**

~10-20% improvement for working sets smaller than this value. Matters because test databases are usually small enough to fit entirely in buffers.

**Potential Issues**

If your test data is larger than 128MB, increase this value or set to None to use Postgres default.

### 🟡 `synchronous_commit_off`

**Risk Factor:** 0.4

**Gain**

15-25% improvement for transactional workloads. Matters because tests often run many small transactions in sequence.

**Potential Issues**

Transaction durability is not guaranteed. Acceptable for most test scenarios.

### 🟢 `tmpfs`

**Risk Factor:** 0.2

**Gain**

10-100x improvement for I/O heavy tests. Matters because test databases typically have small datasets and I/O is a major bottleneck. Default (True) auto-sizes to 50% of host RAM.

**Potential Issues**

If your tests have large datasets that exceed available RAM, disable tmpfs by setting to False. Or set to a positive integer for a fixed size in MB.

### 🟢 `wal_level_minimal`

**Risk Factor:** 0.1

**Gain**

5-8% reduction in WAL generation. Matters for write-heavy test workloads.

**Potential Issues**

Prevents replication and backup features, which tests don't need anyway.

### 🟢 `work_mem_mb`

**Risk Factor:** 0.2

**Gain**

Using None (default) is fine for tests. Only tune this if you see many temporary files being written during complex queries.

**Potential Issues**

Setting this too low can cause slow sorts and hash operations.
