"""Formatter registry for drift-check output formats."""
from __future__ import annotations

from typing import Callable, Dict, List

from drift_check.drift_detector import DriftItem

_REGISTRY: Dict[str, str] = {
    "html": "drift_check.formatters.html_reporter:render_html",
    "csv": "drift_check.formatters.csv_reporter:render_csv",
    "markdown": "drift_check.formatters.markdown_reporter:render_markdown",
    "junit": "drift_check.formatters.junit_reporter:render_junit",
    "slack": "drift_check.formatters.slack_reporter:render_slack",
    "sarif": "drift_check.formatters.sarif_reporter:render_sarif",
    "excel": "drift_check.formatters.excel_reporter:render_excel",
    "pdf": "drift_check.formatters.pdf_reporter:render_pdf",
    "yaml": "drift_check.formatters.yaml_reporter:render_yaml",
    "prometheus": "drift_check.formatters.prometheus_reporter:render_prometheus",
    "graphite": "drift_check.formatters.graphite_reporter:render_graphite",
    "influxdb": "drift_check.formatters.influxdb_reporter:render_influxdb",
    "datadog": "drift_check.formatters.datadog_reporter:render_datadog",
    "opsgenie": "drift_check.formatters.opsgenie_reporter:render_opsgenie",
    "splunk": "drift_check.formatters.splunk_reporter:render_splunk",
    "newrelic": "drift_check.formatters.newrelic_reporter:render_newrelic",
    "syslog": "drift_check.formatters.syslog_reporter:render_syslog",
    "pagerduty": "drift_check.formatters.pagerduty_reporter:render_pagerduty",
    "webhook": "drift_check.formatters.webhook_reporter:render_webhook",
    "dotenv": "drift_check.formatters.dotenv_reporter:render_dotenv",
    "teamcity": "drift_check.formatters.teamcity_reporter:render_teamcity",
    "ndjson": "drift_check.formatters.ndjson_reporter:render_ndjson",
    "terraform": "drift_check.formatters.terraform_reporter:render_terraform",
    "sonarqube": "drift_check.formatters.sonarqube_reporter:render_sonarqube",
    "azure_devops": "drift_check.formatters.azure_devops_reporter:render_azure_devops",
    "github": "drift_check.formatters.github_reporter:render_github",
}


def get_available_formatters() -> List[str]:
    """Return the names of all registered output formatters."""
    return list(_REGISTRY.keys())


def get_formatter(name: str) -> Callable[[List[DriftItem]], str]:
    """Return the render callable for *name*.

    Raises
    ------
    KeyError
        If *name* is not a registered formatter.
    """
    if name not in _REGISTRY:
        raise KeyError(f"Unknown formatter: {name!r}. Available: {get_available_formatters()}")

    module_path, func_name = _REGISTRY[name].rsplit(":", 1)
    import importlib
    module = importlib.import_module(module_path)
    return getattr(module, func_name)  # type: ignore[return-value]
