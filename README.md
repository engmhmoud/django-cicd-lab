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
