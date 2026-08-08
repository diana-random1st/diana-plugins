# App Store release preflight

Run every relevant check sequentially and report evidence as PASS, FAIL, or
UNKNOWN. UNKNOWN is not READY.

## 1. Identity and source state

- Confirm repository, target, bundle identifier, App Store app ID, scheme, team,
  marketing version, and expected build number from current source/configuration.
- Confirm the release diff and user-owned changes are committed or explicitly
  acknowledged before any destructive cleanup or external delivery.
- Run the project's canonical tests, lint, and release build checks.

## 2. Processed build

- Confirm the expected build exists in TestFlight.
- Confirm processing completed and compliance is resolved.
- Confirm the build number and bundle identifier match the archive just produced.
- Confirm required entitlements/capabilities exist in the signed app.
- Confirm the build is selectable for the intended App Store version.

Use an authenticated API/UI session already configured through secure automation.
Do not retrieve or print vault secrets as part of the check.

## 3. Metadata

- App name and subtitle where applicable.
- Description and keywords.
- Support URL; marketing URL if used.
- What's New for an update.
- Privacy-policy URL where required.
- Copyright and content-rights declaration.
- Primary category and any secondary category.

## 4. Screenshots and device support

- At least one valid screenshot for every required display family.
- Current accepted App Store Connect dimensions, confirmed in the live UI/API.
- iPad screenshots when the submitted binary supports iPad.
- Screenshots show current UI, contain no debug/private data, and match metadata.
- Localized screenshots and metadata are complete for every locale being submitted.

Do not stretch a screenshot merely to hit dimensions when it would misrepresent
the UI. Prefer capture from a matching simulator/device and inspect the result.

## 5. Rating, pricing, availability, privacy

- Expanded age-rating questionnaire is complete.
- Pricing schedule and base territory are correct.
- Availability regions are set.
- App Privacy labels match actual SDK/data behavior.
- Tracking, linked-to-user, and purpose answers are human-confirmed legal claims.
- Export compliance reflects actual encryption behavior.

## 6. Product and review blockers

Check the relevant Apple review risks:

| Area | Evidence |
| --- | --- |
| Performance | Launch and critical paths do not crash or hang |
| Accurate metadata | Store text/screenshots match the binary |
| In-app purchase | Digital goods use the approved StoreKit path |
| Design | No placeholders, broken layouts, or inaccessible primary actions |
| Minimum functionality | Product is more than a thin website wrapper |
| Data collection/use | Privacy labels and privacy policy match runtime behavior |
| Account deletion | Required deletion path exists when accounts are created |

For a resubmission, read every Resolution Center point, map each to a concrete
fix and regression check, and prepare a concise reviewer reply.

## 7. Submission state

- The intended build is attached to the version using the direct relationship
  endpoint or visible UI state.
- No stale review submission is holding the wrong build.
- All yellow/red App Store Connect banners are resolved or explained.
- The current state permits `Add for Review` / reviewSubmissions submission.

## Output

```text
APPLE RELEASE PREFLIGHT - <App> <version> (<build>)

PASS Identity: <evidence>
PASS Build: processed and selectable
FAIL Screenshots: <missing display family>
UNKNOWN Privacy: human attestation not yet published
PASS Binary: distribution signed, expected entitlements

VERDICT: READY | READY WITH WARNINGS | NOT READY
BLOCKERS: [...]
WARNINGS: [...]
NEXT ACTION: [...]
```

Only READY may proceed automatically to the review-submission stage. READY WITH
WARNINGS requires an explicit judgment that every warning is non-blocking.
