# infra-reporting-starter

![Terraform](https://img.shields.io/badge/Terraform-1.7-blue)
![Template](https://img.shields.io/badge/Template-AWS-gold)
![License](https://img.shields.io/badge/License-APACHE-2.0-brightgreen)

Terraform-first AWS starter with deployment notes and reporting hooks.

## Overview

This AWS starter focuses on transparent infrastructure examples that are easy to review in a portfolio. It includes a small Terraform footprint, configurable inputs, and a lightweight reporting path for post-deploy inventory.

Current infrastructure defaults include:

- an S3 bucket for project artifacts or report exports
- bucket versioning for safer retention
- server-side encryption with SSE-S3
- public access blocking to avoid accidental exposure

## Quick Start

```bash
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform validate
terraform plan
```

## Included Starter Assets

- `main.tf` provisions a tagged S3 bucket with safer default controls.
- `variables.tf` centralizes the environment inputs.
- `outputs.tf` exposes bucket metadata for reporting and automation.
- `scripts/render_inventory.py` emits a simple JSON inventory summary.

## Reporting Workflow

Generate Terraform outputs and build a machine-readable report:

```bash
terraform output -json > tf-output.json
python scripts/report_hook.py --terraform-output tf-output.json --out reports/infra-report.json
cat reports/infra-report.json
```

You can also run the helper directly in an initialized Terraform working directory:

```bash
python scripts/report_hook.py
```

## Deployment Notes

1. Copy `terraform.tfvars.example` to `terraform.tfvars` and adjust values.
2. Run `terraform init`, `terraform validate`, and `terraform plan`.
3. Apply when ready with `terraform apply`.
4. Export outputs and archive the generated report as a CI artifact or operations note.

## Automation Disclosure

**Note:** This repository uses automation and AI assistance for planning, initial scaffolding, routine maintenance, and selected code or documentation generation. I review and curate the outputs as part of my portfolio workflow.

## Additional Starter Assets

- `scripts/report_hook.py` reads Terraform outputs and produces a small infrastructure report payload for CI, ops notes, or inventory handoff.
- `docs/architecture.md` explains the current AWS layout, deployment flow, and low-risk extension points.
- `terraform.tfvars.example` provides a copy-ready local configuration example.
