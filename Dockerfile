# syntax=docker/dockerfile:1
# Multi-stage, non-root image for the orders service (see learning/005 ch03-ch04 for the why).

FROM python:3.14.8-slim-trixie AS build
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1
RUN python -m venv /venv
COPY requirements.lock /tmp/requirements.lock
# Hash-checked install of the full lock (learning/013 ch04): a changed or swapped file fails the build.
# pip is removed afterwards: the runtime never installs anything, and pip's vendored packages
# (urllib3, msgpack, setuptools) were the only HIGH findings Trivy reported (Lab 4).
RUN /venv/bin/pip install --require-hashes --no-deps -r /tmp/requirements.lock \
 && /venv/bin/pip uninstall --yes pip

FROM python:3.14.8-slim-trixie AS runtime
ARG APP_VERSION=dev
ARG GIT_SHA=unknown
ENV PATH=/venv/bin:$PATH PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    APP_VERSION=$APP_VERSION GIT_SHA=$GIT_SHA
RUN python -m pip uninstall --yes pip \
 && useradd --uid 10001 --create-home app
COPY --from=build /venv /venv
WORKDIR /app
COPY --chown=app:app . .
USER app
EXPOSE 8000
HEALTHCHECK --interval=5s --timeout=3s --retries=5 \
  CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2).status == 200 else 1)"]
# exec form: gunicorn is PID 1 and gets SIGTERM directly (graceful shutdown, 005 ch04)
CMD ["gunicorn", "config.wsgi", "--bind", "127.0.0.1:8000", "--workers", "2", "--graceful-timeout", "20", "--access-logfile", "-"]
