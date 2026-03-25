# infra-reporting-starter

Production-friendly AWS governance and FinOps reporting accelerator. This project combines Terraform infrastructure for a reporting foundation with Python tooling that generates multi-account sample telemetry, computes governance scorecards, and exports executive-ready reporting artifacts.

## Highlights

- Terraform foundation for an S3 reporting lake, Athena workgroup, Glue catalog, KMS encryption, and scheduled Lambda processing
- Synthetic multi-account AWS inventory, cost, and security datasets for realistic portfolio demos
- Reporting pipeline that produces account scorecards, prioritized findings, and an executive HTML summary
- Strong fit for senior cloud, platform, FinOps, and governance-focused roles

## Project Layout

- `terraform/` contains the AWS reporting foundation
- `lambda/` contains the scheduled reporting Lambda handler
- `src/infra_reporting_starter/` contains the Python package and CLI
- `data/raw/` stores the generated sample datasets
- `reports/` stores generated scorecards and summaries

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m infra_reporting_starter.cli run-all --accounts 24 --months 12 --resources-per-account 120
```

## Outputs

After `run-all`, the project writes:

- `data/raw/aws_inventory_snapshot.csv`
- `data/raw/aws_cost_usage.csv`
- `data/raw/security_findings.csv`
- `reports/account_scorecard.csv`
- `reports/findings_summary.json`
- `reports/executive_summary.html`

## Terraform Foundation

The Terraform stack provisions:

- encrypted S3 storage for reporting artifacts
- Athena and Glue components for ad hoc analysis
- a scheduled Lambda function for report orchestration
- CloudWatch logging and KMS-backed encryption defaults

## Automation Disclosure

**Note:** This repository uses automation and AI assistance for planning, initial scaffolding, routine maintenance, and selected code or documentation generation. I review and curate the outputs as part of my portfolio workflow.
