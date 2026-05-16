"""Syslog-compatible formatter for drift results.

Produces RFC-5424-style log lines suitable for forwarding to a syslog
daemon or SIEM.  Each drift item becomes one line; a summary line is
always appended.
"""
from __future__ import annotations

import datetime
from typing import List

from drift_check.drift_detector import DriftItem, DriftKind

_SEVERITY = {
    DriftKind.CHANGED: "WARNING",
    DriftKind.MISSING_LIVE: "ERROR",
    DriftKind.EXTRA_LIVE: "NOTICE",
}

APP_NAME = "drift-check"
FACILITY = 1   # user-level messages
_SEV_CODE = {"EMERGENCY": 0, "ALERT": 1, "CRITICAL": 2, "ERROR": 3,
             "WARNING": 4, "NOTICE": 5, "INFO": 6, "DEBUG": 7}


def _pri(severity: str) -> int:
    return FACILITY * 8 + _SEV_CODE.get(severity, 6)


def _timestamp() -> str:
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _rfc5424_line(severity: str, msg_id: str, message: str) -> str:
    pri = _pri(severity)
    ts = _timestamp()
    return (
        f"<{pri}>1 {ts} - {APP_NAME} - {msg_id} - "
        + message
    )


def render_syslog(items: List[DriftItem]) -> str:
    """Return newline-separated RFC-5424 log lines for *items*."""
    lines: List[str] = []

    for item in items:
        severity = _SEVERITY.get(item.kind, "INFO")
        if item.kind == DriftKind.CHANGED:
            diff_parts = "; ".join(
                f"{k}: {v['terraform']!r} -> {v['live']!r}"
                for k, v in (item.diff or {}).items()
            )
            message = (
                f"CHANGED resource_id={item.resource_id!r} "
                f"resource_type={item.resource_type!r} diff=[{diff_parts}]"
            )
        elif item.kind == DriftKind.MISSING_LIVE:
            message = (
                f"MISSING_LIVE resource_id={item.resource_id!r} "
                f"resource_type={item.resource_type!r}"
            )
        else:
            message = (
                f"EXTRA_LIVE resource_id={item.resource_id!r} "
                f"resource_type={item.resource_type!r}"
            )
        lines.append(_rfc5424_line(severity, item.kind.value, message))

    changed = sum(1 for i in items if i.kind == DriftKind.CHANGED)
    missing = sum(1 for i in items if i.kind == DriftKind.MISSING_LIVE)
    extra = sum(1 for i in items if i.kind == DriftKind.EXTRA_LIVE)
    summary_sev = "INFO" if not items else "WARNING"
    summary_msg = (
        f"SUMMARY total={len(items)} changed={changed} "
        f"missing={missing} extra={extra}"
    )
    lines.append(_rfc5424_line(summary_sev, "SUMMARY", summary_msg))

    return "\n".join(lines)
