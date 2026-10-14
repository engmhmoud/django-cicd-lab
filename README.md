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
pip install --require-hashes -r requirements-dev.lock   # hashed; the same runtime pins as the image
python manage.py test --parallel auto --shuffle
```

Changing a dependency: edit `requirements.txt` (runtime) or `requirements-dev.txt` (tools), then regenerate both locks
(`requirements.lock` first, then `requirements-dev.lock` with `-c requirements.lock`; the commands are in the file headers).
CI fails if the dev lock's runtime pins drift from `requirements.lock`.

Rules for this repo: work on a branch, open a PR, CI must be green, squash-merge. `main` is protected by a ruleset.
Lab code only: no secrets live here.

## Running the tests

`python manage.py test --parallel auto --shuffle` (needs a Postgres; CI uses a `postgres:18.6` service container).
