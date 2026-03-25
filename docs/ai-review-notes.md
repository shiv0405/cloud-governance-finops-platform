# AI Review Notes

Propose three safe, portfolio-strengthening maintenance updates: add secure S3 defaults in Terraform, complete and harden the reporting hook script, and add deployment usage notes plus a checked-in tfvars example referenced by the README.

- Adds low-risk AWS starter protections by enabling S3 versioning, server-side encryption, and public access blocking for the artifact bucket.
- Completes `scripts/report_hook.py` so the reporting path shown in docs is actually usable in CI or local workflows.
- Adds `terraform.tfvars.example` and clearer deployment/reporting notes so the repository's documented quick-start matches the files present in the repo.
- Bucket naming remains derived from `project_name` and `environment`; if stricter global uniqueness is needed later, a random suffix can be added in a follow-up without breaking this small starter.
