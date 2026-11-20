---
name: django-pro
description: Use for Django work (Pregmate API runs Django 6.1 + DRF) that needs architecture, ORM, async, API, security, testing, performance, or deployment guidance.
---

# Django Pro

1. **Inspect first.** Django version (`pyproject.toml`), settings layout, installed apps, sync/async mix. Follow the existing structure; prefer Django built-ins over new packages.
2. **Read the repo rules.** The repo's CLAUDE.md / AGENTS.md win over general advice.
3. **Primary sources** for the version in use (`stable` resolves to the current release):
   - docs https://docs.djangoproject.com/en/stable/, release notes https://docs.djangoproject.com/en/stable/releases/
   - ORM performance https://docs.djangoproject.com/en/stable/topics/db/optimization/
   - async https://docs.djangoproject.com/en/stable/topics/async/
   - security https://docs.djangoproject.com/en/stable/topics/security/, deploy checklist https://docs.djangoproject.com/en/stable/howto/deployment/checklist/
   - DRF https://www.django-rest-framework.org/
4. **Tests with the change**, especially queries, permissions, async flows and Celery tasks. Before presenting: `python manage.py check`, targeted tests, `ruff check`.

## Pregmate API (`~/src/pm/pregmate-api`, Django code in `src/`)

- Public HTTP contract is frozen (serializer fields, URLs, status codes) unless Roman asks explicitly; see `CLAUDE.md`.
- Tests on macOS go through the Makefile, which exports `DYLD_FALLBACK_LIBRARY_PATH` for WeasyPrint; plain `uv run pytest` fails the PDF tests:
  ```bash
  cd src && uv run --no-sync make test PYTEST='pytest tests/ --ignore=tests/e2e --tb=short -q'
  make lint   # ruff + mypy + ty
  ```
- Reproduce against dev read-only: `kubectl -n dev exec deploy/api-sync -- python -c '…'` (settings module `settings`; call `django.setup()` first).
- Deploy → the repo's `release` skill, not by hand.
