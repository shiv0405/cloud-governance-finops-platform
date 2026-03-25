# Architecture

## Overview

This project represents a practical AWS governance and FinOps reporting foundation:

- S3 stores raw and curated reporting outputs
- KMS encrypts storage and logs
- Glue and Athena support ad hoc analytics over reporting datasets
- EventBridge triggers a reporting Lambda on a defined schedule
- Python tooling generates representative inventory and cost telemetry for demos and portfolio reviews

## Why This Is Senior-Friendly

- It connects infrastructure, security posture, cost visibility, and reporting rather than stopping at raw Terraform
- The stack is designed around operational workflows, not only resource creation
- The reporting pipeline creates artifacts that can feed dashboards, exec briefings, or remediation queues
