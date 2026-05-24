"""Registry integration tests for the timeline formatter."""
import pytest
from drift_check.drift_detector import DriftItem, DriftKind
from drift_check.formatters import get_available_formatters, get_formatter


def test_timeline_is_listed():
    assert "timeline" in get_available_formatters()


def test_get_formatter_returns_callable():
    fn = get_formatter("timeline")
    assert callable(fn)


def test_get_formatter_no_drift_produces_string():
    fn = get_formatter("timeline")
    result = fn([])
    assert isinstance(result, str)
    assert len(result) > 0


def test_get_formatter_no_drift_is_valid_html():
    fn = get_formatter("timeline")
    result = fn([])
    assert "<!DOCTYPE html>" in result
    assert "</html>" in result


def test_get_formatter_with_drift_contains_resource_id():
    fn = get_formatter("timeline")
    items = [
        DriftItem(
            resource_id="aws_instance.test",
            kind=DriftKind.CHANGED,
            diff={"instance_type": {"terraform": "t2.micro", "live": "t3.small"}},
        )
    ]
    result = fn(items)
    assert "aws_instance.test" in result


def test_unknown_formatter_raises_key_error():
    with pytest.raises(KeyError):
        get_formatter("does_not_exist_xyz")
