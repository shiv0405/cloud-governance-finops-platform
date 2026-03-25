# infra-reporting-starter

![Terraform](https://img.shields.io/badge/Terraform-1.7-blue)
![Template](https://img.shields.io/badge/Template-AWS-gold)
![License](https://img.shields.io/badge/License-APACHE-2.0-brightgreen)

Terraform-first AWS starter with deployment notes and reporting hooks.

## Overview

This AWS starter focuses on transparent infrastructure examples that are easy to review in a portfolio. It includes a small Terraform footprint, configurable inputs, and a placeholder helper script for reporting inventory.

## Quick Start

```bash
terraform init
terraform validate
terraform plan -var="project_name=infra-reporting-starter"
```

## Included Starter Assets

- `main.tf` provisions a tagged S3 bucket placeholder.
- `variables.tf` centralizes the environment inputs.
- `scripts/render_inventory.py` emits a simple JSON inventory summary.

## Automation Disclosure

**Note:** This repository uses automation and AI assistance for planning, initial scaffolding, routine maintenance, and selected code or documentation generation. I review and curate the outputs as part of my portfolio workflow.

## Additional Starter Assets

- `scripts/report_hook.py` reads Terraform outputs and produces a small infrastructure report payload for CI, ops notes, or inventory handoff.
- `docs/architecture.md` explains the current AWS layout, deployment flow, and low-risk extension points.
- `terraform.tfvars.example` provides a copy-ready local configuration example.

## Example Reporting Flow

```bash
terraform output -json > tf-output.json
python scripts/report_hook.py --terraform-output tf-output.json
```

Or let the script call Terraform directly:

```bash
python scripts/report_hook.py
```
