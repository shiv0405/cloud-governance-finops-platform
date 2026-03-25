# Runbook

## Local Reporting Flow

1. Generate sample inputs:
   `python -m infra_reporting_starter.cli generate-data --accounts 24 --months 12 --resources-per-account 120`
2. Build the reports:
   `python -m infra_reporting_starter.cli build-report`
3. Review:
   - `reports/account_scorecard.csv`
   - `reports/findings_summary.json`
   - `reports/executive_summary.html`

## Terraform Flow

1. Copy `terraform/terraform.tfvars.example` to `terraform/terraform.tfvars`
2. Run `terraform init`
3. Run `terraform validate`
4. Run `terraform plan`
5. Apply only after updating ownership, region, and scheduling settings for the real environment
