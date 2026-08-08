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

1. Discover the project's documented release command, signing settings, app identity, and current version before changing anything.
2. Never run `diana system vault get`, print credentials, or build secret JSON interactively; secrets may enter only through an existing secure script/environment boundary.
3. Confirm irreversible identifiers and the next build number before archive or upload.
4. Run the project's tests and archive validation before delivery.
5. Verify the processed build and directly attached App Store build; upload success alone is not release success.
6. Treat App Privacy answers and other legal attestations as human-owned confirmations.
7. Report each stage as PASS, FAIL, or UNKNOWN with the observed App Store state and remaining blockers.
