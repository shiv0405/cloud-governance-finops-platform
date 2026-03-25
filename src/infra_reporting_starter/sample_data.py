from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd


REGIONS = ["us-east-1", "eu-west-1", "ap-southeast-1", "sa-east-1"]
SERVICES = ["EC2", "S3", "RDS", "Lambda", "EKS", "CloudFront"]
OWNER_TEAMS = ["platform", "data", "security", "customer-apps", "internal-tools"]
CONTROL_IDS = {
    "public_access": "S3-001",
    "encryption_gap": "KMS-003",
    "idle_compute": "EC2-007",
    "missing_backup": "RDS-002",
    "root_mfa_disabled": "IAM-004",
    "logging_gap": "CLOUDTRAIL-001",
    "tagging_gap": "TAG-001",
}


@dataclass(frozen=True)
class SampleGenerationConfig:
    accounts: int = 24
    months: int = 12
    resources_per_account: int = 120
    seed: int = 42


def generate_sample_inputs(
    accounts: int = 24,
    months: int = 12,
    resources_per_account: int = 120,
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rng = random.Random(seed)
    account_ids = [f"{100000000000 + index}" for index in range(accounts)]
    account_names = [f"business-unit-{index + 1:02d}" for index in range(accounts)]

    inventory_rows: list[dict[str, object]] = []
    cost_rows: list[dict[str, object]] = []
    finding_rows: list[dict[str, object]] = []

    for account_index, account_id in enumerate(account_ids):
        account_name = account_names[account_index]
        base_region = REGIONS[account_index % len(REGIONS)]
        base_monthly_spend = 12000 + account_index * 1450

        for resource_index in range(resources_per_account):
            service = SERVICES[(account_index + resource_index) % len(SERVICES)]
            region = REGIONS[(account_index + resource_index * 2) % len(REGIONS)]
            public_exposure = 1 if service in {"S3", "CloudFront"} and rng.random() < 0.07 else 0
            encrypted = 0 if service in {"S3", "RDS"} and rng.random() < 0.11 else 1
            utilization_pct = round(14 + ((resource_index * 7 + account_index * 3) % 76) + rng.random() * 8, 2)
            backup_enabled = 0 if service in {"RDS", "EKS"} and rng.random() < 0.14 else 1
            tags_present = 0 if rng.random() < 0.09 else 1
            monthly_cost_estimate = round(18 + ((resource_index + 4) * (account_index + 1) % 280) + rng.random() * 20, 2)

            inventory_rows.append(
                {
                    "account_id": account_id,
                    "account_name": account_name,
                    "region": region,
                    "service": service,
                    "resource_type": f"aws_{service.lower()}_resource",
                    "resource_id": f"{service.lower()}-{account_index + 1:02d}-{resource_index + 1:04d}",
                    "owner_team": OWNER_TEAMS[(account_index + resource_index) % len(OWNER_TEAMS)],
                    "tags_present": tags_present,
                    "public_exposure": public_exposure,
                    "encrypted": encrypted,
                    "backup_enabled": backup_enabled,
                    "utilization_pct": utilization_pct,
                    "monthly_cost_estimate": monthly_cost_estimate,
                    "home_region": base_region,
                }
            )

            resource_id = f"{service.lower()}-{account_index + 1:02d}-{resource_index + 1:04d}"
            _append_finding(
                finding_rows,
                account_id=account_id,
                account_name=account_name,
                region=region,
                resource_id=resource_id,
                finding_type="public_access",
                severity="critical",
                should_add=bool(public_exposure),
                rng=rng,
            )
            _append_finding(
                finding_rows,
                account_id=account_id,
                account_name=account_name,
                region=region,
                resource_id=resource_id,
                finding_type="encryption_gap",
                severity="high",
                should_add=not bool(encrypted),
                rng=rng,
            )
            _append_finding(
                finding_rows,
                account_id=account_id,
                account_name=account_name,
                region=region,
                resource_id=resource_id,
                finding_type="idle_compute",
                severity="medium",
                should_add=utilization_pct < 22,
                rng=rng,
            )
            _append_finding(
                finding_rows,
                account_id=account_id,
                account_name=account_name,
                region=region,
                resource_id=resource_id,
                finding_type="missing_backup",
                severity="medium",
                should_add=not bool(backup_enabled),
                rng=rng,
            )
            _append_finding(
                finding_rows,
                account_id=account_id,
                account_name=account_name,
                region=region,
                resource_id=resource_id,
                finding_type="tagging_gap",
                severity="medium",
                should_add=not bool(tags_present),
                rng=rng,
            )

        if rng.random() < 0.38:
            _append_finding(
                finding_rows,
                account_id=account_id,
                account_name=account_name,
                region=base_region,
                resource_id=f"{account_id}-root",
                finding_type="root_mfa_disabled",
                severity="high",
                should_add=True,
                rng=rng,
            )
        if rng.random() < 0.28:
            _append_finding(
                finding_rows,
                account_id=account_id,
                account_name=account_name,
                region=base_region,
                resource_id=f"{account_id}-trail",
                finding_type="logging_gap",
                severity="high",
                should_add=True,
                rng=rng,
            )

        for months_back in range(months):
            month = pd.Timestamp(date.today().replace(day=1)) - pd.DateOffset(months=months_back)
            for service in SERVICES:
                service_multiplier = 0.28 + (SERVICES.index(service) * 0.09)
                seasonality = 0.92 + ((months_back + account_index) % 4) * 0.06
                cost_rows.append(
                    {
                        "account_id": account_id,
                        "account_name": account_name,
                        "month": month.strftime("%Y-%m"),
                        "service": service,
                        "net_cost_usd": round(base_monthly_spend * service_multiplier * seasonality + rng.random() * 950, 2),
                    }
                )

    return (
        pd.DataFrame(inventory_rows),
        pd.DataFrame(cost_rows),
        pd.DataFrame(finding_rows),
    )


def write_inputs(
    inventory: pd.DataFrame,
    cost_usage: pd.DataFrame,
    findings: pd.DataFrame,
    inventory_path: Path,
    cost_usage_path: Path,
    findings_path: Path,
) -> None:
    inventory_path.parent.mkdir(parents=True, exist_ok=True)
    inventory.to_csv(inventory_path, index=False)
    cost_usage.to_csv(cost_usage_path, index=False)
    findings.to_csv(findings_path, index=False)


def _append_finding(
    rows: list[dict[str, object]],
    *,
    account_id: str,
    account_name: str,
    region: str,
    resource_id: str,
    finding_type: str,
    severity: str,
    should_add: bool,
    rng: random.Random,
) -> None:
    if not should_add:
        return
    rows.append(
        {
            "account_id": account_id,
            "account_name": account_name,
            "region": region,
            "control_id": CONTROL_IDS[finding_type],
            "finding_type": finding_type,
            "severity": severity,
            "status": "open" if rng.random() < 0.78 else "accepted",
            "resource_id": resource_id,
        }
    )
