"""Rich-coloured console reporter for interactive terminal output."""
from __future__ import annotations

from typing import List

from drift_check.drift_detector import DriftItem, DriftKind

_RESET = "\033[0m"
_BOLD = "\033[1m"
_RED = "\033[31m"
_YELLOW = "\033[33m"
_CYAN = "\033[36m"
_GREEN = "\033[32m"
_DIM = "\033[2m"


def _kind_colour(kind: DriftKind) -> str:
    return {
        DriftKind.CHANGED: _YELLOW,
        DriftKind.MISSING_LIVE: _RED,
        DriftKind.EXTRA_LIVE: _CYAN,
    }.get(kind, _RESET)


def _kind_label(kind: DriftKind) -> str:
    return {
        DriftKind.CHANGED: "CHANGED",
        DriftKind.MISSING_LIVE: "MISSING",
        DriftKind.EXTRA_LIVE: "EXTRA",
    }.get(kind, str(kind))


def _header(text: str) -> str:
    bar = "─" * len(text)
    return f"{_BOLD}{text}{_RESET}\n{_DIM}{bar}{_RESET}"


def render_console(items: List[DriftItem], *, colour: bool = True) -> str:
    """Return an ANSI-coloured console report string.

    Parameters
    ----------
    items:
        Drift items produced by :func:`drift_check.drift_detector.detect_drift`.
    colour:
        When *False* all ANSI escape codes are suppressed (useful for
        non-interactive streams or tests that inspect raw text).
    """
    def c(code: str) -> str:  # noqa: ANN202
        return code if colour else ""

    if not items:
        return (
            f"{c(_BOLD)}{c(_GREEN)}✔ No drift detected.{c(_RESET)}\n"
        )

    lines: list[str] = [_header("Drift Report") if colour else "Drift Report", ""]

    for item in items:
        colour_code = _kind_colour(item.kind)
        label = _kind_label(item.kind)
        lines.append(
            f"  {c(_BOLD)}{c(colour_code)}[{label}]{c(_RESET)}"
            f"  {c(_BOLD)}{item.resource_id}{c(_RESET)}"
        )
        if item.attribute:
            lines.append(f"    attribute : {item.attribute}")
        if item.expected is not None:
            lines.append(f"    expected  : {c(_GREEN)}{item.expected}{c(_RESET)}")
        if item.actual is not None:
            lines.append(f"    actual    : {c(_RED)}{item.actual}{c(_RESET)}")
        lines.append("")

    changed = sum(1 for i in items if i.kind == DriftKind.CHANGED)
    missing = sum(1 for i in items if i.kind == DriftKind.MISSING_LIVE)
    extra = sum(1 for i in items if i.kind == DriftKind.EXTRA_LIVE)

    lines.append(
        f"{c(_DIM)}Summary:{c(_RESET)} "
        f"{c(_YELLOW)}{changed} changed{c(_RESET)}, "
        f"{c(_RED)}{missing} missing{c(_RESET)}, "
        f"{c(_CYAN)}{extra} extra{c(_RESET)}"
    )
    return "\n".join(lines) + "\n"
