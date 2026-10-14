# django-cicd-lab

A small Django 6.1 "orders" service used by the **Git & CI/CD** labs (topic 013 of a system-design study guide).
It exists to be built, tested, scanned, signed and deployed by GitHub Actions; the code is deliberately small.

| Endpoint | Purpose |
|---|---|
| `GET /healthz` | liveness: the process answers (no database) |
| `GET /readyz` | readiness: 503 while draining or when Postgres is down |
| `GET /version` | the app version and git SHA baked into the image |
| `GET/POST /api/orders`, `GET /api/orders/<id>` | the tiny domain |

Run the tests locally (needs Postgres 18 reachable on `POSTGRES_HOST`):

```bash
pip install -r requirements-dev.txt
python manage.py test --parallel auto --shuffle
```

Rules for this repo: work on a branch, open a PR, CI must be green, squash-merge. `main` is protected by a ruleset.
Lab code only: no secrets live here.

## Running the tests

`python manage.py test --parallel auto --shuffle` (needs a Postgres; CI uses a `postgres:18.6` service container).

## CI concurrency

PR runs share a group per branch, so a new push cancels the old run. Pushes to `main` get one group per commit, so
every merged commit gets its own CI result: a shared group keeps only one *pending* run, and a burst of merges would
cancel the middle commit's run even with `cancel-in-progress: false`.
