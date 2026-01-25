"""Tests for optimization documentation completeness."""

from dataclasses import fields

from elefast.docker.configuration import Optimizations
from elefast.docker.optimization_docs import OPTIMIZATION_DOCS


def test_all_optimizations_documented():
    """Ensure every Optimization field has metadata documentation."""
    optimization_fields = {f.name for f in fields(Optimizations)}
    documented_fields = set(OPTIMIZATION_DOCS.keys())

    missing = optimization_fields - documented_fields
    assert not missing, f"Optimizations missing documentation: {missing}"

    extra = documented_fields - optimization_fields
    assert not extra, f"Documentation for non-existent optimizations: {extra}"
