---
name: diana-deploy
description: Pre-deploy gate and post-deploy watch — route to the project's own deploy skill, CI green on the exact SHA, secrets and dependency audit, migration check, explicit permission, then watch the run and the health. Use before deploying to staging or production. Triggers on 'deploy', 'pre-deploy check', 'deploy readiness'.
---

# Diana Deploy Checklist

1. **Route first.** A project deploy procedure beats this checklist:
   - repo-local skill: `ls .claude/skills` (Pregmate API: `release`, production only from a released tag; `prod-health` after);
   - Diana skills: `apple-release` (iOS), `hapt-play-upload` / `ship-both` (Hapt), `operator-host`, `publish-artifacts` (S3), `cws-publish`, `litellm-access`;
   - otherwise `recall` "<project> canonical deploy" in Hindsight (`bank_id: diana`); the CI traps live there.

2. **Ref.** `git fetch && git status -sb`: clean, up to date, on a ref the deploy workflow accepts.

3. **CI green on this exact SHA.** Every check completed with `success` or `skipped`; "the run finished" is not enough:
   ```bash
   gh run list --commit "$(git rev-parse HEAD)" --json name,status,conclusion,url
   ```
   Build and test locally only what CI does not cover.

4. **Security.** `<deployed>` = the SHA now running (image tag, last release tag):
   ```bash
   gitleaks git --log-opts="<deployed>..HEAD" --redact --no-banner
   cargo audit  |  uv audit --frozen  |  bun audit      # whichever stack applies
   ```

5. **Migrations and config.** `git diff --stat <deployed>..HEAD` and look for migrations, Helm values, env or config changes, breaking API changes.

6. **Report.** `READY TO DEPLOY` with ref + SHA, CI run URL, audit result, migrations; or `NOT READY` with the blockers.

7. **Permission.** Ask Roman explicitly before every deploy command, per deploy, per session.

8. **Watch, then verify.** No hand-written sleep/poll loops:
   ```bash
   gh run watch <run-id> --exit-status --compact -i 30
   gh run view <run-id> --log-failed        # on failure
   ```
   Then check the running thing: pods ready and on the new image, the health URL, or the repo's health skill.
