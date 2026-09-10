from __future__ import annotations

import argparse

from proofline.runner import run_validation


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate an agent-built data pipeline")
    parser.add_argument("--fault", action="append", default=[], help="Inject a known defect")
    parser.add_argument("--rows", type=int, default=1_000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    report = run_validation(faults=args.fault, row_count=args.rows, seed=args.seed)
    print(report.model_dump_json(indent=2))


if __name__ == "__main__":
    main()

