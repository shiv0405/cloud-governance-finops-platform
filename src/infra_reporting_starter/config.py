from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    root: Path
    raw_dir: Path
    reports_dir: Path
    docs_dir: Path
    inventory_path: Path
    cost_usage_path: Path
    findings_path: Path
    scorecard_path: Path
    findings_summary_path: Path
    portfolio_kpis_path: Path
    recommendations_path: Path
    executive_brief_path: Path
    executive_html_path: Path

    @classmethod
    def from_root(cls, root: Path | None = None) -> "ProjectPaths":
        resolved_root = (root or Path(__file__).resolve().parents[2]).resolve()
        raw_dir = resolved_root / "data" / "raw"
        reports_dir = resolved_root / "reports"
        docs_dir = resolved_root / "docs"
        return cls(
            root=resolved_root,
            raw_dir=raw_dir,
            reports_dir=reports_dir,
            docs_dir=docs_dir,
            inventory_path=raw_dir / "aws_inventory_snapshot.csv",
            cost_usage_path=raw_dir / "aws_cost_usage.csv",
            findings_path=raw_dir / "security_findings.csv",
            scorecard_path=reports_dir / "account_scorecard.csv",
            findings_summary_path=reports_dir / "findings_summary.json",
            portfolio_kpis_path=reports_dir / "portfolio_kpis.json",
            recommendations_path=reports_dir / "remediation_recommendations.csv",
            executive_brief_path=reports_dir / "executive_brief.md",
            executive_html_path=reports_dir / "executive_summary.html",
        )

    def ensure_directories(self) -> None:
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.docs_dir.mkdir(parents=True, exist_ok=True)
