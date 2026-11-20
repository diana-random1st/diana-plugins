#!/usr/bin/env python3
"""ChatGPT Pro automation in Brave Personal via Playwright MCP (Diana gateway).
Reads prompt from stdin, prints response to stdout."""

import sys
import time

from pwmcp import Browser

INPUTS = [
    'div#prompt-textarea[contenteditable="true"]',
    'div[contenteditable="true"][data-placeholder]',
    'div[contenteditable="true"]',
    'textarea[id="prompt-textarea"]',
]
ASSISTANT = [
    '[data-message-author-role="assistant"] .markdown',
    '[data-message-author-role="assistant"]',
    "article:last-child .markdown",
    "article:last-child",
]


def wait_for_completion(b, timeout=180):
    """Poll until streaming stops: stop-button disappears or text stabilises."""
    deadline = time.time() + timeout
    stop = "() => !!document.querySelector('[data-testid=\"stop-button\"]')"

    # Phase 1: wait for generation to start (up to 10s)
    for _ in range(20):
        if b.evaluate(stop):
            break
        time.sleep(0.5)

    # Phase 2: wait for stop-button to disappear
    while time.time() < deadline:
        if not b.evaluate(stop):
            return True
        time.sleep(1)

    # Phase 3 fallback: text stability check
    last = ""
    stable = 0
    while time.time() < deadline:
        cur = extract_response(b)
        if cur and cur == last:
            stable += 1
            if stable >= 4:
                return True
        else:
            stable = 0
            last = cur
        time.sleep(1)

    return False


def extract_response(b):
    return b.evaluate("""(sels) => {
      for (const sel of sels) {
        const els = document.querySelectorAll(sel);
        if (els.length) return els[els.length - 1].innerText.trim();
      }
      return '';
    }""", ASSISTANT) or ""


def run(prompt: str) -> str:
    b = Browser("personal")
    # Reuse the session's ChatGPT tab; a fresh conversation either way.
    b.use_tab("chatgpt.com", "https://chatgpt.com/")
    b.navigate("https://chatgpt.com/")

    input_sel = b.run("""async (page, sels) => {
      for (const sel of sels) {
        try { await page.waitForSelector(sel, {timeout: 5000}); return sel; } catch (e) {}
      }
      return null;
    }""", INPUTS)
    if not input_sel:
        raise RuntimeError(
            "ChatGPT input field not found — is Brave Personal logged in to chatgpt.com?"
        )

    # Click, clear, insert the whole prompt at once, send
    b.run("""async (page, a) => {
      await page.click(a.sel);
      await page.keyboard.press('Meta+a');
      await page.keyboard.insertText(a.prompt);
      await page.waitForTimeout(500);
      await page.keyboard.press('Enter');
    }""", {"sel": input_sel, "prompt": prompt})

    if not wait_for_completion(b):
        print("[chatgpt.py] WARNING: timed out waiting for response", file=sys.stderr)

    time.sleep(0.5)
    # Leave tab open (don't close — user may want to continue in browser)
    return extract_response(b)


if __name__ == "__main__":
    prompt = sys.stdin.read().strip()
    if not prompt:
        print("Error: empty prompt on stdin", file=sys.stderr)
        sys.exit(1)

    try:
        response = run(prompt)
        print(response)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
