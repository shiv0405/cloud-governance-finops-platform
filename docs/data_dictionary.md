# Data Dictionary

## aws_inventory_snapshot.csv

- `account_id`: 12-digit AWS account identifier
- `account_name`: business-friendly account alias
- `region`: AWS region for the resource
- `service`: AWS service owning the resource
- `resource_type`: simplified Terraform-style resource type label
- `resource_id`: synthetic resource identifier
- `owner_team`: owning platform or product team
- `tags_present`: whether required governance tags are present
- `public_exposure`: whether the resource is externally exposed
- `encrypted`: whether encryption at rest is enabled
- `backup_enabled`: whether backups are configured
- `utilization_pct`: simplified utilization signal
- `monthly_cost_estimate`: monthly estimated cost contribution in USD

## aws_cost_usage.csv

- `account_id`: owning AWS account
- `account_name`: account alias
- `month`: billing month in `YYYY-MM`
- `service`: AWS service
- `net_cost_usd`: modeled monthly net spend

## security_findings.csv

- `account_id`: owning AWS account
- `control_id`: internal control or benchmark reference
- `finding_type`: type of governance or security issue
- `severity`: finding severity
- `status`: open or accepted
- `resource_id`: affected resource identifier
