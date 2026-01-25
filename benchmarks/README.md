# elefast Benchmarks

Benchmarking tools for measuring performance characteristics of elefast components.

## Available Benchmarks

### `bench-db-startup`

Benchmark PostgreSQL container startup performance with various optimization configurations.

### `bench-io`

Benchmark PostgreSQL IO operation performance with various optimization configurations.

This benchmark measures:
- **Startup time**: Time to create and start the Docker container
- **Connection time**: Time to establish a PostgreSQL connection
- **Total time**: Combined startup and connection time

#### Usage

```bash
# Single run for each configuration
bench-db-startup

# Multiple runs to measure consistency
bench-db-startup --runs 3
```

#### `bench-io` Measured Scenarios

1. **Bulk insert**: 10k rows in a single transaction
2. **Individual inserts**: 1k rows with separate transactions
3. **Random updates**: 5k random row updates with individual transactions
4. **Mixed workload**: Setup 5k bulk inserts, then 500 inserts + 300 updates + 200 deletes

#### Usage

```bash
# Single run for each scenario/configuration
bench-io

# Multiple runs to measure consistency
bench-io --runs 3
```

#### Tested Configurations

1. **No optimizations**: All optimizations disabled (baseline disk-based approach)
2. **tmpfs + fsync=off + full_page_writes=off**: Minimal set of meaningful optimizations
3. **All optimizations**: Full configuration (default elefast behavior)

#### Notes

- Each benchmark cleans up its containers after completion
- Ensure Docker is running and accessible before running benchmarks
- The first run of a configuration may be slower due to image pulls/caching
- Results are influenced by system load and available resources
