"""Playwright MCP client for skill scripts.

Drives Roman's real Brave profile through the Diana gateway and the Playwright
extension. No CDP port, no browser relaunch. Stdlib only.

    from pwmcp import Browser
    b = Browser("personal")                         # or "quandex"
    b.use_tab("app-ads.apple.com", "https://app-ads.apple.com/cm/app/1/report")
    b.run("async (page) => page.title()")           # Playwright code -> JSON value
    b.evaluate("(arg) => document.title + arg", "!")  # in-page JS -> JSON value

Canonical copy: diana-personal/skills/browser-cdp/scripts/pwmcp.py. Other skills
carry a copy next to their scripts; change this one first, then the copies.
Gateway base URL: $DIANA_GATEWAY_URL (default http://127.0.0.1:9852/mcp).
"""
import base64
import json
import os
import re
import urllib.request

GATEWAY = os.environ.get("DIANA_GATEWAY_URL", "http://127.0.0.1:9852/mcp")
TAB_LINE = re.compile(r"^- (\d+): (\(current\) )?\[(.*)\]\((.*)\)$")


class BrowserError(RuntimeError):
    pass


class Browser:
    def __init__(self, profile: str = "personal", timeout: float = 300):
        self.url = f"{GATEWAY}/playwright-{profile}"
        self.timeout = timeout
        self.session = None
        self.n = 0
        self._rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
                                 "clientInfo": {"name": "pwmcp", "version": "1"}})
        self._rpc("notifications/initialized", notify=True)

    def _rpc(self, method, params=None, notify=False):
        body = {"jsonrpc": "2.0", "method": method, "params": params or {}}
        if not notify:
            self.n += 1
            body["id"] = self.n
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        if self.session:
            headers["Mcp-Session-Id"] = self.session
        req = urllib.request.Request(self.url, json.dumps(body).encode(), headers)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                self.session = r.headers.get("Mcp-Session-Id") or self.session
                raw = r.read().decode()
        except OSError as e:
            raise BrowserError(f"Diana gateway unreachable at {self.url} ({e}); "
                               "check `diana gateway status` and `diana gateway list`") from e
        if notify:
            return None
        msgs = [json.loads(line[5:]) for line in raw.splitlines() if line.startswith("data:")] or [json.loads(raw)]
        msg = next((m for m in msgs if m.get("id") == self.n), msgs[-1])
        if "error" in msg:
            raise BrowserError(f"{method}: {msg['error']}")
        return msg["result"]

    def call(self, tool: str, **args) -> str:
        """Call any Playwright MCP tool; return its text output."""
        res = self._rpc("tools/call", {"name": tool, "arguments": args})
        text = "\n".join(c.get("text", "") for c in res.get("content", []) if c.get("type") == "text")
        if res.get("isError") or text.lstrip().startswith("### Error"):
            raise BrowserError(f"{tool}: {text.strip()[:800]}")
        return text

    @staticmethod
    def _result(text: str):
        m = re.search(r"### Result\n(.*?)(?=\n### |\Z)", text, re.S)
        if not m:
            return None
        try:
            return json.loads(m.group(1))
        except ValueError:
            return m.group(1).strip()

    def run(self, code: str, arg=None):
        """Run Playwright code `async (page[, arg]) => ...` in the current tab."""
        if arg is not None:
            code = f"async (page) => ({code})(page, {json.dumps(arg)})"
        return self._result(self.call("browser_run_code_unsafe", code=code))

    def evaluate(self, function: str, arg=None):
        """Evaluate in-page JS `() => ...` or `(arg) => ...`; promises are awaited."""
        if arg is not None:
            function = f"() => ({function})({json.dumps(arg)})"
        return self._result(self.call("browser_evaluate", function=function))

    def navigate(self, url: str):
        self.call("browser_navigate", url=url)

    def tabs(self) -> list[dict]:
        """Tabs this Playwright session controls. Roman's own tabs are not listed."""
        out = []
        for line in self.call("browser_tabs", action="list").splitlines():
            m = TAB_LINE.match(line.strip())
            if m:
                out.append({"index": int(m[1]), "current": bool(m[2]), "title": m[3], "url": m[4]})
        return out

    def use_tab(self, url_fragment: str, fallback_url: str | None = None) -> dict:
        """Make the tab showing url_fragment current; open fallback_url only if none does.

        Exactly one tab may match: two sessions once drove the same RevenueCat tab
        and wiped each other's unsaved edits, so never guess which tab is ours.
        The idle extension connect tab is reused before a new tab is opened.
        """
        tabs = self.tabs()
        matches = [t for t in tabs if url_fragment in t["url"]]
        if len(matches) > 1:
            urls = "\n  ".join(t["url"] for t in matches)
            raise BrowserError(f"{len(matches)} tabs match {url_fragment!r}; use a more specific fragment:\n  {urls}")
        if matches:
            if not matches[0]["current"]:
                self.call("browser_tabs", action="select", index=matches[0]["index"])
            return matches[0]
        if not fallback_url:
            raise BrowserError(f"no tab matches {url_fragment!r}; open it first")
        idle = next((t for t in tabs if t["url"].startswith("chrome-extension://")), None)
        if idle:
            if not idle["current"]:
                self.call("browser_tabs", action="select", index=idle["index"])
            self.navigate(fallback_url)
        else:
            self.call("browser_tabs", action="new", url=fallback_url)
        return next(t for t in self.tabs() if t["current"])

    def screenshot(self, path: str, quality: int = 55) -> str:
        """Viewport JPEG of the current tab, written to path."""
        data = self.run(f"async (page) => (await page.screenshot({{type: 'jpeg', quality: {quality}}})).toString('base64')")
        with open(path, "wb") as f:
            f.write(base64.b64decode(data))
        return path
