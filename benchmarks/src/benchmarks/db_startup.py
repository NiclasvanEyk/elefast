"""Benchmark PostgreSQL container startup with various optimization configurations."""

import sys
import time
from dataclasses import dataclass, replace

import psycopg2
from docker import DockerClient

from elefast.docker.configuration import Configuration, Optimizations
from elefast.docker.orchestration import (
    ensure_db_server_started,
    get_docker,
    get_db_server_container,
)


@dataclass
class StartupBenchmarkResult:
    """Result of a single startup benchmark run."""

    name: str
    optimizations: dict[str, bool | int | None]
    startup_time: float
    connection_time: float
    total_time: float


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
) -> float:
    """Wait for PostgreSQL to be ready and return connection time.

    Returns:
        The time taken to establish a successful connection
    """
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
            return time.time() - start
        except psycopg2.OperationalError:
            time.sleep(poll_interval)

    raise TimeoutError(f"PostgreSQL did not become ready after {timeout} seconds")


def benchmark_startup_config(
    docker: DockerClient,
    config_name: str,
    optimizations: Optimizations,
    container_name: str,
) -> StartupBenchmarkResult:
    """Benchmark a single optimization configuration."""
    print(f"  Benchmarking: {config_name}...", end=" ", flush=True)

    # Clean up any existing container
    cleanup_container(docker, container_name)

    config = Configuration(
        container=replace(
            Configuration().container,
            name=container_name,
        ),
        optimizations=optimizations,
    )

    # Measure startup time
    start = time.time()
    container, host_port = ensure_db_server_started(
        docker=docker,
        config=config,
        keep_container_around=True,
    )
    startup_time = time.time() - start

    # Measure connection time (wait for postgres to be ready)
    credentials = config.credentials
    try:
        connection_time = wait_for_postgres(
            host=credentials.host,
            port=host_port,
            user=credentials.user,
            password=credentials.password,
            timeout=60,
        )
    except Exception as e:
        print(f"FAILED\n    Error: {e}")
        cleanup_container(docker, container_name)
        raise

    total_time = startup_time + connection_time

    print(
        f"{total_time:.2f}s (startup: {startup_time:.2f}s, connect: {connection_time:.2f}s)"
    )

    # Clean up after benchmark
    cleanup_container(docker, container_name)

    # Gather optimization settings for reporting
    opt_dict = {
        "tmpfs": optimizations.tmpfs,
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

    return StartupBenchmarkResult(
        name=config_name,
        optimizations=opt_dict,
        startup_time=startup_time,
        connection_time=connection_time,
        total_time=total_time,
    )


def run_benchmarks(runs: int = 1) -> list[StartupBenchmarkResult]:
    """Run startup benchmarks for different optimization configurations."""
    docker = get_docker()
    results: list[StartupBenchmarkResult] = []

    # Define benchmark configurations
    configs = [
        (
            "No optimizations (disk storage)",
            Optimizations(
                tmpfs=False,
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
            "tmpfs (512MB) + fsync=off + full_page_writes=off",
            Optimizations(
                tmpfs=512,
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
        ("All optimizations (auto-sized tmpfs)", Optimizations()),
    ]

    print(f"Running startup benchmarks ({runs} run(s) each)...\n")

    for config_name, optimizations in configs:
        print(f"{config_name}:")
        for i in range(runs):
            if runs > 1:
                print(f"  Run {i + 1}/{runs}: ", end="", flush=True)
            try:
                result = benchmark_startup_config(
                    docker,
                    config_name,
                    optimizations,
                    f"elefast-bench-{hash(config_name) % 1000000}-{i}",
                )
                results.append(result)
            except Exception as e:
                print(f"FAILED: {e}")
                continue
        print()

    return results


def print_summary(results: list[StartupBenchmarkResult]) -> None:
    """Print a summary of benchmark results."""
    if not results:
        print("No successful benchmarks to report.")
        return

    print("\n" + "=" * 80)
    print("BENCHMARK SUMMARY")
    print("=" * 80 + "\n")

    # Group by configuration
    by_config: dict[str, list[StartupBenchmarkResult]] = {}
    for result in results:
        if result.name not in by_config:
            by_config[result.name] = []
        by_config[result.name].append(result)

    for config_name, config_results in by_config.items():
        print(f"{config_name}:")
        total_times = [r.total_time for r in config_results]
        avg_total = sum(total_times) / len(total_times)
        min_total = min(total_times)
        max_total = max(total_times)

        startup_times = [r.startup_time for r in config_results]
        avg_startup = sum(startup_times) / len(startup_times)

        connection_times = [r.connection_time for r in config_results]
        avg_connection = sum(connection_times) / len(connection_times)

        print(
            f"  Total time:      {avg_total:.2f}s (avg), {min_total:.2f}s (min), {max_total:.2f}s (max)"
        )
        print(f"  Startup time:    {avg_startup:.2f}s (avg)")
        print(f"  Connection time: {avg_connection:.2f}s (avg)")
        print()


def main() -> None:
    """Main entry point for db startup benchmarks."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Benchmark PostgreSQL container startup"
    )
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
