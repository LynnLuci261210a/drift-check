"""Tests for the PDF report formatter."""
from __future__ import annotations

import importlib
import sys
from unittest.mock import MagicMock, patch

import pytest

from drift_check.drift_detector import DriftItem, DriftKind


@pytest.fixture()
def changed_item() -> DriftItem:
    return DriftItem(
        resource_id="aws_instance.web",
        kind=DriftKind.CHANGED,
        diff={"instance_type": ("t2.micro", "t3.small")},
    )


@pytest.fixture()
def missing_item() -> DriftItem:
    return DriftItem(
        resource_id="aws_s3_bucket.logs",
        kind=DriftKind.MISSING_LIVE,
        diff=None,
    )


@pytest.fixture()
def extra_item() -> DriftItem:
    return DriftItem(
        resource_id="aws_instance.ghost",
        kind=DriftKind.EXTRA_LIVE,
        diff=None,
    )


def _make_mock_reportlab():
    """Return a minimal mock of the reportlab package hierarchy."""
    rl = MagicMock()
    buf_instance = MagicMock()
    buf_instance.getvalue.return_value = b"%PDF-mock"
    rl.platypus.SimpleDocTemplate.return_value.build = MagicMock()
    return rl, buf_instance


def _render(items):
    """Import and call render_pdf, ensuring reportlab is importable."""
    pytest.importorskip("reportlab")
    from drift_check.formatters.pdf_reporter import render_pdf
    return render_pdf(items)


class TestRenderPdf:
    def test_no_drift_returns_bytes(self):
        result = _render([])
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_no_drift_contains_pdf_header(self):
        result = _render([])
        assert result[:4] == b"%PDF"

    def test_changed_item_returns_bytes(self, changed_item):
        result = _render([changed_item])
        assert isinstance(result, bytes)
        assert result[:4] == b"%PDF"

    def test_missing_item_returns_bytes(self, missing_item):
        result = _render([missing_item])
        assert isinstance(result, bytes)

    def test_extra_item_returns_bytes(self, extra_item):
        result = _render([extra_item])
        assert isinstance(result, bytes)

    def test_multiple_items_returns_bytes(self, changed_item, missing_item, extra_item):
        result = _render([changed_item, missing_item, extra_item])
        assert isinstance(result, bytes)
        assert result[:4] == b"%PDF"

    def test_raises_when_reportlab_missing(self, changed_item):
        """render_pdf should raise RuntimeError if reportlab is not installed."""
        import drift_check.formatters.pdf_reporter as mod

        original = mod._REPORTLAB_AVAILABLE
        try:
            mod._REPORTLAB_AVAILABLE = False
            with pytest.raises(RuntimeError, match="reportlab"):
                mod.render_pdf([changed_item])
        finally:
            mod._REPORTLAB_AVAILABLE = original
