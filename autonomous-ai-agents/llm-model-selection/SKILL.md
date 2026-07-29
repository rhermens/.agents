---
name: llm-model-selection
description: Research and compare LLMs, routers, providers, and reasoning tiers for chat, coding, agents, long-context work, cost, latency, and reliability. Use when choosing a model, evaluating an automatic router, or designing a primary/fallback model policy.
---

# LLM Model Selection

Use current evidence to recommend a model for a workload rather than declaring a universal winner.

## Workflow

1. **Disambiguate the exact model variant only when necessary.** Model families can contain materially different tiers (for example fast, flagship, pro, reasoning effort, preview, or free variants). If context makes the intended variant obvious, state the assumption and proceed.
2. **Check current first-party model/provider pages.** Confirm model slug, release status, deprecation, input/output/cache prices, context and maximum output, modalities, tool support, reasoning controls, provider count, privacy characteristics, and availability.
3. **Use independent evaluation for capability claims.** Prefer comparable settings and harnesses. Label vendor benchmarks as vendor-reported. Never compare one model at maximum reasoning against another in non-reasoning mode without saying so.
4. **Calculate price ratios explicitly.** Compare input and output separately; include cache pricing when the workload reuses large prompts. Avoid suggesting that a benchmark-score percentage is a direct measure of real-world quality.
5. **Map evidence to workload.** Distinguish interactive chat, routine code edits, repository-scale engineering, unattended agents, high-stakes review, extraction/classification, and bulk token processing.
6. **Give a decision, not merely a table.** Identify the quality winner, value winner, and recommended primary/fallback policy.
7. **Attach dates or freshness cues.** Models, discounts, routers, benchmarks, and provider availability change quickly.

## Selection rule

Use constraints before preferences:

```text
eligible(m, w) ⇔ available(m) ∧ capabilities(m) ⊇ requirements(w)
                 ∧ context(m) ≥ required_context(w)
                 ∧ cost(m, w) ≤ budget(w)
recommended(w) = argmax utility(m, w), for eligible models m
```

`argmax` means the eligible model with the highest workload-specific utility. Derive utility from the user's quality, reliability, latency, privacy, and cost priorities.

If no model is eligible, identify the violated constraints. Ask which constraint may change.

## Router Evaluation

When assessing an automatic router:

- Verify whether the named router is current, beta, or deprecated.
- Explain its actual selection signal (task classifier, popularity/spend, benchmark rank, price filter, etc.). Do not equate popularity with task-specific quality.
- Check cost/quality defaults; defaults may be much more cost-oriented than users expect.
- Check model allowlists, provider/privacy controls, fallback behavior, and session stickiness.
- Prefer fixed models plus explicit fallbacks for reproducibility, debugging, benchmarks, and high-stakes production.
- Prefer routers for heterogeneous traffic, discovery, and workloads where prompt types are unknown in advance.

## Comparison Dimensions

Use only dimensions that materially affect the decision:

- Quality and instruction adherence
- Coding and tool-use reliability
- Long-horizon consistency
- Input, output, and cache cost
- Context window and maximum output
- Time to first token and output throughput
- Provider diversity, uptime, and privacy/logging
- Open weights and license
- Verbosity/token efficiency
- Stability: preview status, deprecation, and model drift

## Recommendation Pattern

Keep the answer compact unless the user requests depth:

1. One-line verdict.
2. Small table with current, decision-relevant numbers.
3. Short bullets for where each model wins.
4. Concrete primary/fallback recommendation.
5. Links to first-party pages and the independent comparison.

For follow-up questions such as “and model X?”, extend the existing comparison rather than repeating the entire prior explanation. Emphasize where X fits in the already-established quality/value ladder.

## Pitfalls

- Do not rely on remembered prices, model names, release status, or benchmarks.
- Do not treat aggregate intelligence indexes as coding-agent success rates.
- Do not infer reliability from context-window size.
- Do not hide differences in reasoning effort or benchmark harness.
- Do not recommend a cheap model merely because per-token pricing is low; verbose reasoning and retries can erase savings.
- Do not describe an automatic router as deterministic when rankings or eligible pools can change.

## References

- See `references/openrouter-comparison-notes.md` for a compact evidence checklist and examples of router/model comparison details that can change over time.
