"""Render a self-contained, offline executive resilience assessment."""

from __future__ import annotations

import html
import json
from typing import Any


def _value(value: Any) -> str:
    if value is None:
        return "Not specified"
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True, ensure_ascii=False)
    return str(value)


def _cell(value: Any) -> str:
    return html.escape(_value(value), quote=True)


def _table(title: str, columns: tuple[str, ...], rows: list[tuple[Any, ...]]) -> str:
    if not rows:
        return f"<section><h2>{_cell(title)}</h2><p class=\"muted\">No findings.</p></section>"
    header = "".join(f"<th scope=\"col\">{_cell(column)}</th>" for column in columns)
    body = "".join(
        "<tr>" + "".join(f"<td>{_cell(value)}</td>" for value in row) + "</tr>"
        for row in rows
    )
    return (
        f"<section><h2>{_cell(title)}</h2><div class=\"table-wrap\">"
        f"<table><thead><tr>{header}</tr></thead><tbody>{body}</tbody></table>"
        "</div></section>"
    )


def render_resilience_html(report: dict[str, Any]) -> str:
    """Render a JSON resilience report as a safe, self-contained HTML briefing."""
    if not isinstance(report, dict) or report.get("report_type") != "institutional-resilience-and-recovery-plan":
        raise ValueError("report must be an institutional resilience assessment")

    executive = report.get("executive_assessment", {})
    baseline = executive.get("baseline", {})
    metrics = (
        ("Services", baseline.get("service_count")),
        ("Available", baseline.get("available")),
        ("Degraded", baseline.get("degraded")),
        ("Unavailable", baseline.get("unavailable")),
        ("Correlated domains", executive.get("correlated_failure_domain_count")),
        ("Capacity gaps", executive.get("capacity_gap_count")),
    )
    cards = "".join(
        f"<article class=\"metric\"><span>{_cell(label)}</span><strong>{_cell(value)}</strong></article>"
        for label, value in metrics
    )

    weakest = [
        (
            item.get("dependency", {}).get("type"),
            item.get("dependency", {}).get("id"),
            ", ".join(item.get("affected_services", [])),
            item.get("weighted_impact"),
            ", ".join(item.get("unavailable_services", [])) or "None",
        )
        for item in report.get("weakest_dependencies", [])
    ]
    correlated = [
        (
            item.get("failure_domain"),
            ", ".join(item.get("failed_assets", {}).get("nodes", [])),
            ", ".join(item.get("failed_assets", {}).get("links", [])),
            ", ".join(item.get("failed_assets", {}).get("sites", [])),
            ", ".join(item.get("unavailable_services", [])) or "None",
            item.get("weighted_impact"),
        )
        for item in report.get("correlated_failure_scenarios", [])
    ]
    diversity = [
        (
            item.get("service_id"),
            item.get("redundancy_group"),
            item.get("diversity_status"),
            ", ".join(item.get("shared_failure_domains", [])) or "None declared",
        )
        for item in report.get("physical_diversity_assessment", [])
    ]
    recovery = [
        (
            item.get("rank"),
            item.get("service_name"),
            item.get("criticality"),
            item.get("priority_weight"),
            item.get("baseline_status"),
            item.get("recovery_objectives", {}).get("rto_minutes"),
            item.get("recovery_objectives", {}).get("rpo_minutes"),
        )
        for item in report.get("recovery_priorities", [])
    ]
    capacity = [
        (
            item.get("service_name"),
            item.get("scenario", {}).get("type"),
            item.get("scenario", {}).get("id"),
            item.get("required_capacity_mbps"),
            item.get("declared_available_capacity_mbps"),
            item.get("capacity_gap_mbps"),
            item.get("status", "assessed"),
        )
        for item in report.get("capacity_assessment", [])
    ]
    recommendations = report.get("redundancy_recommendations", [])
    recommendation_html = "".join(
        "<article class=\"recommendation\">"
        f"<p class=\"eyebrow\">{_cell(item.get('priority', 'unranked'))} priority</p>"
        f"<h3>Protect {_cell(item.get('protect_dependency'))}</h3>"
        f"<p>{_cell(item.get('recommended_action'))}</p>"
        f"<p class=\"muted\">Modeled weighted impact: {_cell(item.get('modeled_weighted_impact'))}</p>"
        f"<p class=\"muted\">Assumptions: {_cell('; '.join(item.get('assumptions', [])))}</p>"
        "</article>"
        for item in recommendations
    ) or "<p class=\"muted\">No redundancy recommendations were generated.</p>"

    candidate = report.get("candidate_comparison", {})
    candidate_html = (
        _table(
            "Candidate comparison",
            ("Measure", "Baseline", "Candidate", "Change"),
            [
                (label, candidate.get("baseline", {}).get(key),
                 candidate.get("candidate", {}).get(key), candidate.get("change", {}).get(delta))
                for label, key, delta in (
                    ("Available services", "available", "available_services"),
                    ("Degraded services", "degraded", "degraded_services"),
                    ("Unavailable services", "unavailable", "unavailable_services"),
                    ("Weighted affected priority", "weighted_affected_priority", "weighted_affected_priority"),
                    ("Modeled capacity gaps", "modeled_capacity_gap_count", "modeled_capacity_gaps"),
                )
            ],
        )
        if candidate.get("candidate_supplied")
        else "<section><h2>Candidate comparison</h2><p class=\"muted\">No candidate dependency model was supplied.</p></section>"
    )

    limitations = "".join(f"<li>{_cell(item)}</li>" for item in report.get("limitations", []))
    headline = _cell(executive.get("headline", "Institutional resilience assessment"))
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>NETOPPS | Institutional Resilience Briefing</title>
<style>
:root {{ color-scheme: light; font-family: Inter, ui-sans-serif, system-ui, sans-serif; background: #f3f6fa; color: #172033; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; }}
header {{ background: #111d32; color: #fff; padding: 2.5rem max(1.25rem, calc((100vw - 1180px)/2)); }}
header p {{ color: #bdc9dc; margin: .5rem 0 0; }}
main {{ max-width: 1180px; margin: 2rem auto; padding: 0 1.25rem 3rem; }}
h1 {{ margin: 0; font-size: clamp(1.8rem, 4vw, 2.7rem); letter-spacing: -.04em; }}
h2 {{ font-size: 1.2rem; margin: 0 0 1rem; }}
h3 {{ font-size: 1rem; margin: .25rem 0 .5rem; }}
section {{ background: #fff; border: 1px solid #dce3ed; border-radius: 14px; padding: 1.25rem; margin: 1rem 0; }}
.metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: .8rem; margin: 1rem 0; }}
.metric {{ background: #fff; border: 1px solid #dce3ed; border-radius: 12px; padding: 1rem; }}
.metric span {{ display: block; color: #58657a; font-size: .8rem; }}
.metric strong {{ display: block; font-size: 1.7rem; margin-top: .3rem; }}
.table-wrap {{ overflow-x: auto; }}
table {{ width: 100%; border-collapse: collapse; font-size: .88rem; }}
th, td {{ text-align: left; padding: .7rem .6rem; border-bottom: 1px solid #e7ecf2; vertical-align: top; }}
th {{ color: #58657a; font-weight: 650; white-space: nowrap; }}
.recommendation {{ border-left: 3px solid #5376a8; padding: .75rem 1rem; margin: .8rem 0; background: #f7f9fc; border-radius: 0 10px 10px 0; overflow-wrap: anywhere; }}
.eyebrow {{ text-transform: uppercase; letter-spacing: .08em; font-size: .7rem; color: #526887; font-weight: 700; }}
.muted, footer {{ color: #657187; font-size: .86rem; }}
.notice {{ border: 1px solid #e7d8aa; background: #fffaf0; border-radius: 12px; padding: 1rem; }}
ul {{ padding-left: 1.2rem; }}
li {{ margin: .45rem 0; }}
footer {{ padding: 1rem 0; }}
@media print {{ :root {{ background: #fff; }} main {{ margin: 0 auto; }} section, .metric {{ break-inside: avoid; }} }}
</style>
</head>
<body>
<header><h1>Institutional Resilience Briefing</h1><p>NETOPPS · Simulation-only decision support · Model version {_cell(report.get("model_version"))}</p></header>
<main>
<section><h2>Executive assessment</h2><p>{headline}</p><p class="muted">Highest-risk dependency: {_cell(executive.get("highest_risk_dependency"))}</p></section>
<div class="metrics">{cards}</div>
{_table("Weakest infrastructure dependencies", ("Type", "Dependency", "Affected services", "Weighted impact", "Unavailable services"), weakest)}
{_table("Correlated failure scenarios", ("Shared failure domain", "Nodes", "Links", "Sites", "Unavailable services", "Weighted impact"), correlated)}
{_table("Physical diversity evidence review", ("Service", "Redundancy group", "Assessment", "Shared failure domains"), diversity)}
<section><h2>Redundancy recommendations</h2>{recommendation_html}</section>
{_table("Recovery priorities", ("Rank", "Service", "Criticality", "Priority weight", "Current modeled state", "RTO (min)", "RPO (min)"), recovery)}
{_table("Declared capacity assessment", ("Service", "Failure type", "Failure ID", "Required Mbps", "Available Mbps", "Gap Mbps", "Assessment"), capacity)}
{candidate_html}
<section class="notice"><h2>Interpretation and limitations</h2><p>This report is generated from operator-supplied models. It is not live monitoring, a network audit, an SLA certification, or proof of successful failover or physical independence.</p><ul>{limitations}</ul></section>
<footer>Generated locally by NETOPPS. No external assets, scripts, telemetry, or network calls are used by this report.</footer>
</main>
</body>
</html>
"""
