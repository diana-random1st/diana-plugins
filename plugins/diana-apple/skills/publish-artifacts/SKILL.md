---
name: publish-artifacts
description: "Publish files to S3 bucket with CloudFront invalidation. Use when user wants to deploy, publish, or upload artifacts (HTML, images, files) to the web. Triggers: 'publish', 'deploy to s3', 'upload artifact', 'cdn invalidation'."
allowed-tools:
  - "Bash(aws:*)"
---

# Publish Artifacts

Upload files to Roman's personal site bucket and invalidate the CloudFront cache.
Publishing is an external action: get Roman's explicit OK for each publish.

## Target: random1st.click (personal)

```bash
export AWS_PROFILE=random1st BUCKET=random1st.click DISTRIBUTION_ID=E1FWJFFMXKIDEB
```

Public URL = `https://random1st.click/<destination>`.

**Work content does not go here.** Pregmate/Quandex internal pages are published as Cloudflare
Workers Static Assets behind Cloudflare Access (Quandex people): Terraform in
`~/src/pm/pregmate-infra/cloudflare/` (e.g. `support_guide.tf`), worked example with deploy and
verification steps in `~/Customer-Support-Overview/publish/README.md`.

## Workflow

```bash
# 1. Upload (Content-Type is guessed from the extension; pass --content-type only to override)
aws s3 cp <local-file> "s3://$BUCKET/<destination>"
#    directory: aws s3 sync <dir> "s3://$BUCKET/<prefix>/"   (add --delete only for a prefix you own:
#    it removes remote files missing locally)

# 2. Invalidate the changed paths ("/*" only when many files changed)
aws cloudfront create-invalidation --distribution-id "$DISTRIBUTION_ID" --paths "/<destination>"

# 3. Verify, then return the URL
aws cloudfront get-invalidation --distribution-id "$DISTRIBUTION_ID" --id <invalidation-id> --query Invalidation.Status
python3 -c "import urllib.request as u;print(u.urlopen(u.Request('https://random1st.click/<destination>',method='HEAD'),timeout=15).status)"
```

Use descriptive destination paths (`demos/2026/chart.html`, not `file1.html`). Flags:
[aws s3 cp](https://docs.aws.amazon.com/cli/latest/reference/s3/cp.html) ·
invalidation behaviour and pricing: [CloudFront invalidation](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Invalidation.html).
