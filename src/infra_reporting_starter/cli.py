from __future__ import annotations

import argparse
from pathlib import Path

from .config import ProjectPaths
from .reporting import run_reporting_pipeline
from .sample_data import generate_sample_inputs, write_inputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cloud governance and FinOps platform CLI")
    parser.add_argument("--project-root", default=".", help="Project root containing data/, reports/, and terraform/")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser("generate-data", help="Generate synthetic AWS governance input datasets")
    generate_parser.add_argument("--accounts", type=int, default=24)
    generate_parser.add_argument("--months", type=int, default=12)
    generate_parser.add_argument("--resources-per-account", type=int, default=120)
    generate_parser.add_argument("--seed", type=int, default=42)

    subparsers.add_parser("build-report", help="Build account scorecards and executive summary from existing inputs")

    run_all_parser = subparsers.add_parser("run-all", help="Generate data and build reports")
    run_all_parser.add_argument("--accounts", type=int, default=24)
    run_all_parser.add_argument("--months", type=int, default=12)
    run_all_parser.add_argument("--resources-per-account", type=int, default=120)
    run_all_parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = ProjectPaths.from_root(Path(args.project_root).resolve())
    paths.ensure_directories()

    if args.command in {"generate-data", "run-all"}:
        inventory, cost_usage, findings = generate_sample_inputs(
            accounts=args.accounts,
            months=args.months,
            resources_per_account=args.resources_per_account,
            seed=args.seed,
        )
        write_inputs(
            inventory=inventory,
            cost_usage=cost_usage,
            findings=findings,
            inventory_path=paths.inventory_path,
            cost_usage_path=paths.cost_usage_path,
            findings_path=paths.findings_path,
        )
        print(f"Wrote input datasets to {paths.raw_dir}")

    if args.command in {"build-report", "run-all"}:
        result = run_reporting_pipeline(paths)
        print(result)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
