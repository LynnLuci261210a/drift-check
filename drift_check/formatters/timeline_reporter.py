"""Timeline reporter – renders drift items as a chronological HTML timeline."""
from __future__ import annotations

import html
from datetime import datetime, timezone
from typing import List

from drift_check.drift_detector import DriftItem, DriftKind

_KIND_COLOUR = {
    DriftKind.CHANGED: "#f0ad4e",
    DriftKind.MISSING_LIVE: "#d9534f",
    DriftKind.EXTRA_LIVE: "#5bc0de",
}

_KIND_LABEL = {
    DriftKind.CHANGED: "changed",
    DriftKind.MISSING_LIVE: "missing",
    DriftKind.EXTRA_LIVE: "extra",
}


def _event_block(item: DriftItem, index: int) -> str:
    colour = _KIND_COLOUR.get(item.kind, "#999")
    label = _KIND_LABEL.get(item.kind, "unknown")
    rid = html.escape(item.resource_id)
    detail_rows = ""
    if item.diff:
        rows = "".join(
            f"<tr><td><code>{html.escape(k)}</code></td>"
            f"<td>{html.escape(str(v.get('terraform', '')))}</td>"
            f"<td>{html.escape(str(v.get('live', '')))}</td></tr>"
            for k, v in item.diff.items()
        )
        detail_rows = (
            "<table class='diff'><thead><tr>"
            "<th>Attribute</th><th>Terraform</th><th>Live</th>"
            f"</tr></thead><tbody>{rows}</tbody></table>"
        )
    side = "left" if index % 2 == 0 else "right"
    return (
        f"<div class='event {side}' style='--accent:{colour}'>"
        f"<span class='badge'>{label}</span>"
        f"<strong>{rid}</strong>"
        f"{detail_rows}"
        "</div>"
    )


def render_timeline(items: List[DriftItem]) -> str:
    """Return a self-contained HTML timeline page."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    total = len(items)
    body = "".join(_event_block(it, i) for i, it in enumerate(items))
    if not body:
        body = "<p class='ok'>&#10003; No drift detected.</p>"

    return f"""<!DOCTYPE html>
<html lang='en'><head><meta charset='utf-8'>
<title>Drift Timeline</title>
<style>
body{{font-family:sans-serif;margin:2rem}}
.timeline{{position:relative;padding:1rem 0}}
.timeline::before{{content:'';position:absolute;left:50%;top:0;bottom:0;width:2px;background:#ccc}}
.event{{position:relative;width:44%;padding:1rem;margin-bottom:1.5rem;border-left:4px solid var(--accent);background:#fafafa;border-radius:4px}}
.event.right{{margin-left:52%}}
.event.left{{margin-left:2%}}
.badge{{display:inline-block;padding:.2rem .5rem;border-radius:3px;font-size:.75rem;background:var(--accent);color:#fff;margin-bottom:.4rem}}
table.diff{{width:100%;font-size:.8rem;border-collapse:collapse;margin-top:.5rem}}
table.diff th,table.diff td{{border:1px solid #ddd;padding:.3rem .5rem;text-align:left}}
table.diff th{{background:#f0f0f0}}
.ok{{color:green;font-size:1.2rem}}
</style></head>
<body>
<h1>Drift Timeline</h1>
<p>Generated: {ts} &mdash; {total} item(s)</p>
<div class='timeline'>{body}</div>
</body></html>
"""
