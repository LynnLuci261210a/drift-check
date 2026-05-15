"""Formatters package for drift-check.

Provides pluggable output formatters beyond the core text/JSON reporters.
Each formatter module exposes a render_* function that accepts a sequence
of DriftItem objects and returns a formatted string.
"""
from __future__ import annotations

from drift_check.formatters.html_reporter import render_html
from drift_check.formatters.csv_reporter import render_csv
from drift_check.formatters.markdown_reporter import render_markdown

__all__ = [
    "render_html",
    "render_csv",
    "render_markdown",
]
