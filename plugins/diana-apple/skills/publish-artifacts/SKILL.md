---
name: publish-artifacts
description: "Publish files to S3 bucket with CloudFront invalidation. Use when user wants to deploy, publish, or upload artifacts (HTML, images, files) to the web. Triggers: 'publish', 'deploy to s3', 'upload artifact', 'cdn invalidation'."
allowed-tools:
  - "Bash(aws:*)"
---

# Publish Artifacts

Deploy files to S3 bucket with automatic CloudFront CDN invalidation.

## Configuration

Set these before use:
- `BUCKET` — S3 bucket name
- `DISTRIBUTION_ID` — CloudFront distribution ID
- `AWS_PROFILE` — AWS CLI profile name

## When to Use

- Publishing HTML artifacts/pages to the web
- Uploading images or assets
- Deploying static files
- Making files publicly accessible via CDN

## How to Use

### Trigger Phrases

- "publish to $BUCKET"
- "upload to s3"
- "deploy artifact"
- `/publish <file-path> [destination-path]`

### Examples

```
Publish index.html to the root
```

```
Upload build/output.html as demo.html
```

```
Deploy the artifact at /tmp/chart.png to images/chart.png
```

## Workflow

1. **Upload to S3**:
   ```bash
   AWS_PROFILE=$AWS_PROFILE aws s3 cp <local-file> s3://$BUCKET/<destination> \
     --content-type <mime-type>
   ```

2. **Invalidate CloudFront Cache**:
   ```bash
   AWS_PROFILE=$AWS_PROFILE aws cloudfront create-invalidation \
     --distribution-id $DISTRIBUTION_ID \
     --paths "/<destination>"
   ```

3. **Return Public URL**:
   ```
   https://$BUCKET/<destination>
   ```

## Content Types

Automatically detect and set appropriate Content-Type:
- `.html` → `text/html`
- `.css` → `text/css`
- `.js` → `application/javascript`
- `.json` → `application/json`
- `.png` → `image/png`
- `.jpg/.jpeg` → `image/jpeg`
- `.gif` → `image/gif`
- `.svg` → `image/svg+xml`
- `.pdf` → `application/pdf`
- `.webp` → `image/webp`

## Commands Reference

### Upload Single File
```bash
AWS_PROFILE=$AWS_PROFILE aws s3 cp <file> s3://$BUCKET/<path> --content-type <type>
```

### Upload Directory
```bash
AWS_PROFILE=$AWS_PROFILE aws s3 sync <dir> s3://$BUCKET/<path>/ --delete
```

### Invalidate Specific Path
```bash
AWS_PROFILE=$AWS_PROFILE aws cloudfront create-invalidation \
  --distribution-id $DISTRIBUTION_ID \
  --paths "/<path>"
```

### Invalidate All (use sparingly)
```bash
AWS_PROFILE=$AWS_PROFILE aws cloudfront create-invalidation \
  --distribution-id $DISTRIBUTION_ID \
  --paths "/*"
```

### List Bucket Contents
```bash
AWS_PROFILE=$AWS_PROFILE aws s3 ls s3://$BUCKET/ --recursive
```

### Check Invalidation Status
```bash
AWS_PROFILE=$AWS_PROFILE aws cloudfront get-invalidation \
  --distribution-id $DISTRIBUTION_ID \
  --id <invalidation-id>
```

## Tips

- Use descriptive destination paths: `demos/2024/chart.html` not `file1.html`
- Set cache-control headers for long-lived assets
- Invalidations can take 1-2 minutes to propagate globally
- Each invalidation of paths >1000 costs $0.005 per path

## Example: random1st.click

- BUCKET: `random1st.click`
- DISTRIBUTION_ID: `E1FWJFFMXKIDEB`
- AWS_PROFILE: `random1st`
