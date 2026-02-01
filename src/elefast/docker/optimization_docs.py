"""Documentation and metadata for Postgres optimization settings."""

from dataclasses import dataclass


@dataclass(frozen=True)
class OptimizationInfo:
    """Metadata about a Postgres optimization setting."""

    gain: str
    """Description of performance gain and why it matters for tests."""

    risk: str
    """Description of risks and when to disable this optimization."""

    risk_factor: float
    """Likelihood this optimization causes problems (0.0-1.0).

    0.0 = safe for all tests
    1.0 = risky, may break tests in common scenarios
    """


OPTIMIZATION_DOCS = {
    "tmpfs": OptimizationInfo(
        gain="10-100x improvement for I/O heavy tests. Matters because test databases typically have small datasets and I/O is a major bottleneck. Default (True) auto-sizes to 50% of host RAM.",
        risk="If your tests have large datasets that exceed available RAM, disable tmpfs by setting to False. Or set to a positive integer for a fixed size in MB.",
        risk_factor=0.2,
    ),
    "fsync_off": OptimizationInfo(
        gain="10-30% write throughput improvement. Matters because tests run many sequential writes during setup and teardown.",
        risk="Not suitable for tests that verify data durability. Set to False if your tests need to survive process crashes.",
        risk_factor=0.7,
    ),
    "synchronous_commit_off": OptimizationInfo(
        gain="15-25% improvement for transactional workloads. Matters because tests often run many small transactions in sequence.",
        risk="Transaction durability is not guaranteed. Acceptable for most test scenarios.",
        risk_factor=0.4,
    ),
    "full_page_writes_off": OptimizationInfo(
        gain="5-10% reduction in WAL write volume. Matters when tests generate significant WAL.",
        risk="Only safe if the container never crashes unexpectedly (which it shouldn't in tests).",
        risk_factor=0.2,
    ),
    "wal_level_minimal": OptimizationInfo(
        gain="5-8% reduction in WAL generation. Matters for write-heavy test workloads.",
        risk="Prevents replication and backup features, which tests don't need anyway.",
        risk_factor=0.1,
    ),
    "disable_wal_senders": OptimizationInfo(
        gain="Minimal performance gain, mainly prevents unnecessary resource reservation.",
        risk="Prevents replication, which test databases don't use.",
        risk_factor=0.05,
    ),
    "disable_archiving": OptimizationInfo(
        gain="Eliminates archiving overhead. Matters when WAL would otherwise be copied elsewhere.",
        risk="Prevents point-in-time recovery, which test databases don't need.",
        risk_factor=0.05,
    ),
    "autovacuum_off": OptimizationInfo(
        gain="Skipping this optimization (set to False) means Postgres will vacuum dead tuples, preventing table bloat. Matters for test suites with many updates/deletes—without vacuuming, tables grow and scans become slower over time.",
        risk="If you have very short test suites that finish in seconds, you might benefit from disabling vacuuming (set to True). For long-running suites, leave it enabled.",
        risk_factor=0.6,
    ),
    "jit_off": OptimizationInfo(
        gain="Negligible for simple queries, saves a bit of startup overhead. Matters because test queries are usually simple and don't benefit from JIT.",
        risk="Safe to disable; only affects complex analytical queries.",
        risk_factor=0.05,
    ),
    "shared_buffers_mb": OptimizationInfo(
        gain="~10-20% improvement for working sets smaller than this value. Matters because test databases are usually small enough to fit entirely in buffers.",
        risk="If your test data is larger than 128MB, increase this value or set to None to use Postgres default.",
        risk_factor=0.4,
    ),
    "work_mem_mb": OptimizationInfo(
        gain="Using None (default) is fine for tests. Only tune this if you see many temporary files being written during complex queries.",
        risk="Setting this too low can cause slow sorts and hash operations.",
        risk_factor=0.2,
    ),
    "maintenance_work_mem_mb": OptimizationInfo(
        gain="Using None (default) is fine for tests. Only tune this if you have slow CREATE INDEX or VACUUM operations during setup.",
        risk="Setting this too low can cause slow maintenance operations.",
        risk_factor=0.15,
    ),
    "checkpoint_timeout_seconds": OptimizationInfo(
        gain="Reducing checkpoint frequency (~30 min for tests) means ~5-10% less overhead during test runs. Matters because tests finish within this window and checkpoints are pure overhead.",
        risk="If you have tests that run longer than this value, increase it or set to None to use Postgres default (5 minutes).",
        risk_factor=0.3,
    ),
    "disable_statement_logging": OptimizationInfo(
        gain="2-5% reduction in logging overhead. Matters for speed-focused tests that run thousands of statements.",
        risk="Set to False if you need to debug slow queries or unexpected test failures.",
        risk_factor=0.15,
    ),
}
