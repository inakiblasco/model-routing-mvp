# Phase 1 Proposal: Real Model Routing Evaluation

## Executive Summary

Phase 0 proved the harness: tasks can be loaded, routed, evaluated, and reported
against synthetic models.

Phase 1 turns that harness into a credible model-routing evaluation project:

- run a richer benchmark with task labels
- compare cheap, standard, strong, rule-based, and policy-based routing
- add real API-backed model configuration
- keep access decisions deterministic and explainable
- prepare a clean comparison slot for Sakana AI Fugu

The goal is not to build an enterprise permissions platform yet. The goal is to
measure when a task justifies a stronger model, and when orchestration like Fugu
creates value beyond deterministic routing.

## Phase 0

Phase 0 files:

- `MVP_BRIEF.md`
- `benchmarks/synthetic_tasks.jsonl`
- `config.phase0.example.json`

Phase 0 answered:

> Can a simple router match the strongest synthetic model while reducing cost
> and latency?

It was intentionally small and deterministic.

## Phase 1

Phase 1 answers:

> Can a deterministic policy router make better model choices when task type,
> risk, and sensitivity are included?

New Phase 1 files:

- `benchmarks/phase1_tasks.jsonl`
- `config.example.json`
- `config.phase1.openai.example.json`

New task labels:

- `task_type`
- `risk`
- `sensitivity`

New routing strategy:

- `policy_router`

## Routing Strategies

The framework now compares:

| Strategy | Purpose |
| --- | --- |
| `always_fast` | Cheapest baseline |
| `always_strong` | Quality ceiling and cost ceiling |
| `rule_based_router` | Task-category baseline |
| `policy_router` | Deterministic task/risk/sensitivity policy |

The policy router is deliberately simple:

- high-risk or confidential tasks go to the strong model
- reasoning, architecture, legal, and security tasks go to the strong model
- coding, debugging, research, summarization, and extraction tasks go to the standard model
- low-risk simple work goes to the fast model

This is not the final policy. It is the baseline that smarter strategies must
beat.

## Recommended Model Plan

### Phase 1A: OpenAI Only

Use this first because it is the easiest access path.

| Tier | Candidate | Purpose |
| --- | --- | --- |
| Fast | `gpt-5-nano` | Cheap classification, extraction, simple admin tasks |
| Standard | `gpt-5-mini` | Coding, summarization, routine reasoning |
| Strong | `gpt-5` | High-risk, confidential, architecture, legal/security reasoning |

OpenAI documentation lists `gpt-5`, `gpt-5-mini`, and `gpt-5-nano` as API
models with different cost/performance points. Verify actual account access
with the Models API before running a paid benchmark.

### Phase 1B: Add One Non-OpenAI Provider

Recommended provider: Mistral.

Why:

- non-Chinese provider
- API accessible
- has small, efficient models
- has code-specialized options
- has open-weight lineage useful for later local evaluation

Candidate families:

- Ministral 3B/8B/14B for lightweight tiers
- Mistral Small / Medium / Large for general capability tiers
- Codestral for code-specific comparison

Do not add Anthropic, Google, Mistral, Sakana, local models, and Chinese models
all at once. That creates provider-management work before the benchmark earns it.

### Phase 2: Sakana AI Fugu

Treat Fugu as a strategy, not as magic.

Future strategies:

- `fugu`
- `fugu-max`
- `fugu-ultra`
- `fugu-cyber`, only for approved cybersecurity tasks

The interesting question for Sakana is:

> Where does Fugu's orchestration beat deterministic routing on quality,
> cost, or latency?

That framing makes this project complementary to Sakana, not competitive.

## Chinese Model Policy

Chinese-origin models should not be dismissed technically, but they need a clear
security boundary.

Proposed policy:

- no hosted Chinese API endpoints with company/private data without written approval
- public or synthetic benchmarks are acceptable for research comparison
- self-hosted open weights can be reviewed separately from hosted APIs
- results should be marked `research_only` until approved

Question for security:

> Are Chinese-origin models forbidden entirely, or only hosted Chinese API
> endpoints handling company data?

That distinction matters.

## Local Model Policy

Do not promise local models until hardware is known.

Local evaluation is useful later if the company can provide appropriate GPU
capacity. Until then, keep local models as a Phase 2 or Phase 3 extension.

## What Is Implemented In Phase 1

- richer benchmark with 36 labeled tasks
- task labels in result records
- deterministic `policy_router`
- risk, sensitivity, and task-type summary tables
- OpenAI API config example
- preserved Phase 0 config

## What Is Deliberately Not Implemented Yet

- SSO
- dashboards
- approval workflows
- real org hierarchy permissions
- local model serving
- provider-specific SDKs
- Fugu adapter beyond OpenAI-compatible future compatibility

Those are productization steps. Phase 1 is still an evaluation framework.

## Run Commands

Phase 1 synthetic run:

```powershell
uv run python -m model_routing_mvp --config config.example.json
```

Phase 1 OpenAI run:

```powershell
$env:OPENAI_API_KEY = "..."
uv run python -m model_routing_mvp --config config.phase1.openai.example.json
```

## Expected Output

The run writes:

- `outputs/results.jsonl`
- `outputs/results.csv`
- `outputs/summary.md`

The summary report shows:

- strategy metrics
- routing distribution
- risk metrics
- sensitivity metrics
- task-type metrics

## Career-Grade Framing

Do not present this as:

> I built a router.

Present it as:

> I built a deterministic evaluation harness for measuring when cheap models are
> enough, when strong models are justified, and when orchestration like Fugu
> creates measurable value beyond rule-based routing.

## Sources

- OpenAI GPT-5 developer announcement: https://openai.com/index/introducing-gpt-5-for-developers/
- OpenAI Models API: https://developers.openai.com/api/reference/resources/models
- Mistral model overview: https://docs.mistral.ai/models
- Mistral pricing: https://docs.mistral.ai/inference/pricing
- Sakana AI Fugu models: https://console.sakana.ai/models
