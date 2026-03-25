from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_terraform_output(path: str | None) -> dict[str, Any]:
    if path:
        return json.loads(Path(path).read_text(encoding="utf-8"))

    result = subprocess.run(
        ["terraform", "output", "-json"],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def normalize_outputs(raw: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for name, meta in raw.items():
        if isinstance(meta, dict) and "value" in meta:
            normalized[name] = meta["value"]
        else:
            normalized[name] = meta
    return normalized


def build_report(outputs: dict[str, Any]) -> dict[str, Any]:
    bucket_name = outputs.get("bucket_name")
    resources: list[dict[str, Any]] = []

    if bucket_name:
        resources.append(
            {
                "type": "aws_s3_bucket",
                "name": bucket_name,
                "role": "artifact-storage",
            }
        )

    return {
        "project": "infra-reporting-starter",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "terraform-output",
        "resource_count": len(resources),
        "resources": resources,
        "outputs": outputs,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render a lightweight infrastructure report from Terraform outputs."
    )
    parser.add_argument(
        "--terraform-output",
        help="Optional path to a saved `terraform output -json` file.",
    )
    args = parser.parse_args()

    try:
        raw = load_terraform_output(args.terraform_output)
        outputs = normalize_outputs(raw)
        report = build_report(outputs)
    except FileNotFoundError as exc:
        print(f"error: file not found: {exc}", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as exc:
        print("error: failed to run `terraform output -json`", file=sys.stderr)
        if exc.stderr:
            print(exc.stderr.strip(), file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON input: {exc}", file=sys.stderr)
        return 3

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
