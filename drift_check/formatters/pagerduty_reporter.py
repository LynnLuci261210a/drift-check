"""PagerDuty Events API v2 payload formatter for drift results."""
from __future__ import annotations

from typing import List

from drift_check.drift_detector import DriftItem, DriftKind

_SEVERITY = {
    DriftKind.CHANGED: "warning",
    DriftKind.MISSING_LIVE: "critical",
    DriftKind.EXTRA_LIVE: "info",
}


def _alert_summary(item: DriftItem) -> str:
    """Return a short human-readable summary line for a drift item."""
    if item.kind == DriftKind.CHANGED:
        attrs = ", ".join(item.diff.keys()) if item.diff else "unknown"
        return f"Drift detected on {item.resource_id}: changed attributes [{attrs}]"
    if item.kind == DriftKind.MISSING_LIVE:
        return f"Resource {item.resource_id} defined in Terraform but missing from live infra"
    return f"Resource {item.resource_id} exists in live infra but not in Terraform"


def _payload(item: DriftItem, source: str) -> dict:
    """Build a single PagerDuty Events API v2 payload dict."""
    details: dict = {"resource_id": item.resource_id, "kind": item.kind.value}
    if item.diff:
        details["diff"] = {
            attr: {"terraform": v["terraform"], "live": v["live"]}
            for attr, v in item.diff.items()
        }
    return {
        "routing_key": "",  # caller must inject the real integration key
        "event_action": "trigger",
        "payload": {
            "summary": _alert_summary(item),
            "source": source,
            "severity": _SEVERITY.get(item.kind, "warning"),
            "custom_details": details,
        },
    }


def render_pagerduty(
    items: List[DriftItem],
    source: str = "drift-check",
) -> dict:
    """Return a dict with a list of PagerDuty event payloads.

    If there are no drift items an empty ``events`` list is returned so the
    caller can still inspect the structure without sending noisy alerts.
    """
    return {
        "source": source,
        "total_drift": len(items),
        "events": [_payload(item, source) for item in items],
    }
