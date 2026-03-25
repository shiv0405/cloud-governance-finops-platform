# Architecture Notes

## Current Scope

This starter intentionally keeps the deployed footprint small:

- One AWS provider configured from variables
- One S3 bucket for project artifacts or reporting exports
- One reporting helper path through Terraform outputs and Python

This makes the repository easy to review, plan, and extend without hiding behavior behind a large module tree.

## Resource Flow

```text
Terraform variables
  -> AWS provider
  -> S3 artifact bucket
  -> Terraform outputs
  -> reporting hook script
  -> JSON report for CI, docs, or inventory systems
```

## Deployment Sequence

1. Set values in a local tfvars file or pass `-var` flags.
2. Run `terraform init`.
3. Run `terraform validate` and `terraform plan`.
4. Apply when ready.
5. Generate a machine-readable report with `scripts/report_hook.py`.

## Reporting Hook Intent

The reporting hook is designed for lightweight post-deploy visibility:

- emit a JSON summary after `terraform apply`
- attach the report to CI artifacts
- feed a later dashboard or inventory sync job
- keep reporting logic outside Terraform state definitions

## Recommended Next Extensions

Low-risk additions that fit this starter:

- enable S3 bucket versioning for artifact retention
- add bucket encryption and public access blocking
- publish reports to a dedicated prefix in the bucket
- add CloudWatch dashboards or alarms for report-processing jobs
- add a GitHub Actions workflow that runs plan and saves the JSON report

## Example Operational Boundary

Keep Terraform responsible for infrastructure declarations.
Keep Python helpers responsible for formatting, exporting, and integrating reports.
This separation helps preserve reviewability and avoids embedding operational formatting logic in HCL.
