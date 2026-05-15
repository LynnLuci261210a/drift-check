"""Slack-compatible JSON payload renderer for drift reports."""
from __future__ import annotations

import json
from typing import List

from drift_check.drift_detector import DriftItem, DriftKind

_KIND_EMOJI = {
    DriftKind.CHANGED: ":warning:",
    DriftKind.MISSING: ":x:",
    DriftKind.EXTRA: ":heavy_plus_sign:",
}

_KIND_COLOR = {
    DriftKind.CHANGED: "#FFA500",
    DriftKind.MISSING: "#FF0000",
    DriftKind.EXTRA: "#439FE0",
}


def _attachment(item: DriftItem) -> dict:
    emoji = _KIND_EMOJI.get(item.kind, ":grey_question:")
    color = _KIND_COLOR.get(item.kind, "#CCCCCC")
    title = f"{emoji} `{item.resource_id}` — {item.kind.value}"

    fields = []
    for attr, (expected, actual) in (item.attribute_diff or {}).items():
        fields.append(
            {
                "title": attr,
                "value": f"expected: `{expected}`\nactual: `{actual}`",
                "short": False,
            }
        )

    return {
        "color": color,
        "title": title,
        "fields": fields,
        "footer": "drift-check",
    }


def render_slack(items: List[DriftItem]) -> str:
    """Return a Slack Block Kit-compatible JSON string.

    Produces a payload suitable for posting to a Slack incoming webhook.
    """
    if not items:
        payload = {
            "text": ":white_check_mark: No infrastructure drift detected."
        }
        return json.dumps(payload, indent=2)

    attachments = [_attachment(item) for item in items]
    payload = {
        "text": f":rotating_light: Drift detected in *{len(items)}* resource(s).",
        "attachments": attachments,
    }
    return json.dumps(payload, indent=2)
