from __future__ import annotations

import json

import pandas as pd

from .config import ProjectPaths


def run_reporting_pipeline(paths: ProjectPaths | None = None) -> dict[str, object]:
    resolved_paths = paths or ProjectPaths.from_root()
    resolved_paths.ensure_directories()

    inventory = pd.read_csv(resolved_paths.inventory_path)
    cost_usage = pd.read_csv(resolved_paths.cost_usage_path)
    findings = pd.read_csv(resolved_paths.findings_path)

    scorecard = build_account_scorecard(inventory, cost_usage, findings)
    summary = build_findings_summary(scorecard, findings)

    scorecard.to_csv(resolved_paths.scorecard_path, index=False)
    resolved_paths.findings_summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    resolved_paths.executive_html_path.write_text(build_executive_html(scorecard, summary), encoding="utf-8")

    return {
        "accounts": int(scorecard.shape[0]),
        "critical_accounts": int((scorecard["risk_band"] == "critical").sum()),
        "reports": {
            "scorecard_path": str(resolved_paths.scorecard_path),
            "findings_summary_path": str(resolved_paths.findings_summary_path),
            "executive_html_path": str(resolved_paths.executive_html_path),
        },
    }


def build_account_scorecard(
    inventory: pd.DataFrame,
    cost_usage: pd.DataFrame,
    findings: pd.DataFrame,
) -> pd.DataFrame:
    current_month = cost_usage["month"].max()
    previous_month = cost_usage.loc[cost_usage["month"] != current_month, "month"].max()

    current_spend = (
        cost_usage[cost_usage["month"] == current_month]
        .groupby(["account_id", "account_name"], as_index=False)["net_cost_usd"]
        .sum()
        .rename(columns={"net_cost_usd": "current_month_spend_usd"})
    )
    previous_spend = (
        cost_usage[cost_usage["month"] == previous_month]
        .groupby(["account_id", "account_name"], as_index=False)["net_cost_usd"]
        .sum()
        .rename(columns={"net_cost_usd": "previous_month_spend_usd"})
    )

    inventory_rollup = (
        inventory.groupby(["account_id", "account_name"], as_index=False)
        .agg(
            resources=("resource_id", "count"),
            public_resources=("public_exposure", "sum"),
            unencrypted_resources=("encrypted", lambda values: int((values == 0).sum())),
            resources_without_backup=("backup_enabled", lambda values: int((values == 0).sum())),
            untagged_resources=("tags_present", lambda values: int((values == 0).sum())),
            low_utilization_resources=("utilization_pct", lambda values: int((values < 25).sum())),
        )
    )

    findings_rollup = (
        findings.groupby(["account_id", "account_name"], as_index=False)
        .agg(
            open_findings=("status", lambda values: int((values == "open").sum())),
            critical_findings=("severity", lambda values: int((values == "critical").sum())),
            high_findings=("severity", lambda values: int((values == "high").sum())),
        )
    )

    scorecard = current_spend.merge(previous_spend, on=["account_id", "account_name"], how="left")
    scorecard = scorecard.merge(inventory_rollup, on=["account_id", "account_name"], how="left")
    scorecard = scorecard.merge(findings_rollup, on=["account_id", "account_name"], how="left").fillna(0)

    scorecard["spend_growth_pct"] = (
        (scorecard["current_month_spend_usd"] - scorecard["previous_month_spend_usd"])
        / scorecard["previous_month_spend_usd"].replace({0: 1})
        * 100
    ).round(2)

    scorecard["governance_score"] = (
        100
        - scorecard["public_resources"] * 6
        - scorecard["unencrypted_resources"] * 3
        - scorecard["resources_without_backup"] * 2
        - scorecard["untagged_resources"] * 1
        - scorecard["critical_findings"] * 5
        - scorecard["high_findings"] * 3
    ).clip(lower=0)

    scorecard["optimization_score"] = (
        100
        - scorecard["low_utilization_resources"] * 1.2
        - scorecard["spend_growth_pct"].clip(lower=0) * 0.35
    ).clip(lower=0)

    risk_score = (
        scorecard["critical_findings"] * 10
        + scorecard["high_findings"] * 5
        + scorecard["public_resources"] * 8
        + scorecard["unencrypted_resources"] * 3
        + scorecard["low_utilization_resources"] * 1.1
        + scorecard["spend_growth_pct"].clip(lower=0) * 0.7
    )
    scorecard["risk_score"] = risk_score.round(2)
    scorecard["risk_band"] = pd.cut(
        scorecard["risk_score"],
        bins=[-1, 25, 55, 90, float("inf")],
        labels=["stable", "watch", "elevated", "critical"],
    )

    return scorecard.sort_values(["risk_score", "current_month_spend_usd"], ascending=[False, False]).reset_index(drop=True)


def build_findings_summary(scorecard: pd.DataFrame, findings: pd.DataFrame) -> dict[str, object]:
    top_accounts = scorecard.head(10)[
        ["account_id", "account_name", "risk_score", "risk_band", "current_month_spend_usd", "spend_growth_pct"]
    ].to_dict(orient="records")
    finding_types = (
        findings.groupby(["finding_type", "severity"], as_index=False)
        .size()
        .sort_values("size", ascending=False)
        .rename(columns={"size": "count"})
    )
    return {
        "portfolio_summary": {
            "accounts": int(scorecard.shape[0]),
            "critical_accounts": int((scorecard["risk_band"] == "critical").sum()),
            "elevated_accounts": int((scorecard["risk_band"] == "elevated").sum()),
            "current_month_spend_usd": round(float(scorecard["current_month_spend_usd"].sum()), 2),
        },
        "top_accounts": top_accounts,
        "finding_breakdown": finding_types.head(12).to_dict(orient="records"),
    }


def build_executive_html(scorecard: pd.DataFrame, summary: dict[str, object]) -> str:
    overview = summary["portfolio_summary"]
    cards = "".join(
        [
            _card("Accounts", overview["accounts"]),
            _card("Critical", overview["critical_accounts"]),
            _card("Elevated", overview["elevated_accounts"]),
            _card("Current Spend", f"${overview['current_month_spend_usd']:,.0f}"),
        ]
    )
    account_rows = "".join(
        f"<tr><td>{row.account_name}</td><td>{row.risk_band}</td><td>{row.risk_score}</td><td>${row.current_month_spend_usd:,.0f}</td><td>{row.spend_growth_pct}%</td></tr>"
        for row in scorecard.head(12).itertuples()
    )
    breakdown_rows = "".join(
        f"<tr><td>{item['finding_type']}</td><td>{item['severity']}</td><td>{item['count']}</td></tr>"
        for item in summary["finding_breakdown"]
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AWS Governance Executive Summary</title>
  <style>
    body {{ margin: 0; padding: 28px; background: #f2f4f8; color: #16212b; font-family: "Segoe UI", sans-serif; }}
    .hero, .panel {{ background: #ffffff; border-radius: 24px; padding: 24px; margin-bottom: 18px; box-shadow: 0 16px 40px rgba(22, 33, 43, 0.08); }}
    .cards {{ display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); }}
    .card {{ background: #eef4fb; border-radius: 18px; padding: 16px; }}
    .card span {{ display: block; font-size: 12px; color: #5f7081; text-transform: uppercase; margin-bottom: 6px; }}
    .card strong {{ font-size: 30px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ text-align: left; padding: 10px; border-bottom: 1px solid #e8edf4; }}
    .kicker {{ text-transform: uppercase; letter-spacing: 0.12em; color: #9c5a18; font-weight: 700; font-size: 12px; }}
  </style>
</head>
<body>
  <section class="hero">
    <div class="kicker">AWS Governance and FinOps</div>
    <h1>Infra Reporting Executive Summary</h1>
    <p>Multi-account reporting view for cost posture, governance drift, and remediation priority.</p>
    <div class="cards">{cards}</div>
  </section>
  <section class="panel">
    <h2>Highest-Risk Accounts</h2>
    <table>
      <thead><tr><th>Account</th><th>Band</th><th>Risk Score</th><th>Current Spend</th><th>Spend Growth</th></tr></thead>
      <tbody>{account_rows}</tbody>
    </table>
  </section>
  <section class="panel">
    <h2>Finding Breakdown</h2>
    <table>
      <thead><tr><th>Finding Type</th><th>Severity</th><th>Count</th></tr></thead>
      <tbody>{breakdown_rows}</tbody>
    </table>
  </section>
</body>
</html>"""


def _card(label: str, value: object) -> str:
    return f"<div class='card'><span>{label}</span><strong>{value}</strong></div>"
