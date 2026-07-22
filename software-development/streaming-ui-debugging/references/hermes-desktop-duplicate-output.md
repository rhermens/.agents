# Hermes desktop duplicate output investigation

Session-specific lesson: the desktop app can appear to show model output twice when reasoning/thinking text is rendered in addition to final assistant content.

Observed clues:

- User config had `display.show_reasoning: false`.
- Recent desktop session rows in `state.db` stored assistant `content` plus `reasoning` / `reasoning_content`.
- The live WebSocket gateway still emitted reasoning frames:
  - `reasoning.delta` via `reasoning_callback`
  - `reasoning.available` from tool-progress/review-summary callbacks
- Therefore there are two seams to test/fix:
  1. Live gateway event emission should not emit reasoning events when the session display setting disables reasoning.
  2. Session-message hydration/API should strip or omit reasoning fields when reasoning display is disabled, otherwise old sessions can still show reasoning after reload.

Useful focused red tests:

```python
def test_reasoning_callback_respects_session_show_reasoning(monkeypatch):
    emitted = []
    monkeypatch.setitem(server._sessions, "sid-hidden", {"show_reasoning": False})
    monkeypatch.setattr(server, "_emit", lambda event, sid, payload=None: emitted.append((event, sid, payload)))

    server._agent_cbs("sid-hidden")["reasoning_callback"]("hidden thought")

    assert emitted == []


def test_reasoning_available_respects_session_show_reasoning(monkeypatch):
    emitted = []
    monkeypatch.setitem(server._sessions, "sid-hidden", {"show_reasoning": False})
    monkeypatch.setattr(server, "_emit", lambda event, sid, payload=None: emitted.append((event, sid, payload)))

    server._on_tool_progress("sid-hidden", "reasoning.available", preview="hidden summary")

    assert emitted == []
```

Implementation direction used in the session:

- Add a helper like `_show_reasoning_enabled(sid)` in the gateway server.
- Gate `reasoning_callback` and `reasoning.available` before emitting.
- Add a separate hydration/API sanitization helper for stored messages so assistant reasoning keys are removed when the display toggle is off.

Do not capture transient pytest/venv setup failures as rules. The durable lesson is the two-path live-stream vs hydration debugging pattern.
