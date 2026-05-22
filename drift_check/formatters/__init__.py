"""Formatters package for drift-check output renderers."""

from typing import List


def get_available_formatters() -> List[str]:
    """Return a list of available formatter names.

    Returns:
        A list of strings representing the names of all registered formatters.
    """
    return ["text", "json", "yaml"]
