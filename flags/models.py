from django.db import models


class Flag(models.Model):
    """Runtime state of a feature flag. Which flags exist (and who owns them) lives in registry.py."""

    name = models.SlugField(max_length=64, unique=True)
    enabled = models.BooleanField(default=False)  # the kill switch: False turns the flag off for everyone
    percent = models.PositiveSmallIntegerField(default=0)  # rollout: share of subjects (0-100) that get it
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} enabled={self.enabled} percent={self.percent}"
