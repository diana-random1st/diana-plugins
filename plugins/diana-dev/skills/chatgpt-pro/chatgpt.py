#!/usr/bin/env python3
"""ChatGPT Pro automation via Brave CDP. Reads prompt from stdin, prints response to stdout."""

import sys
import time


def wait_for_completion(page, timeout=180):
    """Poll until streaming stops: stop-button disappears or text stabilises."""
    deadline = time.time() + timeout

    # Phase 1: wait for generation to start (up to 10s)
    for _ in range(20):
        if page.query_selector('[data-testid="stop-button"]'):
            break
        time.sleep(0.5)

    # Phase 2: wait for stop-button to disappear
    while time.time() < deadline:
        if not page.query_selector('[data-testid="stop-button"]'):
            return True
        time.sleep(0.5)

    # Phase 3 fallback: text stability check
    last = ""
    stable = 0
    while time.time() < deadline:
        msgs = page.query_selector_all('[data-message-author-role="assistant"]')
        cur = msgs[-1].inner_text() if msgs else ""
        if cur and cur == last:
            stable += 1
            if stable >= 4:
                return True
        else:
            stable = 0
            last = cur
        time.sleep(1)

    return False


def extract_response(page):
    for sel in [
        '[data-message-author-role="assistant"] .markdown',
        '[data-message-author-role="assistant"]',
        "article:last-child .markdown",
        "article:last-child",
    ]:
        els = page.query_selector_all(sel)
        if els:
            return els[-1].inner_text().strip()
    return ""


def run(prompt: str) -> str:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://localhost:41922")
        context = browser.contexts[0]

        # Reuse existing ChatGPT tab or open new one
        existing = [pg for pg in context.pages if "chatgpt.com" in pg.url]
        if existing:
            page = existing[0]
            page.bring_to_front()
            # Navigate to fresh conversation
            page.goto("https://chatgpt.com/")
        else:
            page = context.new_page()
            page.goto("https://chatgpt.com/")

        page.wait_for_load_state("domcontentloaded")
        time.sleep(2)

        # Find input field
        input_sel = None
        for sel in [
            'div#prompt-textarea[contenteditable="true"]',
            'div[contenteditable="true"][data-placeholder]',
            'div[contenteditable="true"]',
            'textarea[id="prompt-textarea"]',
        ]:
            try:
                page.wait_for_selector(sel, timeout=5000)
                if page.query_selector(sel):
                    input_sel = sel
                    break
            except Exception:
                continue

        if not input_sel:
            raise RuntimeError(
                "ChatGPT input field not found — is Brave logged in to chatgpt.com?"
            )

        # Click, clear, type
        page.click(input_sel)
        time.sleep(0.3)
        page.keyboard.press("Meta+a")
        time.sleep(0.1)

        # For large prompts write to clipboard and paste
        page.evaluate(f"navigator.clipboard.writeText({repr(prompt)})")
        page.keyboard.press("Meta+v")
        time.sleep(0.5)

        # Send
        page.keyboard.press("Enter")

        # Wait for response
        ok = wait_for_completion(page)
        if not ok:
            print(
                "[chatgpt.py] WARNING: timed out waiting for response", file=sys.stderr
            )

        time.sleep(0.5)
        result = extract_response(page)

        # Leave tab open (don't close — user may want to continue in browser)
        return result


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
