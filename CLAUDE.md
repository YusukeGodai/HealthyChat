# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

HealthyChat — an AI health monitoring chat app built with **Flask** (Python backend) and **vanilla JavaScript** (frontend). The UI and all prompts are in Simplified Chinese.

The core idea: a main chat model (Model A) converses naturally while embedding a hidden `[MONITOR]` JSON block in every response. If the monitor detects a psychological or physical health issue, the backend dispatches to a specialist model (Model B for psychology, Model C for health) and streams intervention/advice to the client.

## Running the App

```bash
python app.py
# Serves on http://127.0.0.1:5000, debug mode on
```

Dependencies: Flask, Requests. No requirements.txt yet — install manually.

## Running Tests

```bash
python test_scenarios.py
```

Tests 4 scenarios (normal chat, suggest intervention, force intervention, health advice). Note: includes 30-second rate-limit sleeps between calls.

## Architecture

```
Browser (index.html + app.js)
   ↕ HTTP / SSE
Flask Backend (app.py)
   ├── Model A (chat + hidden monitor)
   │     → detects "psychological" → Model B (crisis assessment, last 10 msgs)
   │     → detects "health"        → Model C (health advice, last 25 msgs)
   ├── LLMClient (models.py) — OpenRouter-compatible API with retry/backoff
   └── Session store — in-memory dict keyed by UUID sid
```

### Key files

- `app.py` — Flask routes (`/`, `/api/config`, `/api/chat`, `/api/clear`) and SSE streaming logic
- `models.py` — `LLMClient` class: wraps OpenAI-compatible chat completions with retry (3 attempts, exponential backoff)
- `prompts.py` — System prompts for Models A, B, C (Chinese). Defines the `[RESPONSE]`/`[MONITOR]` output format
- `config.py` — Default API base, key, and model name
- `templates/index.html` — Single-page app shell
- `static/app.js` — Frontend: chat UI, SSE event handling, config modal
- `static/style.css` — Styling

### SSE event types

`assistant_message` | `thinking` | `intervention` | `health_advice` | `error` | `done`

### Model A response format

Model A returns a `[RESPONSE]` block (visible to user) and a `[MONITOR]` JSON block (hidden). The monitor JSON has `detected` (none/psychological/health), `severity`, and `reason` fields. Parsing uses regex with multiple fallback strategies.

### Intervention levels

- **Psychological:** `suggest` (common issues) or `force` (life-threatening, e.g. suicidal ideation)
- **Health severity:** minor / moderate / serious

## Conventions

- Models are referenced as A (chat), B (psychological), C (health) throughout code and prompts.
- Configuration is per-session via Flask session cookies. API keys are masked in GET responses.
- All state is in-memory only — no database, no persistence across restarts.
