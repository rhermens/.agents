# Token Reduction Techniques — Detailed Reference

## Built-in ContextCompressor (default, always on)

Source: `agent/context_compressor.py`. 4-phase algorithm:

1. **Prune old tool results** (>200 chars, outside protected tail) → replaced
   with `[Old tool output cleared to save context space]`. Cheap pre-pass, no
   LLM call.
2. **Determine boundaries** — head (`protect_first_n`, default 3), middle
   (summarized), tail (token-budget based, walks backward from end).
3. **Generate structured summary** — auxiliary model writes a handoff with
   sections: Goal / Constraints & Preferences / Progress (Done, In Progress,
   Blocked) / Key Decisions / Relevant Files / Next Steps / Critical Context.
4. **Assemble** — head + summary + tail. Orphaned tool_call/result pairs
   cleaned up.

Iterative: on second+ compaction, updates the existing summary rather than
re-summarizing from scratch.

### Gateway hygiene layer (85% threshold)

Separate safety net in `gateway/run.py`. Fires at 85% of context length
before the agent processes a message. Prevents API failures in long-lived
Telegram/Discord sessions. Only triggers when `len(history) >= 4`.

### Computed values (200K context model at defaults)

```
threshold_tokens   = 200,000 × 0.50 = 100,000
tail_token_budget  = 100,000 × 0.20 = 20,000
max_summary_tokens = min(200,000 × 0.05, 12,000) = 10,000
```

### Small-context floor

Models below 512K context are floored at threshold 0.75. An override below
0.75 is raised to 0.75; an override above 0.75 (e.g. 0.80) wins.

### Codex gpt-5.5 autoraise

ChatGPT Codex OAuth hard-caps gpt-5.5 at 272K context. Hermes raises the
trigger to 85% (~231K) automatically. Opt out:
`hermes config set compression.codex_gpt55_autoraise false`

## Pluggable context engines

`context.engine` in config.yaml selects the engine. Default `"compressor"`.
Plugins can provide alternatives (e.g. `"lcm"` for Lossless Context
Management). Plugins are never auto-activated — must set engine name
explicitly. Plugin resolution: `plugins/context_engine/<name>/` → general
plugin system → fall back to built-in.

## Audit script (from mrmoe28/hermes-context-optimization)

```python
import sqlite3, getpass

db = f"/home/{getpass.getuser()}/.hermes/state.db"
conn = sqlite3.connect(db)
c = conn.cursor()

c.execute('''
  SELECT id, title, message_count, input_tokens, output_tokens
  FROM sessions ORDER BY started_at DESC LIMIT 1
''')
row = c.fetchone()
if row:
    sid, title, msgs, inp, out = row
    ratio = inp / (out or 1)
    print(f"Session: {title}")
    print(f"  Messages: {msgs} | Input: {inp:,} | Output: {out:,} | Ratio: {ratio:.0f}:1")
    c.execute('''SELECT role, COUNT(*), SUM(token_count) FROM messages
                 WHERE session_id=? GROUP BY role''', (sid,))
    print("  By role:")
    for r in c.fetchall():
        print(f"    {r[0]}: {r[1]} msgs, {r[2] or 0:,} tokens")
conn.close()
```

Danger signs: ratio > 50:1, tool messages dominating, >60 messages with
few user messages.

## Community resources

- **mrmoe28/hermes-context-optimization** — step-by-step audit guide.
  Real session data showing 100:1 input/output ratios. The 7 optimizations
  apply in order: prune skills, cap context, reduce max_turns, enable
  compaction, configure compression, cap tool output, prune memory.
  https://github.com/mrmoe28/hermes-context-optimization

- **alexgreensh/token-optimizer** — comprehensive plugin with 9 active
  compression features, session continuity, dashboard. Hermes adapter
  via `install.sh --hermes`. PolyForm Noncommercial license.
  https://github.com/alexgreensh/token-optimizer

- **christopher-s/context-mode-hermes** — Context Mode adapter for Hermes.
  Intercepts high-output tool calls via pre_tool_call/post_tool_call/
  pre_llm_call hooks. Redirects to sandboxed MCP tools.
  https://github.com/christopher-s/context-mode-hermes

- **Issue #14948** — proposal for progressive tool-result compression.
  https://github.com/NousResearch/hermes-agent/issues/14948

- **Issue #10585** — multi-resolution compression for MEMORY.md/USER.md
  static bloat. https://github.com/NousResearch/hermes-agent/issues/10585

## Token Optimizer feature comparison

| Feature | Token Optimizer | Headroom | RTK | context-mode |
|---------|-----------------|----------|-----|--------------|
| Bash/command output compression | 🟢 60+ patterns | 🟢 6 algorithms | 🟢 100+ filters | 🟡 |
| Search/grep output | 🟢 | 🔴 | 🔴 | 🟡 |
| Tabular/JSON output | 🟢 | 🟢 SmartCrusher | 🔴 | 🟡 |
| File re-reads (delta mode) | 🟢 diff only | 🔴 | 🔴 | 🔴 |
| File re-reads (structure map) | 🟢 skeleton | 🔴 | 🔴 | 🔴 |
| Large tool results (>4K) | 🟢 archived, expandable | 🔴 | 🔴 | 🔴 |
| Model output verbosity | 🟢 lean-output nudge | 🔴 | 🔴 | 🔴 |
| Structural context audit | 🟢 per-component | 🔴 | 🔴 | 🔴 |
| Compaction survival | 🟢 checkpoint+restore | 🔴 | 🔴 | 🟡 session guide |
| Session continuity | 🟢 cross-session hints | 🔴 | 🔴 | 🟡 |
| Model routing nudges | 🟢 12 detectors | 🔴 | 🔴 | 🔴 |
| Cache keep-warm | 🟢 opt-in ping | 🔴 | 🔴 | 🔴 |
