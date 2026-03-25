from __future__ import annotations

from pathlib import Path

from infra_reporting_starter.config import ProjectPaths
from infra_reporting_starter.reporting import run_reporting_pipeline
from infra_reporting_starter.sample_data import generate_sample_inputs, write_inputs


def test_reporting_pipeline_generates_outputs(tmp_path: Path) -> None:
    paths = ProjectPaths.from_root(tmp_path)
    paths.ensure_directories()
    inventory, cost_usage, findings = generate_sample_inputs(accounts=8, months=6, resources_per_account=30, seed=7)
    write_inputs(
        inventory=inventory,
        cost_usage=cost_usage,
        findings=findings,
        inventory_path=paths.inventory_path,
        cost_usage_path=paths.cost_usage_path,
        findings_path=paths.findings_path,
    )

    result = run_reporting_pipeline(paths)

    assert result["accounts"] == 8
    assert Path(result["reports"]["scorecard_path"]).exists()
    assert Path(result["reports"]["executive_html_path"]).exists()
