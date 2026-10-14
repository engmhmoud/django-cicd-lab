"""Settings for the 013 lab service. Everything comes from the environment (12-factor)."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def env(name, default=None):
    return os.environ.get(name, default)


SECRET_KEY = env("DJANGO_SECRET_KEY", "lab-only-not-a-secret")  # lab-only default, never used in production
DEBUG = env("DJANGO_DEBUG", "0") == "1"
ALLOWED_HOSTS = [h for h in env("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,app,edge").split(",") if h]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "orders",
    "flags",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", "app"),
        "USER": env("POSTGRES_USER", "app"),
        "PASSWORD": env("POSTGRES_PASSWORD", "app"),
        "HOST": env("POSTGRES_HOST", "localhost"),
        "PORT": env("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": 60,
        "CONN_HEALTH_CHECKS": True,
        "OPTIONS": {"connect_timeout": 3},
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
TIME_ZONE = "UTC"

# What the /version endpoint reports. Baked into the image at build time (Dockerfile ARGs).
APP_VERSION = env("APP_VERSION", "dev")
GIT_SHA = env("GIT_SHA", "unknown")

# Readiness: the app reports "not ready" while this file exists (used to drain before shutdown).
DRAIN_FILE = env("DRAIN_FILE", "/tmp/draining")  # noqa: S108 (a flag file, not data)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", "INFO")},
}
