---
name: diana-security-audit
description: Comprehensive security audit of codebase or specific files. OWASP, dependency vulnerabilities, secrets detection, threat modeling. Triggers on 'security audit', 'security scan', 'vulnerability check', 'pentest review'.
---

# Diana Security Audit

Deep security analysis following OWASP methodology and DevSecOps best practices.

## Steps

1. **Scope definition**:
   - Specific files → audit those
   - No files specified → audit recent changes (`git log --oneline -20`)
   - Full audit → scan entire project structure

2. **Dependency audit**:
   - Rust: `cargo audit`
   - Python: `uv pip audit` or `pip-audit`
   - Node: `bun audit` or `npm audit`
   - Report: CVE IDs, severity, affected packages, fix versions

3. **Static analysis — OWASP Top 10**:
   - **A01 Broken Access Control**: auth checks, RBAC, IDOR
   - **A02 Cryptographic Failures**: weak crypto, plaintext secrets, insecure protocols
   - **A03 Injection**: SQL, command, LDAP, XSS, template injection
   - **A04 Insecure Design**: missing threat model, business logic flaws
   - **A05 Security Misconfiguration**: debug mode, default creds, overly permissive CORS
   - **A06 Vulnerable Components**: outdated deps (from step 2)
   - **A07 Auth Failures**: weak passwords, missing MFA, session issues
   - **A08 Data Integrity**: deserialization, unsigned updates, CI/CD poisoning
   - **A09 Logging Failures**: missing audit trail, PII in logs
   - **A10 SSRF**: unvalidated URLs, internal network access

4. **Secrets scan**:
   - Grep for patterns: API keys, tokens, passwords, connection strings
   - Check: `.env` committed? `.gitignore` complete? Secrets in config files?
   - Check git history: `git log -p --all -S "password\|secret\|api_key" -- . | head -100`

5. **Report format**:
   ```
   ## Security Audit Report

   **Scope**: [files/project]
   **Date**: [date]
   **Risk Level**: [CRITICAL|HIGH|MEDIUM|LOW]

   ### Findings

   #### 🔴 CRITICAL
   [finding with file:line, description, impact, fix]

   #### 🟡 HIGH
   ...

   #### 🔵 MEDIUM
   ...

   ### Dependencies
   [CVE list]

   ### Recommendations
   1. [prioritized actions]
   ```

6. **Save to memory**: Key findings and patterns to beliefs for future reference.
