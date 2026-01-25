#!/usr/bin/env -S uv run
"""Generate optimization documentation from the optimization registry.

This script generates docs/optimizations.md from the OPTIMIZATION_DOCS registry
in elefast.docker.optimization_docs.

Usage:
    python scripts/generate_optimization_docs.py
"""

import sys
from pathlib import Path

# Add src to path so we can import elefast
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import directly to avoid loading other dependencies
import importlib.util
from dataclasses import fields

spec = importlib.util.spec_from_file_location(
    "optimization_docs",
    Path(__file__).parent.parent
    / "src"
    / "elefast"
    / "docker"
    / "optimization_docs.py",
)
optimization_docs_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(optimization_docs_module)
OPTIMIZATION_DOCS = optimization_docs_module.OPTIMIZATION_DOCS

# Import configuration to get default values
spec_config = importlib.util.spec_from_file_location(
    "configuration",
    Path(__file__).parent.parent / "src" / "elefast" / "docker" / "configuration.py",
)
configuration_module = importlib.util.module_from_spec(spec_config)
spec_config.loader.exec_module(configuration_module)

# Get default Optimizations instance to extract defaults
DEFAULT_OPTIMIZATIONS = configuration_module.Optimizations()
OPTIMIZATION_DEFAULTS = {
    f.name: getattr(DEFAULT_OPTIMIZATIONS, f.name)
    for f in fields(DEFAULT_OPTIMIZATIONS)
}


def generate_markdown() -> str:
    """Generate markdown documentation from OPTIMIZATION_DOCS registry."""
    lines = [
        "---",
        "icon: lucide/wrench",
        "---",
        "",
        "<!-- AUTO-GENERATED FILE: DO NOT EDIT MANUALLY -->",
        "<!-- Run `uv run scripts/generate_optimization_docs.py` to regenerate -->",
        "",
        "# Optimizations",
        "",
        "This document describes all available optimization settings for the Docker PostgreSQL container.",
        "",
        "## Why Test Databases Are Different",
        "",
        "Production PostgreSQL instances prioritize data durability, crash recovery, and handling",
        "concurrent workloads from multiple applications. Test databases have fundamentally different",
        "requirements:",
        "",
        "- **Isolation**: Test databases are ephemeral—they're created per test run and discarded",
        "  afterward. Data doesn't need to survive container restarts or crashes.",
        "- **Sequential workloads**: Tests run serially within a process, not concurrent requests from",
        "  multiple users. Heavy durability guarantees are unnecessary overhead.",
        "- **Speed is paramount**: Slow tests mean slow feedback loops for developers. Optimizing for",
        "  test speed directly improves developer experience.",
        "- **No recovery requirements**: Production needs crash recovery and point-in-time restore.",
        "  Tests just need to spin up fresh.",
        "",
        "Elefast exploits these differences by disabling features like fsync, WAL archiving, and",
        "replication, storing the entire database in RAM, and tuning PostgreSQL aggressively for",
        "speed. These optimizations are **not safe for production**, but perfect for testing.",
        "",
        "## Available Optimizations",
        "",
        "The settings below reduce disk I/O, memory overhead, and background work at the cost",
        "of durability guarantees and crash recovery. All are safe for isolated test databases",
        "that don't need to survive container restarts.",
        "",
        "## Overview",
        "",
        "| Setting | Default | Risk | Description |",
        "|---------|---------|------|-------------|",
    ]

    # Add table rows
    for name, info in sorted(OPTIMIZATION_DOCS.items()):
        risk_emoji = (
            "🟢" if info.risk_factor < 0.3 else "🟡" if info.risk_factor < 0.6 else "🔴"
        )
        first_line = info.gain.split(".")[0] + "."
        default_value = OPTIMIZATION_DEFAULTS.get(name)
        lines.append(f"| `{name}` | `{default_value}` | {risk_emoji} | {first_line} |")

    lines.extend(
        [
            "",
            "**Risk levels:** 🟢 Low (< 0.3) | 🟡 Medium (0.3-0.6) | 🔴 High (> 0.6)",
            "",
            "## Settings",
            "",
        ]
    )

    # Add detailed sections for each setting
    for name, info in sorted(OPTIMIZATION_DOCS.items()):
        risk_emoji = (
            "🟢" if info.risk_factor < 0.3 else "🟡" if info.risk_factor < 0.6 else "🔴"
        )
        default_value = OPTIMIZATION_DEFAULTS.get(name)
        lines.extend(
            [
                f"### {risk_emoji} `{name}`",
                "",
                f"**Risk Factor:** {info.risk_factor}",
                "",
                "**Gain**",
                "",
                f"{info.gain}",
                "",
                "**Potential Issues**",
                "",
                f"{info.risk}",
                "",
            ]
        )

    return "\n".join(lines)


def main() -> None:
    """Generate and write optimization documentation."""
    docs_dir = Path(__file__).parent.parent / "docs"
    docs_dir.mkdir(exist_ok=True)

    output_file = docs_dir / "optimizations.md"
    content = generate_markdown()

    output_file.write_text(content)
    print(f"✓ Generated {output_file}")


if __name__ == "__main__":
    main()
