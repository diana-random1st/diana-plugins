# Django guide

Use this guide after you have identified the project's version and current structure.

## Core stance

- Prefer Django-idiomatic solutions and built-in primitives first.
- Keep business logic testable and out of large views or serializers.
- Treat database behavior, security, and observability as part of correctness.

## Project structure and architecture

Reach for this section when designing or refactoring modules.

- Keep apps modular and aligned with existing domain boundaries.
- Use settings split by environment when the project already has that pattern or the task needs it.
- Add a service layer or repository-style helper only when it clarifies business logic or external integrations.
- Keep admin, forms, serializers, tasks, and views thin; let models, services, and query helpers hold reusable rules.

## Models, ORM, and database work

Use this section for schema, querying, and migrations.

- Model relationships, constraints, and indexes should match the real access pattern.
- Use `select_related`, `prefetch_related`, annotations, and custom querysets before considering raw SQL.
- Reach for PostgreSQL-native types and functions when the project already depends on PostgreSQL and they simplify the model.
- For data migrations, plan rollback safety and batch size before touching production-shaped data.
- Use transactions for multi-step writes that must commit atomically.

## Views, APIs, and interfaces

- Choose CBVs or FBVs based on local convention; do not mix styles gratuitously.
- For APIs, use DRF serializers, permissions, throttles, and validation rather than ad hoc request parsing.
- Keep response contracts explicit and test them.
- When GraphQL is already present, follow the existing stack such as Strawberry or Graphene instead of introducing a new one.

## Async, Channels, and background work

- Use async views or middleware only where the dependency chain is actually async-safe.
- For WebSockets and real-time features, keep Channels responsibilities narrow and state transitions explicit.
- For long-running or retryable work, push it to Celery and make retries idempotent.
- Document the queue, broker, timeout, and retry expectations in code or tests when behavior depends on them.

## Security and authentication

- Keep Django security middleware enabled unless the project has a verified reason not to.
- Preserve CSRF, XSS, and permission boundaries when changing forms or APIs.
- Prefer first-party auth flows and hardened libraries over custom token handling.
- Treat object-level authorization and multitenant filtering as first-class concerns, not optional polish.

## Testing and quality

- Add tests for the changed behavior, not just the happy path.
- Use `pytest-django`, factories, and focused fixtures to keep tests readable.
- For queryset or permission changes, test both correctness and the expected failure modes.
- Run `python manage.py check`, targeted tests, and linting before calling the task done.

## Performance and operations

- Measure query count and shape when touching list views, dashboards, or feeds.
- Use caching only when you can define invalidation and ownership.
- Keep static/media handling, storage backends, and deployment settings environment-aware.
- When shipping async or background features, verify worker/runtime configuration, not just code paths.

## Integrations

This section covers common external dependencies.

- Payments, email, SMS, storage, search, and monitoring integrations should be wrapped behind clear adapters or service helpers.
- Log failures with actionable context and without leaking secrets.
- Keep provider-specific code isolated so the rest of the project can stay framework-first.

## Response pattern

When giving Django guidance or code:
- explain the Django-specific constraint first
- suggest the smallest idiomatic change
- mention test coverage or migration impact
- call out security or performance consequences when they matter
