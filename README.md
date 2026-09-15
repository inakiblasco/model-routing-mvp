# model-routing-mvp

Minimal Python framework for evaluating task-based and policy-based routing
across LLM models/providers.

Core research question: can a simple routing policy match the quality of always
using the strongest model while reducing cost and/or latency?

This is a research prototype, not production software.

## Architecture

- `Task`: `task_id`, `prompt`, `expected_category`, optional structured evaluator.
- `ModelAdapter`: common `generate(prompt)` interface returning response, latency,
  token usage, and estimated cost.
- `Router`: common route interface returning the selected model and reason.
- Baselines: `always_fast`, `always_strong`, `rule_based_router`,
  `policy_router`.
- Evaluators: `exact`, `contains`, and `regex`.
- Outputs: `results.jsonl`, `results.csv`, and `summary.md`.

The default Phase 1 config uses deterministic synthetic models so experiments
run offline and are repeatable. A small OpenAI-compatible HTTP adapter is
included for configurable external endpoints, but no external service is called
unless you run an API-backed config.

## Setup

Requires Python 3.12.

```powershell
cd C:\Users\blascomontanoin\model-routing-mvp
uv sync --dev
```

## Run

```powershell
uv run python -m model_routing_mvp --config config.example.json
```

Outputs are written to `outputs/` by default.

For the preserved Phase 0 benchmark:

```powershell
uv run python -m model_routing_mvp --config config.phase0.example.json
```

For the Phase 1 OpenAI API config:

```powershell
$env:OPENAI_API_KEY = "..."
uv run python -m model_routing_mvp --config config.phase1.openai.example.json
```

## Test

```powershell
uv run pytest
```

If your network uses enterprise TLS interception and uv reports an unknown issuer, run:

```powershell
uv sync --dev --system-certs
```

## Quality Gates

Before presenting results, run both checks:

```powershell
uv run pytest
uv run python -m model_routing_mvp --config config.example.json
```

## Configuration

Runtime configuration lives in `config.example.json`, not in code. These
environment variables override the matching config values:

- `MODEL_ROUTING_BENCHMARK_PATH`
- `MODEL_ROUTING_OUTPUT_DIR`
- `MODEL_ROUTING_REDACT_RESPONSES`

For real providers, add a model with adapter `openai_compatible_http`:

```json
{
  "key": "strong",
  "adapter": "openai_compatible_http",
  "provider": "example-provider",
  "model_name": "example-model",
  "endpoint_env": "EXAMPLE_LLM_ENDPOINT",
  "api_key_env": "EXAMPLE_LLM_API_KEY",
  "input_cost_per_1k": 0.005,
  "output_cost_per_1k": 0.01
}
```

Credentials are read from environment variables and are never logged. Keep
`.env` files and generated outputs out of git.

## Security Notes

- Use only synthetic or public benchmark data.
- Do not put company, client, or secret information in benchmark prompts.
- Model responses can be redacted from output records with
  `MODEL_ROUTING_REDACT_RESPONSES=true`.
- Logs are structured JSON and do not include prompts, responses, endpoints, or
  credentials.
- No telemetry is included.
- External endpoints are configurable and never called by the default synthetic
  setup.
