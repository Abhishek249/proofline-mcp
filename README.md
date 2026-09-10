<p align="center">
  <img src="assets/proofline-logo.png" alt="Proofline logo" width="340">
</p>

<h1 align="center">Proofline MCP</h1>

[![CI](https://github.com/Abhishek249/proofline-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/Abhishek249/proofline-mcp/actions/workflows/ci.yml)

**A validation control plane for data pipelines written by AI agents.**

Coding agents can now generate an ingestion or transformation pipeline in minutes. The harder
question is whether the generated pipeline silently changed the data. Proofline runs a candidate
implementation against a trusted reference, executes deterministic invariants, and returns a
machine-readable evidence report through the Model Context Protocol (MCP).

This repository is a working vertical slice built around NYC taxi-shaped trip data. It includes a
deterministic local fixture, four realistic defect classes, five validation checks, and an MCP tool
an agent can invoke before accepting its own pipeline change.

## Proof that it works

The proof harness starts a real Proofline MCP server as a subprocess, performs the MCP handshake,
discovers the tool, invokes it for five controlled scenarios, and asserts the expected outcome and
diagnostic evidence. This tests the public protocol boundary—not an internal function shortcut.

```bash
python scripts/prove_it.py
```

The committed [proof report](docs/proof-report.json) records the reproducible result. CI regenerates
the same proof on every push. At seed 42 with 500 source records:

| Scenario | Expected decision | Required diagnostic | Result |
|---|---:|---|---:|
| Clean candidate | Pass | No failed checks | Pass |
| Duplicate rows | Fail | `key_uniqueness` | Detected |
| Missing partition | Fail | `key_set` | Detected |
| Timezone shift | Fail | `pickup_hour_distribution` | Detected |
| Wrong zone mapping | Fail | `fare_by_pickup_zone` | Detected |


### Reproduce the statistics

```bash
python scripts/benchmark_mcp.py --output benchmark-report.json
```

The benchmark performs 40 calls through a real MCP client/server session: four deterministic seeds,
two dataset sizes, one clean scenario, and four controlled defect classes. It reports detection
recall, false-positive rate, required-diagnostic accuracy, and p50/p95 MCP call latency.

GitHub Actions runs the benchmark on every push and on manual dispatch, writes the metrics into the
workflow summary, and uploads the complete JSON evidence as the `proofline-benchmark` artifact.
Statistics are scoped to this published controlled test matrix; they are not claims about arbitrary
production pipelines.

## Why this matters

Traditional data-quality tests ask whether one dataset satisfies fixed rules. Proofline asks a
different question: **is the agent's new implementation behaviorally equivalent to the trusted
pipeline, and what evidence supports that conclusion?**

| Injected defect | Evidence that exposes it |
|---|---|
| Duplicate records | row-count drift and duplicate keys |
| Missing daily partition | missing keys and aggregate drift |
| Timezone conversion error | pickup-hour distribution drift |
| Incorrect zone mapping | per-zone fare aggregate drift |

## Quick start

Requires Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

Run a clean candidate:

```bash
proofline --rows 1000
```

Inject a defect and inspect the evidence:

```bash
proofline --fault missing_partition --fault duplicate_rows
```

Run the MCP server over stdio:

```bash
proofline-mcp
```

The server exposes `validate_candidate_pipeline`, with `faults`, `row_count`, and `seed` as inputs.
For example, an MCP client can request validation with `faults=["timezone_shift"]` and receive the
overall decision, every check, expected and actual values, and focused failure evidence.


## Validate a real geospatial run

Proofline also exposes `validate_geospatial_run`. It accepts a typed evidence envelope collected
from your existing orchestrator, worker, database, and spatial comparison scripts. Proofline does
not need—and should not receive—database credentials or proprietary source code.

Example MCP arguments:

```json
{
  "evidence": {
    "parent_id": "fixture-1290",
    "run_id": "orchestrator-run-123",
    "orchestration_status": "SUCCESS",
    "worker_status": "Completed",
    "tile_count": 120,
    "polygon_generated": false,
    "postgres_written": false,
    "result_row_count": 0,
    "aggregated_shape_present": false,
    "expected_session_count": 12,
    "actual_session_count": 12,
    "reference_area": 100.0,
    "candidate_area": 0.0,
    "jaccard_index": 0.0
  }
}
```

This run fails even though orchestration reports `SUCCESS`, because tiles existed but no polygon or
database result was produced. The response identifies the violated invariants and includes the
observed evidence. Optional reference fields add session-count, relative-area, and Jaccard checks.

A practical agent workflow is:

1. Trigger or inspect a pipeline run using the environment's existing tools.
2. Collect the non-secret evidence fields above.
3. Call `validate_geospatial_run`.
4. Accept the deployment only when Proofline returns `status: "pass"`.

## Architecture

```mermaid
flowchart TD
    A["Agent changes pipeline"] --> B["Reference and candidate runs"]
    B --> C["Deterministic validators"]
    C --> D["Evidence report"]
    D --> E["MCP response to agent"]
    E --> F{"Accept change?"}
```

The MVP deliberately keeps orchestration separate from validation logic:

- `fixtures.py` creates reproducible taxi-shaped source records.
- `pipelines.py` contains the reference, candidate, and controlled defect injection.
- `validators.py` produces evidence-bearing check results.
- `runner.py` creates stable run identities and the final report.
- `server.py` exposes the capability through MCP.

## Research direction

Proofline is designed to grow into a benchmark for **agent-generated data pipeline reliability**.
A publishable evaluation would give coding agents transformation tasks, inject or observe defect
classes, and measure detection recall, false-positive rate, time-to-diagnosis, and evidence quality
across validation strategies.

The next milestone replaces the synthetic fixture with public NYC Taxi & Limousine Commission
Parquet files, adds DuckDB-based candidate implementations, and stores signed provenance for every
artifact. The synthetic mode remains important: it makes CI deterministic and provides known
ground truth for each defect.

## Roadmap

- [x] Reproducible reference and candidate pipelines
- [x] Controlled fault injection and evidence-rich checks
- [x] MCP server, CLI, tests, Docker image, and CI
- [x] Reusable geospatial evidence contract and MCP validator
- [ ] Pluggable PostgreSQL and orchestrator adapters
- [ ] NYC TLC Parquet adapter and schema contracts
- [ ] Agent task corpus and benchmark harness
- [ ] OpenTelemetry traces and signed evidence bundles
- [ ] Kubernetes deployment and policy-gated pull-request integration
- [ ] Empirical study and research paper

## Project status

Proofline is an early research prototype. It should not yet be used as a production quality gate.
Contributions and benchmark defect cases are welcome.
