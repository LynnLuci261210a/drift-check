"""Ansible-compatible drift report formatter.

Produces output in Ansible's JSON callback format so drift results can be
consumed by existing Ansible tooling and dashboards.
"""
from __future__ import annotations

import json
from typing import List

from drift_check.drift_detector import DriftItem, DriftKind


def _kind_label(kind: DriftKind) -> str:
    return {
        DriftKind.CHANGED: "changed",
        DriftKind.MISSING_LIVE: "missing",
        DriftKind.EXTRA_LIVE: "extra",
    }[kind]


def _task_result(item: DriftItem) -> dict:
    """Convert a single DriftItem into an Ansible task-result-style dict."""
    result: dict = {
        "resource_id": item.resource_id,
        "drift_kind": _kind_label(item.kind),
        "failed": True,
        "msg": f"Drift detected ({_kind_label(item.kind)}): {item.resource_id}",
    }
    if item.diff:
        result["diff"] = {
            "before": {k: v[0] for k, v in item.diff.items()},
            "after": {k: v[1] for k, v in item.diff.items()},
        }
    return result


def render_ansible(items: List[DriftItem]) -> str:
    """Render drift items as an Ansible JSON callback-style payload.

    The top-level object mirrors the structure emitted by Ansible's
    ``json`` stdout callback plugin so the output can be parsed by the
    same consumers.
    """
    tasks = [_task_result(item) for item in items]

    total = len(items)
    changed = sum(1 for i in items if i.kind == DriftKind.CHANGED)
    missing = sum(1 for i in items if i.kind == DriftKind.MISSING_LIVE)
    extra = sum(1 for i in items if i.kind == DriftKind.EXTRA_LIVE)

    payload = {
        "plays": [
            {
                "play": {"name": "drift-check", "id": "drift-check-1"},
                "tasks": [
                    {
                        "task": {"name": "infrastructure drift", "id": f"task-{idx}"},
                        "hosts": {result["resource_id"]: result},
                    }
                    for idx, result in enumerate(tasks)
                ],
            }
        ],
        "stats": {
            "drift-check": {
                "changed": changed,
                "failures": missing + extra,
                "ignored": 0,
                "ok": 0 if total else 1,
                "rescued": 0,
                "skipped": 0,
                "unreachable": 0,
            }
        },
    }
    return json.dumps(payload, indent=2)
