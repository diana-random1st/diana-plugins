---
name: django-pro
description: Use for Django 5.x work that needs architecture, ORM, async, API, security, testing, performance, or deployment guidance.
---

# Django Pro

Start here when the task is primarily Django.

Workflow:
1. Inspect the project first: Django version, settings layout, installed apps, current models/views/serializers/tasks, and whether the codebase is sync, async, or mixed.
2. Choose the narrowest route in [references/guide.md](./references/guide.md): architecture, ORM, async, DRF, Channels, Celery, security, testing, performance, or deployment.
3. Prefer Django's built-in capabilities before adding third-party packages or cross-cutting patterns.
4. Follow the existing project structure instead of imposing a fresh architecture before reading what is already there.
5. Add or update tests alongside behavior changes, especially for queries, permissions, async flows, and background work.
6. Before presenting, run the relevant checks such as `python manage.py check`, targeted tests, and `ruff check`.
