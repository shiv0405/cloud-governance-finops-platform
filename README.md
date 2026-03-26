# Cloud Governance and FinOps Platform

Production-oriented AWS governance and FinOps analytics project for cloud visibility, remediation planning, and reporting. It combines Terraform infrastructure, synthetic multi-account telemetry, account-level scorecards, remediation recommendations, and executive reporting into one cohesive operating model.

## Overview

- Moves beyond infrastructure provisioning into governance, cost posture, and operating accountability
- Produces actionable outputs for platform, security, and FinOps stakeholders
- Includes a multi-account dataset with cost, utilization, tagging, backup, encryption, and exposure signals
- Combines infrastructure, reporting, and remediation planning in one workflow

## Core Capabilities

- Terraform foundation for a reporting lake, Athena workgroup, Glue catalog, encryption, and scheduled processing
- Synthetic AWS inventory, cost usage, and security findings across multiple business-unit accounts
- Account scorecards with governance, optimization, maturity, and risk measures
- Portfolio KPI snapshot, executive brief, and remediation recommendation queue

## Project Layout

- `terraform/` contains the AWS reporting foundation
- `lambda/` contains the scheduled reporting Lambda handler
- `src/infra_reporting_starter/` contains the Python package and CLI
- `data/raw/` stores the generated source datasets
- `reports/` stores scorecards, KPI snapshots, recommendations, and executive outputs
- `docs/` contains architecture, runbook, and operating-model notes

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
cloud-governance-finops-platform run-all --accounts 24 --months 12 --resources-per-account 120
```

## Outputs

After `run-all`, the project writes:

- `data/raw/aws_inventory_snapshot.csv`
- `data/raw/aws_cost_usage.csv`
- `data/raw/security_findings.csv`
- `reports/account_scorecard.csv`
- `reports/findings_summary.json`
- `reports/portfolio_kpis.json`
- `reports/remediation_recommendations.csv`
- `reports/executive_brief.md`
- `reports/executive_summary.html`

## Business Questions It Answers

- Which accounts combine governance drift with meaningful spend and therefore need leadership attention?
- Where is the clearest savings opportunity across low-utilization and weak tagging discipline?
- Which issues belong with platform engineering versus security engineering versus FinOps?
- How mature is the portfolio overall, and what would it take to improve it quarter over quarter?

## Terraform Foundation

The Terraform stack provisions:

- encrypted S3 storage for reporting artifacts
- Athena and Glue components for ad hoc analysis
- a scheduled Lambda function for report orchestration
- CloudWatch logging and KMS-backed encryption defaults

## Production Path

- replace synthetic inputs with CUR, Config, Security Hub, and inventory extracts
- wire remediation recommendations into ticketing or platform backlog workflows
- add trend persistence to compare governance posture month over month
- expose selected KPI outputs through an API or semantic layer for executive dashboards
