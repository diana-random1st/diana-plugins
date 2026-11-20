---
name: apple-release
description: "Canonical iOS release lifecycle — native or Flutter build, signing, TestFlight delivery, preflight checks, App Store metadata, screenshots, review submission. Not macOS notarization; use apple-sign."
triggers: ["apple-release", "apple-publish", "apple-submit", "greenlight", "testflight", "publish ios", "ready to submit", "submit for review", "зарелизь в апстор"]
---

# Apple Release

Select the lifecycle stage from evidence in the current project and App Store
Connect; never assume a remembered app ID, bundle ID, scheme, or build number.

| Stage | Read |
| --- | --- |
| Native/Flutter build, archive, export, TestFlight | `references/build-and-testflight.md` |
| Readiness or rejection-fix check | `references/preflight.md` |
| Metadata, screenshots, build selection, review submission | `references/app-store-submission.md` |
| API roles, privacy boundary, Firebase provider caveat | `references/provider-notes.md` |

0. **Project skills first.** List the repository's skills in the branch being released (`.claude/skills/`, `.agents/skills/`, the `AGENTS.md` catalog) and use them in place of a home-grown procedure: release cut and version bump, merge back, PR review, QA handoff (Pregmate: `pma-ship`, `pma-merge-release`, `pma-review-pr`, `pma-qa-handoff`). Before a build that goes to TestFlight or review, read every review and thread on the PR it ships; an unanswered human blocker stops the release until it is fixed or Roman overrides it. (2026-11-12: Pregmate 1.13.7 (738) and the 1.14.1 plan were made without reading two human reviews that held a calendar freeze and a Watch data-loss window, and the release branch broke `pma-merge-release`'s three-version-line rule.)
1. Discover the project's documented release command, signing settings, app identity, and current version before changing anything. Pregmate iOS (`quandex/pregmate-mobile-app`) delivers through GitHub Actions: `Deploy Dev` (`dev.yml`), `QA Build` (`qa-build.yml`), `Deploy Release` (`release.yml`); lanes live in `fastlane/Fastfile` — list them with `gh api repos/quandex/pregmate-mobile-app/actions/workflows --jq '.workflows[]|[.id,.name,.path]|@tsv'`.
2. App Store Connect reads: `~/.diana/plugins/marketplaces/diana-plugins/plugins/diana-apple/skills/apple-release/scripts/asc.py --team pregmate|hapt get <path> [--fields a,b]` | `builds --app ID [--version X.Y.Z]` | `beta-groups --app ID` | `profiles --name S` (JSON; exit 1 = HTTP error, 2 = missing credential, named). It wraps the existing clients, which read credentials in-process (App Manager key → JWT) and never print them: Pregmate `~/.cache/asc/asc.py` (`call(method, path, body=None) -> (status, json)`, vault `appstore-{key-id,issuer-id,p8}-pregmate`); Roman's personal team (`--team hapt`: Hapt Touch 6759039802, Vacuum 6775836339, PageRelay 6791978091, TailMap 6752828909) `~/.appstoreconnect/asc_helper.py` (`api(method, path, body)`); its hard-coded `.p8` file is gone (2026-11-19), so asc.py signs with vault `appstore-{key-id,issuer-id,p8}` instead. The helper's `APP_ID` is Vacuum, not Hapt: always pass `--app`. Writes go through the same `call`/`api` in a script that prints only response fields. For another team, if no such client exists, write one — do not fall back to the ASC web UI because of the vault. Bare `vault get` in the terminal and hand-built secret JSON stay forbidden.
3. Confirm irreversible identifiers and the next build number before archive or upload.
4. Run the project's tests and archive validation before delivery.
5. Verify the processed build and directly attached App Store build; upload success alone is not release success.
6. Treat App Privacy answers and other legal attestations as human-owned confirmations.
6a. **Every submission is explained and consented to, any app.** Right before a submit (first submission, resubmission, build swap, and pressing Release): one message saying what is about to be sent — app, version, build and where it was built, What's New, screenshots added, review notes, flags/remote config state, QA's ok — then the explicit question "Submit X.Y.Z (build N) to App Review now? yes / no". Act only on a yes given in reply to that message. An earlier general go-ahead ("можно сабмитать", "забирай") is not consent; anything changed after the summary needs a new summary and a new question.
6b. **Pregmate: Stripe OFF for the version under review — never skip.** Before submitting, Firebase Remote Config (project `pregmate-8d25b`, group Payments) gets `stripe_payment_is_enabled = false` for a condition on that version only (`app.id == '1:1048988775829:ios:e1ab234a6fef6eaaadf29c' && app.version.==(['X.Y.Z'])`), published and read back; it stays off until approval, and turning it back on is Roman's call. Submitting is a separate explicit "yes" after showing Roman the summary (build, texts, notes, flags, Stripe state) — "можно сабмитать" earlier in the day is not that yes. (2026-11-13: 1.14.1 went to review with Stripe on for everyone, without QA's ok and without a final summary.)
7. Report each stage as PASS, FAIL, or UNKNOWN with the observed App Store state and remaining blockers.
