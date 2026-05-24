"""JUnit XML formatter — alias kept for back-compat; delegates to junit_reporter."""
from drift_check.formatters.junit_reporter import render_junit as render_junit_xml  # noqa: F401
