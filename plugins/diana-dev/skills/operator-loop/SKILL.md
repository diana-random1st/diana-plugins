---
name: operator-loop
description: "Run a Product-Operated Agentic SDLC — hypotheses through the seven-stage loop (Hypothesis → Prototype → Spec → Agent Run → Review → Measure → Verdict) over MCP-connected tools. Vendor-neutral."
triggers: ["operator-loop", "init POAS", "bootstrap hypothesis board", "new hypothesis", "advance hypothesis", "operator-loop status", "operator-loop verdict", "POAS"]
---

# Operator Loop

Product-Operated Agentic SDLC. Two modes: `init` (one-time bootstrap) and operations (daily subcommands). Vendor-neutral — specifies service types, not brands. Reference: https://random1st.click/operator-loop.html

## Where it actually runs

No local `/operator-loop` CLI exists — `init` and the subcommands below are the methodology contract. The running system (Hermes, Operator host) lives in two repos:

- `~/src/operator-loop-plugin` — Hermes runtime plugin `plugins/operator-loop/` (intake, ingress, tracker, gates, dashboard).
- `~/src/pm/ol-deploy` — operator profile and role skills: `integrations/hermes/operator-loop/profiles/operator/skills/operator-loop-{operator,coder,tester,staging-builder}/`.
- Host health and deploys: `operator-host` skill.

## Invariants

Signals live in the Insight Inbox, not in board columns. Unit of work is a hypothesis with a falsification threshold. Done is a telemetry-backed verdict, not a merge. Agent output is an evidence package, not a closure. Engineering owns the Review column and all takeover triggers. Skill never merges PRs or writes to `main` directly.

## Service slots

| Slot | Purpose |
|------|---------|
| `tracker` | Hypothesis / Insight / Delivery tickets (Jira, Linear, Asana, ClickUp) |
| `code_host` | Branches, PRs, CI config (GitHub, GitLab, Bitbucket) |
| `design` | Design context for prototype stage (Figma, Penpot) — optional |
| `ci` | Test + eval + cost + complexity gates (GitHub Actions, GitLab CI, CircleCI) |
| `feature_flag` | Cohort rollout + kill switch (LaunchDarkly, Statsig, Unleash) |
| `analytics` | Metrics, dashboards (Amplitude, PostHog, Redash, Mixpanel) |
| `notifications` | Alerts + stage-transition pings (Slack, Telegram, PagerDuty, webhook) |

`tracker`, `code_host`, `ci`, `feature_flag`, `analytics`, `notifications` are required. `design` is optional. If any required vendor has no wired MCP, init stops with a diagnostic naming the missing MCP. Vault: `operator-loop/<project>/<slot>`.

## Init mode (`/operator-loop init`)

1. For each slot: ask vendor name, then vendor-specific follow-ups (project key, workspace, channel, etc.). For `design`, ask if relevant first.
2. Map each vendor to a wired MCP; stop with diagnostic if missing.
3. Prompt for missing vault secrets.
4. Sanity-check: one API call per slot to verify credentials. Failure stops bootstrap and rolls back.
5. Create infrastructure atomically (checkpointed; rollback via inverse API calls):
   - Tracker: issue types (Hypothesis, Insight, Verdict), workflow statuses, per-hypothesis fields, transition validators
   - Code host: branch protection (≥1 reviewer, required status checks, no self-approve), CODEOWNERS for auth/payments/security, CI workflow template, PR template
   - Analytics dashboard: per-hypothesis metric + guardrails + rollout-cohort charts
   - Feature-flag env: `operator-loop-<project>`, kill-switch flag `project:kill` (default OFF)
   - Notifications: register channel, send test message
   - MCP wiring in `~/.diana/mcp.json`
6. Save project config to `~/.diana/projects/<name>.yaml`.
7. Rollback: `/operator-loop init --rollback <project>` — reverses all API calls and removes project YAML.

## Operations subcommands

**`new`** — `/operator-loop new <project> "<hypothesis>"` — validates format ("We believe X for Y will achieve Z. Refuted if metric < threshold over window"), creates Hypothesis ticket, branch, design frame, feature flag, analytics widget.

**`advance`** — `/operator-loop advance <project> <id>` — validates stage evidence, invokes appropriate agent for next stage, updates tracker, posts to notifications.

Stage agents: Hypothesis→Prototype (design MCP + Codex spike) | Prototype→Spec (Codex from prototype + the architecture model: the capability the hypothesis moves, its use cases, commands and invariants) | Spec→Agent Run (Codex: PR, tests, analytics, eval harness) | Agent Run→Review (auto on CI green + takeover check) | Review→Measure (on approved merge: enable flag, start window) | Measure→Verdict (on window close: pull analytics, draft verdict).

**`status`** — table: hypothesis ID, title, stage, owner, cost-to-date, active takeover triggers, time-in-stage.

**`triggers`** — evaluates all 12 takeover triggers; shows clear / grey-zone / fired per trigger.

**`takeover`** — labels ticket, revokes agent write on PR, sends notification. Requires `takeover release` to resume.

**`verdict`** — `/operator-loop verdict <project> <id> <confirmed|refuted|inconclusive|iterate|kill> --notes "..."` — validates measurement window closed, writes verdict, emits analytics event, archives (kill) or creates child (iterate), closes ticket.

**`kill-switch`** — turns off feature flag immediately regardless of stage. Verdict still required afterwards.

## Architecture model

The product repo carries an arch3-lite model at `docs/architecture/model.jsonl`: capabilities, use cases, commands and invariants, each cited to the code it was read from. Trust it in proportion to its `code_evidence` (the share of elements read from code; near 0.00 means it was built from folder names). Two stages read it:

- **Spec** starts from the capability the hypothesis moves. An invariant of that capability with `enforcement: unenforced` is a known hole: the spec closes it or names it as shipped.
- **Review** maps every changed line of the PR to capabilities — the element citing that line, else the enclosing function, else the code reading a changed config key at the PR revision, else the file — and compares them with the capabilities of the spec's component paths.

## Transition gates

| Transition | Required evidence |
|---|---|
| → Prototype | Hypothesis Statement, Signal Links, Target Segment |
| → Spec | Prototype Link, Code Constraint Notes |
| → Agent Run | Spec Link, Success Metric, Acceptance Criteria, Agent Scope (the spec's component paths — what scope drift is measured against), Risk Level |
| → Review | PR URL, CI green, evidence package |
| → Measure | Review approvals, analytics dashboard wired, flag in cohort |
| → Verdict | Measurement window elapsed, analysis written |
| → Closed | Verdict, Decision Notes, follow-up link if Iterate |

## Takeover triggers (12; all fire automatically except scope drift, which advises until measured)

auth/payments/security surface · data migration · new external dependency · CI red · eval regression · cost guardrail breach · PR complexity cap · performance risk · tool permission change · agent can't explain diff · invalid analytics wiring · scope drift

**Scope drift** is computed from the architecture model, not judged. A changed line reaching a capability the spec does not declare is drift. An undeclared file reaching four or more capabilities (cross-cutting) or a component that realizes no use case (platform wiring) is an advisory. A changed code file the model cannot place means the model is stale — rescan. It is computed next to the code — in the product repo's CI, as S5D review evidence — not on the operator host; the loop relays it once per PR head to the task thread and keeps it advisory until its hits on live PRs are labelled.

## Safety

Skill never merges PRs, touches secrets outside `operator-loop/<project>/*`, writes to primary branch, disables takeover triggers, or claims `verdict: confirmed` without elapsed window and analytics data. No irreversible bulk actions without explicit confirmation.
