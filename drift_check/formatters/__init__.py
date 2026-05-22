"""Formatter registry for drift-check output formats."""
from __future__ import annotations

from typing import Callable, Dict, List

from drift_check.formatters.csv_reporter import render_csv
from drift_check.formatters.datadog_reporter import render_datadog
from drift_check.formatters.dotenv_reporter import render_dotenv
from drift_check.formatters.excel_reporter import render_excel
from drift_check.formatters.graphite_reporter import render_graphite
from drift_check.formatters.html_reporter import render_html
from drift_check.formatters.influxdb_reporter import render_influxdb
from drift_check.formatters.junit_reporter import render_junit
from drift_check.formatters.markdown_reporter import render_markdown
from drift_check.formatters.ndjson_reporter import render_ndjson
from drift_check.formatters.newrelic_reporter import render_newrelic
from drift_check.formatters.opsgenie_reporter import render_opsgenie
from drift_check.formatters.pagerduty_reporter import render_pagerduty
from drift_check.formatters.pdf_reporter import render_pdf
from drift_check.formatters.prometheus_reporter import render_prometheus
from drift_check.formatters.sarif_reporter import render_sarif
from drift_check.formatters.slack_reporter import render_slack
from drift_check.formatters.splunk_reporter import render_splunk
from drift_check.formatters.syslog_reporter import render_syslog
from drift_check.formatters.teamcity_reporter import render_teamcity
from drift_check.formatters.terraform_reporter import render_terraform
from drift_check.formatters.webhook_reporter import render_webhook
from drift_check.formatters.yaml_reporter import render_yaml

_REGISTRY: Dict[str, Callable] = {
    "csv": render_csv,
    "datadog": render_datadog,
    "dotenv": render_dotenv,
    "excel": render_excel,
    "graphite": render_graphite,
    "html": render_html,
    "influxdb": render_influxdb,
    "junit": render_junit,
    "markdown": render_markdown,
    "ndjson": render_ndjson,
    "newrelic": render_newrelic,
    "opsgenie": render_opsgenie,
    "pagerduty": render_pagerduty,
    "pdf": render_pdf,
    "prometheus": render_prometheus,
    "sarif": render_sarif,
    "slack": render_slack,
    "splunk": render_splunk,
    "syslog": render_syslog,
    "teamcity": render_teamcity,
    "terraform": render_terraform,
    "webhook": render_webhook,
    "yaml": render_yaml,
}


def get_available_formatters() -> List[str]:
    """Return sorted list of registered formatter names."""
    return sorted(_REGISTRY.keys())


def get_formatter(name: str) -> Callable:
    """Return formatter callable by name, raising KeyError if unknown."""
    if name not in _REGISTRY:
        available = ", ".join(get_available_formatters())
        raise KeyError(f"Unknown formatter {name!r}. Available: {available}")
    return _REGISTRY[name]
