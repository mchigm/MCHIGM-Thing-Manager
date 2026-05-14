# AI Memo & MCP Client

## MEMO — natural‑language → structured `Item`

The MEMO page (`src/ui/pages/memo.py`) gives the user a chat‑style input. When they hit send, the text is forwarded to `src/ai/memo_agent.py`, which asks an LLM to emit **strict JSON** that the app turns into a fully‑typed `Item`.

### Provider abstraction — `litellm`

The agent uses [litellm](https://github.com/BerriAI/litellm) as a pluggable model interface, so the same code path supports:

- **OpenAI / GPT**
- **Anthropic / Claude**
- **Google / Gemini**
- **OpenRouter**
- **OpenAI‑compatible local servers** (Ollama, LM Studio, vLLM, etc.)

Configuration lives in **Settings → AI Agent**:

| Field | Purpose |
|-------|---------|
| Provider preset | Picks default endpoint and model‑name format |
| Model name | e.g. `gpt-4o-mini`, `claude-3-5-sonnet`, `gemini-1.5-flash` |
| Base URL (optional) | For local / OpenRouter / proxy endpoints |
| API key | Stored in `settings.json` (local‑only) |

litellm itself is wrapped in a `try/except` import so the app still starts even if the optional dependency is missing.

### System prompt and JSON contract

The agent sends a strict system prompt that instructs the model to return JSON of the form:

```json
{
  "title": "string",
  "type": "Task | Event | Note | Goal",
  "status": "Backlog | To-Do | Doing | Done",
  "description": "string",
  "estimated_time": 60,
  "workload": 3,
  "deadline": "2026-05-20T15:00:00Z",
  "tags": ["urgent", "cs101"]
}
```

The parser then:

1. Validates the type/status against `ItemType` / `ItemStatus` enums.
2. Coerces times to UTC‑aware datetimes.
3. Looks up or creates the named tags.
4. Persists a new `Item` via `SessionLocal()`.

### Graceful fallback

If no model is configured (no API key, no base URL, or litellm is unavailable), the MEMO page still saves the raw text as a **Backlog `NOTE`** item. The workflow never fails closed.

### OpenClaw CLI

MEMO also exposes an **Install CLI** action that installs the **OpenClaw CLI** from inside the app — a companion command‑line tool for headless capture. The installer is invoked through `subprocess` and the UI surfaces progress / errors.

---

## MCP Client (beta)

The Model Context Protocol (MCP) integration lives in `src/mcp_client.py` and is configured under **Settings → MCP Client**.

| Setting | Notes |
|---------|-------|
| Server URL | Points at the user's MCP server (e.g. Craft, Teams connectors) |
| Connection status | UI surfaces success / error / not‑connected |

The MCP integration is opt‑in — install the official package to enable live connections:

```bash
pip install "mcp[cli]"
```

Without it installed, the Settings tab still loads and the field is editable, but live calls are stubbed. Tests in `tests/test_mcp_client.py` cover the offline path so the rest of the app is unaffected.

---

## Security considerations

- API keys and MCP URLs are written to `~/.mchigm_thing_manager/settings.json` in plaintext. Treat that file as sensitive.
- All LLM calls are outbound HTTPS via litellm. There is no proxying through the app's own servers.
- The agent prompt instructs the model to **only emit JSON**, but malicious / malformed responses are caught by validation; on failure the MEMO falls back to saving the raw text.
- The OpenClaw CLI installer uses `subprocess` with explicit arguments — no shell interpolation of user input.
