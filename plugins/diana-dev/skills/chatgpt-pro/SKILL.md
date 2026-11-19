---
name: chatgpt-pro
description: "Query ChatGPT Pro (GPT-5.4) in Brave Personal via Playwright MCP for deep one-off tasks — architecture analysis, complex reasoning, second opinion. Uses the logged-in Personal profile, no CDP. Triggers: 'chatgpt pro', 'ask chatgpt', 'gpt-5.4 web', 'chatgpt глубокий анализ'."
---

# ChatGPT Pro

Query ChatGPT Pro (GPT-5.4) through the authenticated Brave **Personal** profile, driven by
Playwright MCP via the Diana gateway (`pwmcp.py` next to the script; see `browser-cdp`).

**Use for:** Deep one-off tasks where you want ChatGPT Pro specifically — architecture review, complex analysis, second opinion. Not for frequent calls (fragile, slow).

## Script

```
~/.agents/skills/chatgpt-pro/chatgpt.py
```

Reads prompt from **stdin**, prints response to **stdout**.

## Protocol

### 1. Check the gateway upstream

```bash
diana gateway test playwright-personal
```

`connected (25 tools)` is the expected answer. No browser restart is ever needed.

### 2. Write prompt to temp file and run

```bash
cat > /tmp/chatgpt-prompt.txt << 'PROMPT_EOF'
[PROMPT HERE]
PROMPT_EOF

python3 ~/.agents/skills/chatgpt-pro/chatgpt.py < /tmp/chatgpt-prompt.txt
```

For large prompts (architecture docs, code pastes) — always use the temp file approach, not inline.

### 3. Present result

Read stdout, present to user with attribution: **"ChatGPT Pro (GPT-5.4):"**.

## Error Handling

| Error | Fix |
|-------|-----|
| "input field not found" | Personal profile not logged in to chatgpt.com — ask Roman to log in there |
| "Diana gateway unreachable" | `diana gateway status`; see `browser-cdp` troubleshooting |
| Timeout (>3 min) | ChatGPT slow — response may still appear in browser tab |
| Empty response | ChatGPT rendered differently — take screenshot to debug |

## Constraints

- **Text only** — the script returns the last assistant message as text; it cannot fetch generated images. For images use the `image` skill (Codex `image_gen`)
- **One query at a time** — script opens a new conversation each run
- **No history** — each call is a fresh chat
- **Model:** Pro auto-selects GPT-5.4 (ChatGPT Pro default)
- **Tab stays open** — the Playwright session's ChatGPT tab is reused next time; Roman can continue there
- **ToS note:** browser automation of chatgpt.com is against OpenAI ToS — use for personal, infrequent tasks only
