"""Settings for the migration linter only (CI job `migrations` in lab03-tests.yml)."""

from .settings import *  # noqa: F403

INSTALLED_APPS = [*INSTALLED_APPS, "django_migration_linter"]  # noqa: F405
