"""Formatter registry for drift-check output formats."""
from __future__ import annotations


def get_available_formatters() -> list[str]:
    """Return the list of all registered output format names."""
    return [
        "text",
        "json",
        "html",
        "csv",
        "markdown",
        "junit",
        "slack",
        "sarif",
        "excel",
        "pdf",
        "yaml",
        "prometheus",
        "graphite",
        "influxdb",
        "datadog",
        "opsgenie",
        "splunk",
        "newrelic",
        "syslog",
        "pagerduty",
        "webhook",
        "dotenv",
        "teamcity",
    ]
