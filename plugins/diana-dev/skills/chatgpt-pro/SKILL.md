---
name: chatgpt-pro
description: "Query ChatGPT Pro (GPT-5.4) via Brave browser automation for deep one-off tasks — architecture analysis, complex reasoning, second opinion. Uses existing Brave session with Pro auth. Triggers: 'chatgpt pro', 'ask chatgpt', 'gpt-5.4 web', 'chatgpt глубокий анализ'."
---

# ChatGPT Pro

Query ChatGPT Pro (GPT-5.4) through the authenticated Brave browser session.

**Use for:** Deep one-off tasks where you want ChatGPT Pro specifically — architecture review, complex analysis, second opinion. Not for frequent calls (fragile, slow).

## Script

```
~/.agents/skills/chatgpt-pro/chatgpt.py
```

Reads prompt from **stdin**, prints response to **stdout**.

## Protocol

### 1. Check Brave is running with CDP

```bash
curl -s http://localhost:41922/json/version \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK:', d['Browser'])" \
  2>/dev/null || echo "CDP not available"
```

If not available — launch Brave with CDP:

```bash
pkill -f "Brave Browser" 2>/dev/null; sleep 1
"/Applications/Brave Browser.app/Contents/MacOS/Brave Browser" \
  --remote-debugging-port=41922 \
  --user-data-dir="$HOME/Library/Application Support/BraveSoftware/Brave-Browser" &
disown
sleep 3
```

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
| "input field not found" | Brave not logged in to chatgpt.com — open manually and log in |
| "CDP not available" | Launch Brave with CDP (step 1) |
| Timeout (>3 min) | ChatGPT slow — response may still appear in browser tab |
| Empty response | ChatGPT rendered differently — take screenshot to debug |

## Constraints

- **One query at a time** — script opens a new conversation each run
- **No history** — each call is a fresh chat
- **Model:** Pro auto-selects GPT-5.4 (ChatGPT Pro default)
- **Tab stays open** — don't close Brave after; user can continue in browser if needed
- **ToS note:** browser automation of chatgpt.com is against OpenAI ToS — use for personal, infrequent tasks only
