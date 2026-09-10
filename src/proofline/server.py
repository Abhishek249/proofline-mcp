from __future__ import annotations

from typing import Literal

from mcp.server.fastmcp import FastMCP

from proofline.runner import run_validation

mcp = FastMCP("Proofline", json_response=True)


@mcp.tool()
def validate_candidate_pipeline(
    faults: list[
        Literal["duplicate_rows", "missing_partition", "timezone_shift", "wrong_zone_mapping"]
    ] | None = None,
    row_count: int = 1_000,
    seed: int = 42,
) -> dict:
    """Compare a candidate taxi pipeline with a trusted reference and return evidence."""
    return run_validation(faults=faults or [], row_count=row_count, seed=seed).model_dump(mode="json")


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

