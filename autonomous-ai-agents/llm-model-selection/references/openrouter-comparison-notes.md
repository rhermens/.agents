# OpenRouter Comparison Notes

Use this as a research checklist, not as a permanent price table. Re-fetch all figures before answering.

## Evidence Sources

1. OpenRouter model page: current slug, pricing, context, max output, providers, latency/throughput, privacy labels, release date, and supported controls.
2. Model developer documentation/model card: architecture, license, intended workloads, tool/reasoning support, and vendor benchmarks.
3. Artificial Analysis or another independent evaluator: intelligence, speed, latency, cost per task, and comparable reasoning settings.
4. Workload-specific evaluations where available: coding-agent, tool-use, long-context retrieval, or domain benchmark results.

## Router Checks

For `openrouter/auto`-style products, inspect the current router documentation for:

- deprecation or beta status;
- how tasks are classified;
- what ranking signal selects candidates;
- allowed-model filtering;
- cost/quality default and direction of its scale;
- model/provider stickiness across turns;
- fallback behavior;
- additional router fees.

A ranking based on community spend or usage is evidence of adoption, not proof of superior quality for the user's workload.

## Price Math

Report input and output ratios separately:

```text
input ratio  = expensive input price / cheap input price
output ratio = expensive output price / cheap output price
```

For repeated repository or conversation context, also compare cache-read prices and expected cache-hit behavior. For agent workflows, mention that verbosity, reasoning tokens, retries, and failed tool calls affect cost per completed task more than headline token price alone.

## Session Example (July 2026; stale by design)

A comparison of Hy3, GLM-5.2, and GPT-5.6 Sol illustrated a reusable three-tier framing:

- low-cost model for chat, extraction, routine edits, and retry-tolerant loops;
- value model for everyday coding and agent work;
- flagship model for difficult debugging, unattended execution, and final review.

The durable lesson is the tiered primary/escalation policy—not the specific prices or benchmark scores from that session. Recheck whether those models and tiers still exist before reusing the framing.
