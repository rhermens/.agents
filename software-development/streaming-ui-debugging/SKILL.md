---
name: streaming-ui-debugging
description: Debug streaming chat/UI bugs where live events, persisted history, and display settings interact.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [debugging, streaming-ui, chat-ui, websocket, hydration, regression-tests]
    related_skills: [systematic-debugging, test-driven-development, hermes-agent]
---

# Streaming UI Debugging

Use this when a chat/agent desktop or web UI shows duplicate output, missing output, stale transcript content, flickering state, or settings that work live but not after reload.

## Core principle

Treat the UI as at least two data paths:

1. Live stream path — WebSocket/SSE/stdout events such as `message.start`, `message.delta`, `reasoning.delta`, `tool.start`, `message.complete`.
2. Hydration path — persisted session/history API that reconstructs the transcript after reload, session switch, or completion fallback.

A bug can be fixed in one path and still reproduce in the other.

## Debug sequence

1. Confirm the user-visible symptom precisely.
   - Is the full answer duplicated?
   - Is reasoning/thinking shown alongside final text?
   - Does it happen while streaming, only after completion, or only after reload/session switch?

2. Inspect the relevant display/config toggle.
   - Identify the canonical config key and default.
   - Verify whether the live session stores a per-session copy of the setting.
   - Beware raw-config loaders that differ from default-merged config loaders.

3. Build a red-capable test at the live event seam.
   - Patch/mock the emitter.
   - Set the session state/config that should suppress or transform an event.
   - Invoke the callback/event adapter directly.
   - Assert that suppressed events are not emitted, and enabled events still are.

4. Build a red-capable test at the hydration seam.
   - Feed stored messages that include fields such as `content`, `reasoning`, `reasoning_content`, tool calls, or provider-specific reasoning items.
   - Assert that the transcript conversion/API response honors the same display setting as the live stream.

5. Fix the source of divergence, not the renderer symptom.
   - Prefer gating/sanitizing at the backend or adapter that owns the setting.
   - Avoid hiding with CSS unless the data is intentionally still present for accessibility/copy/export.

6. Verify both seams.
   - Run the focused live-event test.
   - Run the focused hydration/conversion test.
   - If feasible, run the relevant component or e2e test that renders the transcript.

## Common pitfalls

- Duplicate-looking output may actually be reasoning/thinking plus final answer, not two final answers.
- Completion handlers often replace streamed text, but hydration may later reinsert persisted fields.
- Persisted assistant rows can contain both visible content and reasoning fields; transcript conversion must decide whether to expose reasoning.
- `show_reasoning: false` or similar toggles need to affect live callbacks and history APIs consistently.
- Tool-only assistant messages and reasoning-only assistant messages often have special grouping logic; regression tests should include them if the bug involves tool calls.

## Minimal regression-test pattern

```python
def test_live_reasoning_respects_display_toggle(monkeypatch):
    emitted = []
    monkeypatch.setitem(server._sessions, "sid", {"show_reasoning": False})
    monkeypatch.setattr(server, "_emit", lambda event, sid, payload=None: emitted.append((event, sid, payload)))

    server._agent_cbs("sid")["reasoning_callback"]("hidden thought")

    assert emitted == []
```

Add a companion hydration test that passes stored assistant messages containing both `content` and `reasoning_content` through the session-message API or transcript converter and asserts reasoning is absent when the display toggle is off.

## Reference notes

- `references/hermes-desktop-duplicate-output.md` — concrete Hermes desktop duplicate-output investigation with live reasoning-event tests and the matching hydration seam to check.

## Verification checklist

- [ ] Live event stream honors the setting.
- [ ] Persisted session/history hydration honors the same setting.
- [ ] Enabled/default path still shows the data when intended.
- [ ] Test fails before the fix and passes after it.
- [ ] No unrelated renderer/CSS masking was used as the primary fix.
