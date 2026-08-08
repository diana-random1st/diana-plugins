---
name: apple-sign
description: "Sign and notarize macOS binaries with Developer ID certificate. Triggers: 'codesign', 'notarize', 'apple sign', 'staple'. NOT for: iOS code signing (use apple-release), general 'sign' without macOS context."
---

# Apple Code Signing & Notarization

Sign and notarize macOS binaries with Developer ID certificate.

## Quick Reference

Credential boundary:
+ Never call `diana system vault get` or print signing/notarization credentials.
+ Use the repository's approved release script or an already prepared secure
  environment for `APPLE_SIGNING_IDENTITY`, `APPLE_ID`, `APPLE_PASSWORD`,
  and `APPLE_TEAM_ID`.
+ Stop with UNKNOWN when no authorized credential boundary exists.

Keychain profile: `notarize-diana` (stored via `xcrun notarytool store-credentials`)

## Commands

### Sign a binary
```bash
: "${APPLE_SIGNING_IDENTITY:?secure signing environment is not prepared}"
codesign --force --sign "$APPLE_SIGNING_IDENTITY" --options runtime <binary>
```

### Sign + notarize a Tauri app
```bash
: "${APPLE_ID:?secure notarization environment is not prepared}"
: "${APPLE_PASSWORD:?secure notarization environment is not prepared}"
: "${APPLE_TEAM_ID:?secure notarization environment is not prepared}"
APPLE_ID="$APPLE_ID" APPLE_PASSWORD="$APPLE_PASSWORD" APPLE_TEAM_ID="$APPLE_TEAM_ID" \
  CMAKE_POLICY_VERSION_MINIMUM=3.5 bun run tauri build
```

### Notarize a standalone binary
```bash
: "${APPLE_SIGNING_IDENTITY:?secure signing environment is not prepared}"
# 1. Sign with hardened runtime
codesign --force --sign "$APPLE_SIGNING_IDENTITY" --options runtime <binary>

# 2. Zip for submission
zip /tmp/binary.zip <binary>

# 3. Submit for notarization
xcrun notarytool submit /tmp/binary.zip --keychain-profile "notarize-diana" --wait

# 4. Staple (only works on .app, .dmg, .pkg — not bare binaries)
# xcrun stapler staple <path.app>
```

### Verify signature
```bash
codesign -dvv <binary> 2>&1 | grep -E "Authority|TeamIdentifier"
spctl --assess --type exec <binary>  # Gatekeeper check (apps only)
```

## Tauri Config

In `tauri.conf.json` → `bundle.macOS`:
```json
{
  "signingIdentity": "Developer ID Application: <Your Name> (<TEAMID>)",
  "hardenedRuntime": true,
  "entitlements": "Entitlements.plist"
}
```

Notarization triggers automatically when `APPLE_ID`, `APPLE_PASSWORD`, and `APPLE_TEAM_ID` env vars are set during `tauri build`.

## Certificate Details

- **Type:** Developer ID Application (G2 Sub-CA)
- **Identity:** Developer ID Application: <Your Name> (<TEAMID>) —
  `security find-identity -v -p codesigning` lists yours
- **Expires:** 2031-02-12
- **Chain:** Developer ID Application → Developer ID Certification Authority → Apple Root CA

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| "The signature of the binary is invalid" | Certificate expired or not trusted | Check `security find-identity -v` for valid certs |
| Notarization rejected | Hardened runtime missing or forbidden entitlements | Ensure `--options runtime` flag; review entitlements |
| "No identity found" | Developer ID cert not in keychain | Import via Keychain Access or `security import` |
| Stapling fails on binary | Only .app/.dmg/.pkg can be stapled | For bare binaries, notarize only (stapling not supported) |
