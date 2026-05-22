"""Formatter registry for drift-check output formats."""
from __future__ import annotations

from typing import Callable, Dict, List

from drift_check.drift_detector import DriftItem


def get_available_formatters() -> Dict[str, Callable[[List[DriftItem]], str]]:
    """Return a mapping of format-name -> render function.

    Importing is deferred so that optional heavy dependencies (e.g.
    ``openpyxl``, ``reportlab``) do not cause import errors when they
    are not installed.
    """
    from drift_check.formatters.html_reporter import render_html
    from drift_check.formatters.csv_reporter import render_csv
    from drift_check.formatters.markdown_reporter import render_markdown
    from drift_check.formatters.junit_reporter import render_junit
    from drift_check.formatters.slack_reporter import render_slack
    from drift_check.formatters.sarif_reporter import render_sarif
    from drift_check.formatters.yaml_reporter import render_yaml
    from drift_check.formatters.prometheus_reporter import render_prometheus
    from drift_check.formatters.graphite_reporter import render_graphite
    from drift_check.formatters.influxdb_reporter import render_influxdb
    from drift_check.formatters.datadog_reporter import render_datadog
    from drift_check.formatters.opsgenie_reporter import render_opsgenie
    from drift_check.formatters.splunk_reporter import render_splunk
    from drift_check.formatters.newrelic_reporter import render_newrelic
    from drift_check.formatters.syslog_reporter import render_syslog
    from drift_check.formatters.pagerduty_reporter import render_pagerduty
    from drift_check.formatters.webhook_reporter import render_webhook
    from drift_check.formatters.dotenv_reporter import render_dotenv
    from drift_check.formatters.teamcity_reporter import render_teamcity
    from drift_check.formatters.ndjson_reporter import render_ndjson

    return {
        "html": render_html,
        "csv": render_csv,
        "markdown": render_markdown,
        "junit": render_junit,
        "slack": render_slack,
        "sarif": render_sarif,
        "yaml": render_yaml,
        "prometheus": render_prometheus,
        "graphite": render_graphite,
        "influxdb": render_influxdb,
        "datadog": render_datadog,
        "opsgenie": render_opsgenie,
        "splunk": render_splunk,
        "newrelic": render_newrelic,
        "syslog": render_syslog,
        "pagerduty": render_pagerduty,
        "webhook": render_webhook,
        "dotenv": render_dotenv,
        "teamcity": render_teamcity,
        "ndjson": render_ndjson,
    }
