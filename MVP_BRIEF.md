# Model Routing MVP Brief

This brief describes Phase 0. Phase 1 planning and implementation notes live in
`PHASE_1_PROPOSAL.md`.

## What This Is

This MVP is a small evaluation framework for testing whether different LLM tasks can be routed to different models while preserving answer quality and reducing cost or latency.

In plain terms: instead of sending every request to the strongest and most expensive model, the system tests whether easy tasks can go to faster cheaper models, coding tasks can go to a coding-focused model, and harder reasoning tasks can still go to the strongest model.

## Why It Matters

LLM systems often default to one powerful model for everything. That is simple, but it can waste money and time. This MVP creates a repeatable way to compare that default against routing strategies.

The core question is:

> Can simple task routing match the quality of always using the strongest model while lowering cost and latency?

## What It Does

The framework runs the same benchmark through three strategies:

- `always_fast`: sends every task to the fast model.
- `always_strong`: sends every task to the strongest model.
- `rule_based_router`: sends tasks based on category.

The default routing policy is:

- `simple` -> fast model
- `coding` -> coding model
- `reasoning` -> strongest model

For each task, it records:

- selected model
- model response
- latency
- token usage
- estimated cost
- evaluation result
- routing decision and reason

It writes:

- `outputs/results.jsonl`
- `outputs/results.csv`
- `outputs/summary.md`

## Current Result

On the included synthetic benchmark:

| Strategy | Success Rate | Avg Latency | Avg Cost |
| --- | ---: | ---: | ---: |
| `always_fast` | 33.33% | 0.200s | 0.000003 |
| `always_strong` | 100.00% | 1.800s | 0.000114 |
| `rule_based_router` | 100.00% | 0.933s | 0.000054 |

This shows the intended MVP behavior: the simple router matches the strongest model's quality on the test set while reducing average latency and estimated cost.

## What Is Real vs Simulated

Real:

- routing interfaces
- model adapter interface
- experiment runner
- result files
- evaluation loop
- summary generation
- tests
- configuration and environment variable handling
- redaction option
- OpenAI-compatible HTTP adapter scaffold

Simulated:

- default model responses
- default latency
- default token costs
- benchmark data

The default setup is intentionally offline and deterministic so results are repeatable and safe to share.

## Safety Posture

- Uses only synthetic/public benchmark data.
- Does not include company or client information.
- Does not log prompts, responses, credentials, endpoints, or API keys.
- Supports response redaction.
- Uses environment variables for credentials.
- Does not call external services by default.
- Does not include telemetry.

## How To Run

```powershell
uv sync --dev
uv run pytest
uv run python -m model_routing_mvp --config config.example.json
```

## Status

This is ready to present as a research MVP.

It is not production software, and it does not yet prove that the same savings will hold across real providers or private workloads. What it does prove is that the evaluation harness, routing abstraction, output format, and safety constraints are in place for the next real-model experiment.
