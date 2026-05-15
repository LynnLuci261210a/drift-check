"""Filtering utilities for drift results."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence

from drift_check.drift_detector import DriftItem, DriftKind


@dataclass
class FilterOptions:
    """Options that control which drift items are surfaced."""

    resource_types: Optional[Sequence[str]] = None
    """Only include items whose resource_id starts with one of these prefixes."""

    kinds: Optional[Sequence[DriftKind]] = None
    """Only include items whose DriftKind is in this list."""

    attribute_names: Optional[Sequence[str]] = None
    """Only include CHANGED items that touch at least one of these attribute names."""


def _matches_resource_type(item: DriftItem, prefixes: Sequence[str]) -> bool:
    return any(item.resource_id.startswith(p) for p in prefixes)


def _matches_attribute(item: DriftItem, names: Sequence[str]) -> bool:
    if item.kind != DriftKind.CHANGED:
        return True
    return any(attr in item.diff for attr in names)


def apply_filters(items: Iterable[DriftItem], opts: FilterOptions) -> List[DriftItem]:
    """Return a filtered list of DriftItems according to *opts*.

    Each active filter must match for an item to be included (AND semantics).
    An option set to *None* means "no restriction" for that dimension.
    """
    result: List[DriftItem] = []
    for item in items:
        if opts.resource_types is not None:
            if not _matches_resource_type(item, opts.resource_types):
                continue
        if opts.kinds is not None:
            if item.kind not in opts.kinds:
                continue
        if opts.attribute_names is not None:
            if not _matches_attribute(item, opts.attribute_names):
                continue
        result.append(item)
    return result
