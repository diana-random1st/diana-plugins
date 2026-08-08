# App Store provider and policy boundaries

## App Store Connect API key roles

- Developer-role keys can deliver builds, but may be forbidden from metadata,
  tester, compliance, and review-submission operations.
- App Manager is the normal automation role for metadata and review submission.
- The role is immutable after key creation; recreate the key when the role is
  wrong rather than trying alternate undocumented endpoints.
- Store the `.p8`, key ID, and issuer ID through the established secret boundary.
  Never retrieve or print them interactively.

## App Privacy

The App Privacy data-usage questionnaire is a legal attestation and must remain
human-confirmed. In the verified 2026 workflow, the historical
`appDataUsages`, `appDataUsagesPublishState`, and `appDataUsageCategories`
relationships returned PATH_ERROR because Apple removed them from the public
REST surface. Do not interpret that as an API-role problem or retry with broader
credentials.

Use App Store Connect -> App Privacy to declare each collected type, purpose,
linked-to-user state, and tracking state, then publish. Derive answers from the
actual app and SDK behavior; examples from another app are not reusable facts.

## Firebase social sign-in

For a standard non-GCIP Firebase Auth project, enabling Apple or Google providers
may be Console-only. Do not migrate to Identity Platform merely to automate the
toggle: migration changes billing and is not reversible. Surface that tradeoff
for an explicit architecture decision.

For native Sign in with Apple, web Services ID and return-URL fields may be
irrelevant; verify the actual platform configuration before adding them.
