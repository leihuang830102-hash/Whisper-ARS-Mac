# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A self-built macOS local voice-dictation tool: a global hotkey triggers recording, Whisper Large v3 Turbo (via mlx-whisper) transcribes locally, and the text is typed at the cursor. Fully local, no cloud, no subscription. Phase A (MVP) is complete and verified working.

## Commands

**Python interpreter caveat (critical):** the system `/usr/bin/python3` is 3.9 (too old; project needs ≥3.11). Always use the venv at `.venv/` (Python 3.13 from miniconda). Prefix every python/pytest command with `source .venv/bin/activate`, or call `.venv/bin/python` / `.venv/bin/python -m pytest` directly. Never invoke bare `python3`.

```bash
# Run tests (all)
source .venv/bin/activate && pytest -q

# Run a single test file / single test
pytest tests/test_hotkey.py -v
pytest tests/test_audio.py::test_should_transcribe_rejects_silence_and_short -v

# Run the dictation app (live — needs macOS permissions, see below)
python -m whisper_dictation.app

# First-time model download (HuggingFace is blocked in China — this uses ModelScope)
python scripts/download_model.py      # → models/whisper-large-v3-turbo/ (~1.6GB, gitignored)

# Engine smoke test (records from mic, transcribes with real model)
python scripts/smoke_transcribe.py

# Build the double-clickable .app wrapper (thin launcher → opens Terminal)
bash scripts/build_app.sh             # → ~/Applications/WhisperDictation.app
```

Editable install: `pip install -e ".[dev]"` (already done in the venv).

## Architecture

Linear pipeline orchestrated by `app.py`; each stage is its own module with one responsibility and is unit-testable in isolation:

```
hotkey (pynput global listener) ──on_press/on_release──► ModeMachine ──start/stop──► app.py
                                                                                          │
                                    audio.record_into  ◄──────────────────────────  _start (PTT/toggle)
                                          │                                               │
                                    audio.flatten ─► audio.should_transcribe (silence guard)
                                                          │                                 │
                                              transcribe.transcribe (mlx-whisper, local model)
                                                          │                                 │
                                              typer.type_text (clipboard + Cmd+V)  ◄─────────┘
```

**Key design decisions (the non-obvious bits):**
- **Local model, never HF hub.** `mlx_whisper.load_model()` checks `Path(path).exists()` first — if `config.yaml:model` points at an existing local dir, it skips `snapshot_download` entirely. The model is fetched from ModelScope (not HuggingFace — blocked in China; hf-mirror redirects to origin). See `scripts/download_model.py`.
- **CJK input via clipboard, not key events.** `typer.type_text` writes to the pasteboard then simulates Cmd+V (`Quartz.CGEventCreateKeyboardEvent` + `Quartz.CGEventSetFlags` + `CGEventPost`). Single key events can't reliably type Chinese. Note: `CGEventRef` has no `.setFlags` method in pyobjc — must use the `Quartz.CGEventSetFlags(event, flags)` function.
- **Hotkey state machine is pure logic, decoupled from system events.** `hotkey.ModeMachine` (`on_press`/`on_release` → `'start'`/`'stop'`/`'noop'`) is fully unit-tested; `register_hotkey` (pynput) is a thin event adapter over it. Both PTT and toggle are driven by the same press/release events.
- **Silence guard.** `audio.should_transcribe()` rejects near-silent / too-short audio before sending to the model — prevents Whisper's repetition hallucination on silence.
- **`app._start` double-start guard keys on `self._stream is not None`, not `machine.is_recording`** (the machine state mutates before dispatch, so `is_recording` would always be True and block `record_into`).

## Running live — macOS permissions (the main friction)

Global hotkey + synthetic keystrokes require TCC permissions, and **TCC attributes them to the responsible process**:
- Running from inside an IDE (e.g. Trae CN) fails silently — the IDE's main-app permission doesn't cover its Helper subprocess, so pynput reports `running=True` but receives **0 events**.
- **Always run from a signed standalone terminal (Terminal.app / iTerm)** that has been granted Accessibility + Input Monitoring + Microphone, then fully quit+reopened. The packaged `.app` works around this by launching Terminal via `osascript` (reuses Terminal's permissions; the .app itself needs none).
- Diagnostic for "hotkey does nothing": run a 10s `pynput.keyboard.Listener` printing every keypress — 0 output means permissions didn't reach the responsible process.

Full setup steps and pitfalls: `docs/PERMISSIONS.md`, `LESSONS_LEARNED.md`.

## Hotkey constraints

Supported: modifiers `ctrl/option/cmd/shift` + key (letters, digits, `space`, `enter`, `f1`–`f20`). Avoid:
- `fn` — not reported by pynput (system-intercepted).
- `cmd+space` — conflicts with Spotlight.
- Bare F-keys (e.g. F5) when "Use F1, F2 etc as standard function keys" is off — they arrive as media keycodes (e.g. F5 → `<176>`), not `Key.f5`.

Current default hotkey: `ctrl+shift+space` (avoids all the above; also avoids `option+space` which types a non-breaking space).

## Config

`config.yaml` at repo root: `mode` (`ptt`/`toggle`), `hotkey`, `model` (local dir path), `language`, `sample_rate`. Parsed by `config.load_config` / `parse_hotkey`. The app reads it at startup — change it then restart.
