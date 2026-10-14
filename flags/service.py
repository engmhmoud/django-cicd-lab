"""Server-side flag evaluation: stable per subject, cheap, and instantly reversible."""

import hashlib
import time

from .models import Flag
from .registry import FLAGS

CACHE_SECONDS = 1.0  # how stale a replica's view of a flag can be; a kill switch takes effect within this
_cache: dict[str, tuple[float, bool, int]] = {}


def bucket(flag_name, subject):
    """0-99, the same for the same flag and subject on every replica and every request."""
    digest = hashlib.sha256(f"{flag_name}:{subject}".encode()).hexdigest()
    return int(digest[:8], 16) % 100


def _state(flag_name):
    now = time.monotonic()
    cached = _cache.get(flag_name)
    if cached and now - cached[0] < CACHE_SECONDS:
        return cached[1], cached[2]
    row = Flag.objects.filter(name=flag_name).values_list("enabled", "percent").first()
    enabled, percent = row if row else (False, 0)  # unknown or missing flag: off (fail closed)
    _cache[flag_name] = (now, enabled, percent)
    return enabled, percent


def is_enabled(flag_name, subject):
    if flag_name not in FLAGS:
        raise KeyError(f"unregistered flag {flag_name!r}: add it to flags/registry.py")
    enabled, percent = _state(flag_name)
    return enabled and bucket(flag_name, subject) < percent
