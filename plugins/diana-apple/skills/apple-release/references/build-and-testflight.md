# Build and TestFlight delivery

## Contents

- [Preflight](#preflight)
- [Native Xcode pipeline](#native-xcode-pipeline)
- [Flutter pipeline](#flutter-pipeline)
- [Credential boundary](#credential-boundary)
- [Upload and verification](#upload-and-verification)
- [Common failures](#common-failures)

## Preflight

Use the project's documented release command when it exists. Read the project,
scheme, target, bundle identifier, deployment target, signing team, version, and
build number from source and build settings; do not copy identifiers from an
unrelated app or prior session.

Verify before archiving:

- tests and static checks required by the project pass;
- the next build number is greater than every delivered build for this version;
- `ASSETCATALOG_COMPILER_APPICON_NAME` points at the real AppIcon set;
- `INFOPLIST_KEY_ITSAppUsesNonExemptEncryption` reflects the app's actual crypto use;
- `CODE_SIGN_ENTITLEMENTS` names the target's entitlements when present;
- the Distribution team and required capabilities match the App ID;
- the App Store Connect API key role matches the lifecycle stage.

`-allowProvisioningUpdates` may create or refresh managed profiles and register
supported App ID capabilities. That is an external Apple-side effect; keep it in
the canonical release command and report it.

## Native Xcode pipeline

Use project-derived values, not the placeholders below:

```bash
xcodebuild \
  -scheme <SCHEME> \
  -archivePath /tmp/<APP>.xcarchive \
  clean archive \
  -destination 'generic/platform=iOS' \
  -allowProvisioningUpdates \
  DEVELOPMENT_TEAM=<TEAM_ID> \
  ASSETCATALOG_COMPILER_APPICON_NAME=AppIcon \
  CURRENT_PROJECT_VERSION=<BUILD> \
  MARKETING_VERSION=<VERSION>
```

Inspect the archive before export:

```bash
plutil -p /tmp/<APP>.xcarchive/Info.plist
codesign -d --entitlements :- /tmp/<APP>.xcarchive/Products/Applications/*.app
```

Create an export-options plist through the repository's file-editing mechanism,
with `method=app-store-connect`, `signingStyle=automatic`, and the verified team.
Then export:

```bash
xcodebuild -exportArchive \
  -archivePath /tmp/<APP>.xcarchive \
  -exportOptionsPlist <EXPORT_OPTIONS_PLIST> \
  -exportPath /tmp/<APP>-export \
  -allowProvisioningUpdates
```

Confirm exactly one expected IPA exists and inspect its embedded identity before
delivery.

## Flutter pipeline

Read the current `version:` value from `pubspec.yaml` and compare its `+BUILD`
suffix with App Store Connect. Change only the build component unless the user
also requested a marketing-version change.

```bash
grep '^version:' pubspec.yaml
flutter test
flutter build ipa --release
ls -la build/ios/ipa/*.ipa
```

`flutter build ipa` normally creates both
`build/ios/archive/Runner.xcarchive` and `build/ios/ipa/*.ipa`. Verify both; do
not infer success from the final log line alone.

If the project has a Fastfile, prefer its documented lane. A generic delivery
shape is:

```bash
fastlane pilot upload \
  --ipa build/ios/ipa/<APP>.ipa \
  --api_key_path <SECURE_GENERATED_API_KEY_JSON> \
  --skip_waiting_for_build_processing
```

Do not hand-author the credential JSON in the terminal. An authorized project
script may create a short-lived file from its secret boundary, must set
`in_house: false` for normal App Store teams, must never print key material, and
must remove the file when finished.

## Credential boundary

- A Developer-role App Store Connect key can deliver a build but cannot perform
  many metadata, tester, compliance, or review-submission operations.
- An App Manager key is required for the automated production-listing path.
- API key roles cannot be changed after creation; revoke and recreate if the role
  is wrong.
- An APNs key is not an App Store Connect API key.
- Never revoke or replace another project's key merely because it belongs to the
  same Apple team.
- Never call `diana system vault get` interactively. Use the repository's secure
  release automation or stop with UNKNOWN if no authorized secret boundary exists.

Some Diana hosts block raw shell commands containing delivery keywords to force
skill routing. When the canonical command must live in a script, create the file
through the host's file-editing tool, review it, then execute the script. Do not
hide the command in a heredoc or weaken the hook.

## Upload and verification

Native delivery can use a reviewed script containing:

```bash
xcrun altool --upload-app \
  -f /tmp/<APP>-export/<APP>.ipa \
  -t ios \
  --apiKey "$APPSTORE_KEY_ID" \
  --apiIssuer "$APPSTORE_ISSUER_ID"
```

The environment variables above must already be populated by authorized secure
automation. The script must not retrieve or echo them.

Delivery success is only an intermediate state. Verify all of the following via
App Store Connect API, Fastlane Spaceship, or the authenticated UI:

- the expected version/build exists;
- `processingState=VALID` rather than Processing or Invalid;
- export-compliance state is resolved correctly;
- the intended internal testing state/tester group is active when requested;
- no unexpected signing, entitlement, or symbol warnings block distribution.

For a UI fallback, open the verified archive in Xcode Organizer and use
Distribute App -> App Store Connect -> Upload. UI fallback still requires the
same identity and processed-build verification.

## Common failures

| Symptom | Check |
| --- | --- |
| Bundle version must be higher | Compare the build number with the latest delivered build and increment it |
| `in_house` error | Ensure secure key JSON explicitly sets `in_house: false` for a public App Store team |
| Missing `CFBundleIconName` / validation 90713 | Confirm the AppIcon build setting on Release and archive cleanly |
| Distribution certificate permission error | Check team role and managed signing; do not create certificates blindly |
| Build uploaded but not selectable | Wait for processing and inspect compliance/test detail state |
| Empty/incorrect IPA glob | Stop; identify the exact exported IPA instead of uploading an arbitrary match |
| Auth 403 after successful uploads | Verify API key role; delivery capability does not imply metadata/review capability |
