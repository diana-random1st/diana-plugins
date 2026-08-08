# App Store metadata and review submission

## Contents

- [Prerequisites](#prerequisites)
- [Metadata and screenshots](#metadata-and-screenshots)
- [API-writable fields](#api-writable-fields)
- [Review submission flow](#review-submission-flow)
- [Swap a build already in review](#swap-a-build-already-in-review)
- [Authenticated UI fallback](#authenticated-ui-fallback)

## Prerequisites

Start only after `preflight.md` identifies the correct app/version and a
processed selectable build. App Manager credentials are required for automated
metadata and review operations. App Privacy remains a human-confirmed UI step;
see `provider-notes.md`.

Required production-listing state normally includes:

- description, keywords, promotional text and support URL;
- What's New for updates;
- screenshots for every required display family;
- category, content rights, age rating, pricing and availability;
- privacy answers and policy URL when required;
- the correct build attached directly to the App Store version.

## Metadata and screenshots

With Fastlane Spaceship/ConnectAPI, select the app and editable version, then
update the intended locale. Treat field names as API-version-sensitive and read
back each mutation.

Screenshot capture should use a matching simulator/device family. A typical
native flow is build for the simulator, install, launch, navigate deterministically,
then use `simctl io <UDID> screenshot`. Use XCUITest or a snapshot lane for
multi-screen sets. Inspect every image for clipping, stale UI, private data, and
the live App Store dimension requirement.

## API-writable fields

The verified App Manager path can write most version fields. Prefer supported
library methods; use raw REST only where the library lacks a wrapper.

### Localization

Select the editable version/localization and update attributes such as
`description`, `keywords`, and `promotionalText`. Read the localization back;
an HTTP success without the intended value is insufficient.

### Category

The verified Spaceship key is snake case with `_id`:

```ruby
info = app.fetch_edit_app_info
info.update_categories(
  category_id_map: { primary_category_id: "HEALTH_AND_FITNESS" }
)
raise "category mismatch" unless \
  app.fetch_edit_app_info.primary_category.id == "HEALTH_AND_FITNESS"
```

Do not use a remembered category from another app.

### Age rating

The raw REST update is `PATCH /v1/ageRatingDeclarations/{id}`. A GET may be
forbidden even when PATCH is allowed, so send a complete payload derived from
the current questionnaire instead of read/merge. The expanded questionnaire has
required enum and boolean fields; a 409 lists omissions. Do not convert that
response into guesses about the app's content.

Common enum fields include content/violence/gambling themes and
`ageRatingOverride`; common booleans include gambling, unrestricted web access,
loot boxes, user-generated content, wellness topics, parental controls,
advertising, age assurance, and messaging/chat. `kidsAgeBand` may be null.
Names change across API versions: validate against the current response/schema.

### Free pricing

Where Spaceship exposes only getters, raw REST can create an app price schedule:

1. Query app price points for the intended base territory.
2. Select the point whose `customerPrice` is exactly `0.0`.
3. `POST /v1/appPriceSchedules` with relationships to app, base territory,
   manual price, and the chosen app price point.
4. Read the app price schedule and included point back; confirm price and territory.

Never assume the first point is free without checking `customerPrice`.

## Review submission flow

The legacy `POST /v1/appStoreVersionSubmissions` creation path is not the
canonical submit operation. Use review submissions:

1. Find or create an open `reviewSubmissions` resource for platform `IOS` and app.
2. Create a `reviewSubmissionItems` relationship to the intended App Store version.
3. Patch the review submission with `submitted: true`.
4. Verify both review submission and version reach `WAITING_FOR_REVIEW`.

Do not report success from the POST/PATCH alone. Read back the final state and
the directly attached build.

## Swap a build already in review

For a last-minute replacement on a version already waiting for review:

1. Fetch the per-version `appStoreVersionSubmission` relationship.
2. Delete that submission; expect HTTP 204 and the version to become
   `DEVELOPER_REJECTED` with its selected build cleared.
3. Attach the new processed build by patching the version's build relationship.
4. If Apple returns transient 409 `INVALID_STATE`, wait for the version state to
   settle and retry with a bounded interval; do not switch endpoints blindly.
5. Resubmit through `reviewSubmissions` and verify `WAITING_FOR_REVIEW`.

Always verify the build through
`GET /v1/appStoreVersions/{version_id}/build`. A list request with
`include=build` can omit an attached relationship and is not authoritative for
this check.

## Authenticated UI fallback

Use an already authenticated App Store Connect browser session when a field is
not supported by current API/tooling or for the human privacy attestation.

1. Navigate to the verified app/version URL and capture a DOM snapshot.
2. Inspect current warnings and state before every consequential action.
3. Upload screenshots to the matching device-family drop zone.
4. Fill metadata; App Store Connect may use contenteditable elements rather than
   ordinary inputs.
5. Save draft frequently and snapshot again to confirm persisted values.
6. Complete age/content/privacy attestations with the human's confirmed answers.
7. Select the verified processed build.
8. Add for Review, submit, and wait for `Waiting for Review`.

For a contenteditable field that ignores normal typing, set its text through the
browser evaluation API and dispatch a bubbling `input` event, then read the
rendered value back. Do not execute arbitrary page scripts beyond the focused
field mutation.

Common blockers:

| Blocker | Resolution |
| --- | --- |
| Required display screenshots missing | Capture/upload the live required family and verify dimensions |
| iPad screenshots requested | Confirm binary device support, then supply the required iPad set |
| Build not selectable | Wait for processing/compliance or identify a bundle/version mismatch |
| Content rights incomplete | Declare actual ownership/licensing state |
| Age/privacy incomplete | Complete every human-confirmed question and publish where required |
| Price/availability missing | Set and read back the intended schedule/territories |
| contenteditable did not persist | Use focused input-event evaluation, Save, and snapshot/read back |
