---
name: diana-security-audit
description: Deep security audit of a codebase or files — scanners via security-scan, full-history secrets, dependency CVEs, OWASP Top 10 code pass, agent-config leaks, threat model, verified report. Triggers on 'security audit', 'security scan', 'vulnerability check', 'pentest review'.
---

# Diana Security Audit

For a diff review use `diana-review`; this is the deep pass.

1. **Frame.** `recall` earlier audits of this target in Hindsight (`bank_id: diana`). Create a tracker card. Scope: named files, recent changes (`git log --oneline -20`), or the whole repo.

2. **Scanners.** Run the `security-scan` skill (semgrep, trivy, gitleaks; SARIF, severity gating, waivers). Infra and deploy surfaces → `infra-scan`.

3. **Secrets, whole history.** Values stay redacted, never copied into the report:
   ```bash
   gitleaks git --redact --no-banner -f json -r /tmp/gitleaks-history.json .
   ```
   Also check `.gitignore` covers `.env*`, keys, local settings.

4. **Agent-config leaks.** `permissions.allow` entries in `.claude/settings*.json` capture literal tokens from approved commands; MCP and Codex configs carry tokens too. Prints file:line, rule, masked value and exposure (tracked, ignored, GitHub visibility); exit 1 = findings:
   ```bash
   ~/.agents/skills/diana-security-audit/scripts/agent_config_leaks.py --root . --history
   ```

5. **Dependencies.** `cargo audit` · `uv audit --frozen` · `bun audit` or `npm audit` → CVE, severity, package, fixed version.

6. **Code pass.** Write the threat model in 5 lines first (assets, entry points, trust boundaries), then hunt where they meet. Sources: OWASP Top 10, current edition (https://top10.owasp.org/) · ASVS for requirement-level depth (https://asvs.owasp.org/) · fixes (https://cheatsheetseries.owasp.org/)

7. **Verify.** Reproduce each CRITICAL/HIGH (probe, test, PoC on a local copy). High-stakes verdicts → `tribunal`.

8. **Report.** Scope, date, overall risk; findings by severity with file:line, impact, fix, [VERIFIED]/[INFERRED]; CVE list; prioritized actions. Durable lessons → `retain` (tag `infra`).
