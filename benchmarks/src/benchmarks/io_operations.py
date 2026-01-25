"""Benchmark IO performance with various optimization configurations."""

import sys
import time
from dataclasses import dataclass, replace

import psycopg2
from docker import DockerClient

from elefast.docker.configuration import Configuration, Optimizations
from elefast.docker.orchestration import (
    ensure_db_server_started,
    get_db_server_container,
    get_docker,
)


@dataclass
class IOBenchmarkResult:
    """Result of a single IO benchmark run."""

    scenario: str
    config_name: str
    optimizations: dict[str, bool | int | None]
    operation_count: int
    duration_seconds: float
    ops_per_second: float


def cleanup_container(docker: DockerClient, container_name: str) -> None:
    """Stop and remove a container if it exists."""
    container = get_db_server_container(docker, container_name)
    if container:
        try:
            container.stop(timeout=5)
            container.remove()
        except Exception:
            pass


def wait_for_postgres(
    host: str,
    port: int,
    user: str,
    password: str,
    timeout: int = 60,
    poll_interval: float = 0.5,
) -> None:
    """Wait for PostgreSQL to be ready."""
    start = time.time()
    deadline = start + timeout

    while time.time() < deadline:
        try:
            conn = psycopg2.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                dbname="postgres",
                connect_timeout=5,
            )
            conn.close()
            return
        except psycopg2.OperationalError:
            time.sleep(poll_interval)

    raise TimeoutError(f"PostgreSQL did not become ready after {timeout} seconds")


def setup_test_table(conn: psycopg2.extensions.connection) -> None:
    """Create the test table."""
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS bench_data CASCADE")
        cur.execute("""
            CREATE TABLE bench_data (
                id SERIAL PRIMARY KEY,
                value TEXT NOT NULL,
                amount INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    conn.commit()


def benchmark_bulk_insert(
    conn: psycopg2.extensions.connection,
) -> tuple[int, float]:
    """Benchmark: Insert 10k rows in a single transaction.

    Returns:
        (row_count, duration_seconds)
    """
    row_count = 10000
    values = [(f"value_{i}", i % 1000) for i in range(row_count)]

    # Clear table
    with conn.cursor() as cur:
        cur.execute("TRUNCATE bench_data")
    conn.commit()

    # Measure bulk insert
    start = time.time()
    with conn.cursor() as cur:
        for value, amount in values:
            cur.execute(
                "INSERT INTO bench_data (value, amount) VALUES (%s, %s)",
                (value, amount),
            )
    conn.commit()
    duration = time.time() - start

    return row_count, duration


def benchmark_individual_inserts(
    conn: psycopg2.extensions.connection,
) -> tuple[int, float]:
    """Benchmark: Insert 1k rows with individual transactions.

    Returns:
        (row_count, duration_seconds)
    """
    row_count = 1000
    values = [(f"value_{i}", i % 100) for i in range(row_count)]

    # Clear table
    with conn.cursor() as cur:
        cur.execute("TRUNCATE bench_data")
    conn.commit()

    # Measure individual inserts
    start = time.time()
    for value, amount in values:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO bench_data (value, amount) VALUES (%s, %s)",
                (value, amount),
            )
        conn.commit()
    duration = time.time() - start

    return row_count, duration


def benchmark_random_updates(
    conn: psycopg2.extensions.connection,
) -> tuple[int, float]:
    """Benchmark: Update 5k random rows with individual transactions.

    Returns:
        (update_count, duration_seconds)
    """
    # First, populate with data
    row_count = 5000
    values = [(f"value_{i}", i % 1000) for i in range(row_count)]

    with conn.cursor() as cur:
        cur.execute("TRUNCATE bench_data")
    conn.commit()

    with conn.cursor() as cur:
        for value, amount in values:
            cur.execute(
                "INSERT INTO bench_data (value, amount) VALUES (%s, %s)",
                (value, amount),
            )
    conn.commit()

    # Measure updates
    start = time.time()
    for i in range(row_count):
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE bench_data SET amount = %s WHERE id = %s",
                (i % 500, (i % row_count) + 1),
            )
        conn.commit()
    duration = time.time() - start

    return row_count, duration


def benchmark_mixed_workload(
    conn: psycopg2.extensions.connection,
) -> tuple[int, float]:
    """Benchmark: Mixed workload (setup 5k inserts, then 1k mixed ops).

    Returns:
        (operation_count, duration_seconds)
    """
    # Setup: bulk insert 5k rows
    setup_count = 5000
    setup_values = [(f"setup_{i}", i % 1000) for i in range(setup_count)]

    with conn.cursor() as cur:
        cur.execute("TRUNCATE bench_data")
    conn.commit()

    with conn.cursor() as cur:
        for value, amount in setup_values:
            cur.execute(
                "INSERT INTO bench_data (value, amount) VALUES (%s, %s)",
                (value, amount),
            )
    conn.commit()

    # Mixed operations: 500 inserts, 300 updates, 200 deletes
    operations = []
    for i in range(500):
        operations.append(("insert", f"mixed_{i}", i % 100))
    for i in range(300):
        operations.append(("update", i % setup_count + 1, i % 500))
    for i in range(200):
        operations.append(("delete", i % setup_count + 1, None))

    # Measure mixed workload
    start = time.time()
    for op in operations:
        with conn.cursor() as cur:
            if op[0] == "insert":
                cur.execute(
                    "INSERT INTO bench_data (value, amount) VALUES (%s, %s)",
                    (op[1], op[2]),
                )
            elif op[0] == "update":
                cur.execute(
                    "UPDATE bench_data SET amount = %s WHERE id = %s",
                    (op[2], op[1]),
                )
            elif op[0] == "delete":
                cur.execute("DELETE FROM bench_data WHERE id = %s", (op[1],))
        conn.commit()
    duration = time.time() - start

    return len(operations), duration


def benchmark_scenario(
    docker: DockerClient,
    config_name: str,
    optimizations: Optimizations,
    container_name: str,
    scenario_name: str,
    scenario_func,
) -> IOBenchmarkResult:
    """Run a single IO benchmark scenario."""
    config = Configuration(
        container=replace(
            Configuration().container,
            name=container_name,
        ),
        optimizations=optimizations,
    )

    # Start container (don't measure startup time)
    container, host_port = ensure_db_server_started(
        docker=docker,
        config=config,
        keep_container_around=True,
    )
    wait_for_postgres(
        host=config.credentials.host,
        port=host_port,
        user=config.credentials.user,
        password=config.credentials.password,
    )

    # Connect and run benchmark
    try:
        conn = psycopg2.connect(
            host=config.credentials.host,
            port=host_port,
            user=config.credentials.user,
            password=config.credentials.password,
            dbname="postgres",
        )

        # Setup
        setup_test_table(conn)

        # Run scenario and measure
        operation_count, duration = scenario_func(conn)

        conn.close()
    finally:
        cleanup_container(docker, container_name)

    ops_per_second = operation_count / duration if duration > 0 else 0

    # Gather optimization settings
    opt_dict = {
        "tmpfs_size_mb": optimizations.tmpfs_size_mb,
        "fsync_off": optimizations.fsync_off,
        "synchronous_commit_off": optimizations.synchronous_commit_off,
        "full_page_writes_off": optimizations.full_page_writes_off,
        "wal_level_minimal": optimizations.wal_level_minimal,
        "disable_wal_senders": optimizations.disable_wal_senders,
        "disable_archiving": optimizations.disable_archiving,
        "autovacuum_off": optimizations.autovacuum_off,
        "jit_off": optimizations.jit_off,
        "no_locale": optimizations.no_locale,
        "shared_buffers_mb": optimizations.shared_buffers_mb,
        "work_mem_mb": optimizations.work_mem_mb,
        "maintenance_work_mem_mb": optimizations.maintenance_work_mem_mb,
        "checkpoint_timeout_seconds": optimizations.checkpoint_timeout_seconds,
        "disable_statement_logging": optimizations.disable_statement_logging,
    }

    return IOBenchmarkResult(
        scenario=scenario_name,
        config_name=config_name,
        optimizations=opt_dict,
        operation_count=operation_count,
        duration_seconds=duration,
        ops_per_second=ops_per_second,
    )


def run_benchmarks(runs: int = 1) -> list[IOBenchmarkResult]:
    """Run IO benchmarks for different optimization configurations."""
    docker = get_docker()
    results: list[IOBenchmarkResult] = []

    # Define optimization configurations
    configs = [
        (
            "No optimizations",
            Optimizations(
                tmpfs_size_mb=None,
                fsync_off=False,
                synchronous_commit_off=False,
                full_page_writes_off=False,
                wal_level_minimal=False,
                disable_wal_senders=False,
                disable_archiving=False,
                autovacuum_off=False,
                jit_off=False,
                no_locale=False,
                shared_buffers_mb=None,
                checkpoint_timeout_seconds=None,
                disable_statement_logging=False,
            ),
        ),
        (
            "tmpfs + fsync=off + full_page_writes=off",
            Optimizations(
                tmpfs_size_mb=512,
                fsync_off=True,
                synchronous_commit_off=False,
                full_page_writes_off=True,
                wal_level_minimal=False,
                disable_wal_senders=False,
                disable_archiving=False,
                autovacuum_off=False,
                jit_off=False,
                no_locale=False,
                shared_buffers_mb=None,
                checkpoint_timeout_seconds=None,
                disable_statement_logging=False,
            ),
        ),
        ("All optimizations", Optimizations()),
    ]

    # Define scenarios
    scenarios = [
        ("Bulk insert (10k rows)", benchmark_bulk_insert),
        ("Individual inserts (1k rows)", benchmark_individual_inserts),
        ("Random updates (5k rows)", benchmark_random_updates),
        ("Mixed workload (5k+1k ops)", benchmark_mixed_workload),
    ]

    print(f"Running IO benchmarks ({runs} run(s) each)...\n")

    for scenario_name, scenario_func in scenarios:
        print(f"{scenario_name}:")
        for config_name, optimizations in configs:
            print(f"  {config_name}:")
            for i in range(runs):
                if runs > 1:
                    print(f"    Run {i + 1}/{runs}: ", end="", flush=True)
                try:
                    result = benchmark_scenario(
                        docker,
                        config_name,
                        optimizations,
                        f"elefast-io-bench-{hash((scenario_name, config_name, i)) % 1000000}",
                        scenario_name,
                        scenario_func,
                    )
                    results.append(result)
                    print(
                        f"{result.ops_per_second:.0f} ops/sec ({result.duration_seconds:.2f}s)"
                    )
                except Exception as e:
                    print(f"FAILED: {e}")
                    continue
        print()

    return results


def print_summary(results: list[IOBenchmarkResult]) -> None:
    """Print a summary of benchmark results."""
    if not results:
        print("No successful benchmarks to report.")
        return

    print("\n" + "=" * 90)
    print("IO BENCHMARK SUMMARY")
    print("=" * 90 + "\n")

    # Group by scenario
    by_scenario: dict[str, dict[str, list[IOBenchmarkResult]]] = {}
    for result in results:
        if result.scenario not in by_scenario:
            by_scenario[result.scenario] = {}
        if result.config_name not in by_scenario[result.scenario]:
            by_scenario[result.scenario][result.config_name] = []
        by_scenario[result.scenario][result.config_name].append(result)

    for scenario in [
        s[0]
        for s in [
            ("Bulk insert (10k rows)", None),
            ("Individual inserts (1k rows)", None),
            ("Random updates (5k rows)", None),
            ("Mixed workload (5k+1k ops)", None),
        ]
    ]:
        if scenario not in by_scenario:
            continue

        print(f"{scenario}:")
        for config_name in [
            "No optimizations",
            "tmpfs + fsync=off + full_page_writes=off",
            "All optimizations",
        ]:
            if config_name not in by_scenario[scenario]:
                continue

            config_results = by_scenario[scenario][config_name]
            ops_per_sec = [r.ops_per_second for r in config_results]
            avg_ops = sum(ops_per_sec) / len(ops_per_sec)
            min_ops = min(ops_per_sec)
            max_ops = max(ops_per_sec)

            print(f"  {config_name}:")
            print(
                f"    {avg_ops:.0f} ops/sec (avg), {min_ops:.0f} (min), {max_ops:.0f} (max)"
            )

        print()


def main() -> None:
    """Main entry point for IO benchmarks."""
    import argparse

    parser = argparse.ArgumentParser(description="Benchmark PostgreSQL IO operations")
    parser.add_argument(
        "--runs",
        type=int,
        default=1,
        help="Number of times to run each benchmark (default: 1)",
    )

    args = parser.parse_args()

    try:
        results = run_benchmarks(runs=args.runs)
        print_summary(results)
    except KeyboardInterrupt:
        print("\nBenchmark interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Benchmark failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
