from __future__ import annotations

import json
from textwrap import dedent

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
    portfolio_kpis = build_portfolio_kpis(scorecard)
    recommendations = build_recommendations(scorecard)
    executive_brief = build_executive_brief(scorecard, summary, portfolio_kpis, recommendations)

    scorecard.to_csv(resolved_paths.scorecard_path, index=False)
    recommendations.to_csv(resolved_paths.recommendations_path, index=False)
    resolved_paths.findings_summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    resolved_paths.portfolio_kpis_path.write_text(json.dumps(portfolio_kpis, indent=2), encoding="utf-8")
    resolved_paths.executive_brief_path.write_text(executive_brief, encoding="utf-8")
    resolved_paths.executive_html_path.write_text(
        build_executive_html(scorecard, summary, portfolio_kpis, recommendations),
        encoding="utf-8",
    )

    return {
        "accounts": int(scorecard.shape[0]),
        "critical_accounts": int((scorecard["risk_band"] == "critical").sum()),
        "reports": {
            "scorecard_path": str(resolved_paths.scorecard_path),
            "findings_summary_path": str(resolved_paths.findings_summary_path),
            "portfolio_kpis_path": str(resolved_paths.portfolio_kpis_path),
            "recommendations_path": str(resolved_paths.recommendations_path),
            "executive_brief_path": str(resolved_paths.executive_brief_path),
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
            annualized_infra_run_rate_usd=("monthly_cost_estimate", lambda values: round(float(values.sum()) * 12, 2)),
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

    scorecard["estimated_monthly_savings_usd"] = (
        scorecard["current_month_spend_usd"] * 0.06
        + scorecard["low_utilization_resources"] * 18
        + scorecard["untagged_resources"] * 3
    ).round(2)

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
    scorecard["maturity_band"] = pd.cut(
        scorecard["governance_score"] * 0.55 + scorecard["optimization_score"] * 0.45,
        bins=[-1, 60, 74, 87, float("inf")],
        labels=["reactive", "developing", "managed", "leading"],
    )

    return scorecard.sort_values(["risk_score", "current_month_spend_usd"], ascending=[False, False]).reset_index(drop=True)


def build_findings_summary(scorecard: pd.DataFrame, findings: pd.DataFrame) -> dict[str, object]:
    top_accounts = scorecard.head(10)[
        [
            "account_id",
            "account_name",
            "risk_score",
            "risk_band",
            "current_month_spend_usd",
            "spend_growth_pct",
            "estimated_monthly_savings_usd",
        ]
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
            "estimated_monthly_savings_usd": round(float(scorecard["estimated_monthly_savings_usd"].sum()), 2),
        },
        "top_accounts": top_accounts,
        "finding_breakdown": finding_types.head(12).to_dict(orient="records"),
    }


def build_portfolio_kpis(scorecard: pd.DataFrame) -> dict[str, object]:
    return {
        "accounts": int(scorecard.shape[0]),
        "average_governance_score": round(float(scorecard["governance_score"].mean()), 1),
        "average_optimization_score": round(float(scorecard["optimization_score"].mean()), 1),
        "critical_account_share_pct": round(float((scorecard["risk_band"] == "critical").mean() * 100), 1),
        "watch_or_higher_share_pct": round(float(scorecard["risk_band"].isin(["watch", "elevated", "critical"]).mean() * 100), 1),
        "estimated_monthly_savings_usd": round(float(scorecard["estimated_monthly_savings_usd"].sum()), 2),
        "annualized_infra_run_rate_usd": round(float(scorecard["annualized_infra_run_rate_usd"].sum()), 2),
        "leading_maturity_accounts": int((scorecard["maturity_band"] == "leading").sum()),
    }


def build_recommendations(scorecard: pd.DataFrame) -> pd.DataFrame:
    recommendations = scorecard.copy()
    recommendations["owner_team"] = "Cloud Platform"
    recommendations["recommended_action"] = "Maintain current governance cadence."
    recommendations.loc[recommendations["public_resources"] > 0, "recommended_action"] = "Prioritize public exposure remediation and edge configuration review."
    recommendations.loc[recommendations["low_utilization_resources"] >= 18, "recommended_action"] = "Launch rightsizing and scheduling review for idle compute and oversized services."
    recommendations.loc[recommendations["untagged_resources"] >= 12, "recommended_action"] = "Enforce tagging policy and automate ownership remediation across shared services."
    recommendations.loc[recommendations["critical_findings"] >= 6, "recommended_action"] = "Run executive security review and assign remediation owners within the current sprint."
    recommendations.loc[recommendations["resources_without_backup"] >= 10, "recommended_action"] = "Expand backup coverage and test restoration paths for critical data services."
    recommendations.loc[recommendations["estimated_monthly_savings_usd"] >= 5000, "owner_team"] = "FinOps"
    recommendations.loc[recommendations["critical_findings"] >= 6, "owner_team"] = "Security Engineering"
    return recommendations[
        [
            "account_id",
            "account_name",
            "risk_band",
            "maturity_band",
            "risk_score",
            "current_month_spend_usd",
            "estimated_monthly_savings_usd",
            "owner_team",
            "recommended_action",
        ]
    ].head(15)


def build_executive_brief(
    scorecard: pd.DataFrame,
    summary: dict[str, object],
    portfolio_kpis: dict[str, object],
    recommendations: pd.DataFrame,
) -> str:
    highest = scorecard.iloc[0]
    best = scorecard.sort_values(["governance_score", "optimization_score"], ascending=False).iloc[0]
    top_recommendation = recommendations.iloc[0]
    return dedent(
        f"""\
        # Executive Brief

        Cloud Governance and FinOps Intelligence covers {portfolio_kpis["accounts"]} AWS accounts with an annualized infrastructure run rate of ${portfolio_kpis["annualized_infra_run_rate_usd"]:,.0f}.

        ## Key Signals

        - Average governance score: {portfolio_kpis["average_governance_score"]}
        - Average optimization score: {portfolio_kpis["average_optimization_score"]}
        - Estimated monthly savings opportunity: ${portfolio_kpis["estimated_monthly_savings_usd"]:,.0f}
        - Critical account share: {portfolio_kpis["critical_account_share_pct"]}%

        ## Highest-Risk Account

        - {highest["account_name"]} currently carries a risk score of {highest["risk_score"]} with risk band `{highest["risk_band"]}`.

        ## Strongest Operating Posture

        - {best["account_name"]} leads the portfolio on governance and optimization posture.

        ## Priority Recommendation

        - {top_recommendation["account_name"]}: {top_recommendation["recommended_action"]}
        """
    )


def build_executive_html(
    scorecard: pd.DataFrame,
    summary: dict[str, object],
    portfolio_kpis: dict[str, object],
    recommendations: pd.DataFrame,
) -> str:
    overview = summary["portfolio_summary"]
    cards = "".join(
        [
            _card("Accounts", overview["accounts"]),
            _card("Critical", overview["critical_accounts"]),
            _card("Estimated Monthly Savings", f"${overview['estimated_monthly_savings_usd']:,.0f}"),
            _card("Annualized Run Rate", f"${portfolio_kpis['annualized_infra_run_rate_usd']:,.0f}"),
        ]
    )
    account_rows = "".join(
        f"<tr><td>{row.account_name}</td><td>{row.risk_band}</td><td>{row.maturity_band}</td><td>{row.risk_score}</td><td>${row.current_month_spend_usd:,.0f}</td><td>${row.estimated_monthly_savings_usd:,.0f}</td></tr>"
        for row in scorecard.head(12).itertuples()
    )
    recommendation_rows = "".join(
        f"<tr><td>{row.account_name}</td><td>{row.owner_team}</td><td>{row.recommended_action}</td></tr>"
        for row in recommendations.itertuples()
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Cloud Governance and FinOps Executive Summary</title>
  <style>
    body {{ margin: 0; padding: 28px; background: #f2f4f8; color: #16212b; font-family: "Segoe UI", sans-serif; }}
    .hero, .panel {{ background: #ffffff; border-radius: 24px; padding: 24px; margin-bottom: 18px; box-shadow: 0 16px 40px rgba(22, 33, 43, 0.08); }}
    .cards {{ display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); }}
    .card {{ background: #eef4fb; border-radius: 18px; padding: 16px; }}
    .card span {{ display: block; font-size: 12px; color: #5f7081; text-transform: uppercase; margin-bottom: 6px; }}
    .card strong {{ font-size: 30px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ text-align: left; padding: 10px; border-bottom: 1px solid #e8edf4; vertical-align: top; }}
    .kicker {{ text-transform: uppercase; letter-spacing: 0.12em; color: #9c5a18; font-weight: 700; font-size: 12px; }}
  </style>
</head>
<body>
  <section class="hero">
    <div class="kicker">Cloud Governance and FinOps</div>
    <h1>Executive Cloud Controls Summary</h1>
    <p>Multi-account view for governance posture, spend efficiency, and remediation priority across the AWS estate.</p>
    <div class="cards">{cards}</div>
  </section>
  <section class="panel">
    <h2>Highest-Risk Accounts</h2>
    <table>
      <thead><tr><th>Account</th><th>Risk Band</th><th>Maturity</th><th>Risk Score</th><th>Current Spend</th><th>Monthly Savings</th></tr></thead>
      <tbody>{account_rows}</tbody>
    </table>
  </section>
  <section class="panel">
    <h2>Priority Recommendations</h2>
    <table>
      <thead><tr><th>Account</th><th>Owner</th><th>Recommended Action</th></tr></thead>
      <tbody>{recommendation_rows}</tbody>
    </table>
  </section>
</body>
</html>"""


def _card(label: str, value: object) -> str:
    return f"<div class='card'><span>{label}</span><strong>{value}</strong></div>"
