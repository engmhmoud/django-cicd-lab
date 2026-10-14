import datetime as dt

from django.test import SimpleTestCase, TestCase

from . import service
from .models import Flag
from .registry import FLAGS


class BucketTests(SimpleTestCase):
    def test_same_subject_same_bucket(self):
        self.assertEqual(service.bucket("new_pricing", "c-42"), service.bucket("new_pricing", "c-42"))

    def test_buckets_spread_evenly(self):
        under_10 = sum(service.bucket("new_pricing", f"c-{i}") < 10 for i in range(10_000))
        self.assertAlmostEqual(under_10 / 10_000, 0.10, delta=0.02)


class EvaluationTests(TestCase):
    def setUp(self):
        service._cache.clear()

    def test_off_by_default(self):
        Flag.objects.update_or_create(name="new_pricing", defaults={"enabled": False, "percent": 100})
        self.assertFalse(service.is_enabled("new_pricing", "c-1"))

    def test_rollout_is_monotonic(self):
        """Everyone in the 10 % group stays in when the rollout grows to 50 %."""
        Flag.objects.update_or_create(name="new_pricing", defaults={"enabled": True, "percent": 10})
        at_10 = {i for i in range(1000) if service.is_enabled("new_pricing", f"c-{i}")}
        Flag.objects.filter(name="new_pricing").update(percent=50)
        service._cache.clear()
        at_50 = {i for i in range(1000) if service.is_enabled("new_pricing", f"c-{i}")}
        self.assertLess(at_10, at_50)

    def test_unregistered_flag_is_a_bug(self):
        with self.assertRaises(KeyError):
            service.is_enabled("typo_flag", "c-1")


class FlagDebtTests(SimpleTestCase):
    def test_no_flag_outlives_its_expiry(self):
        """A "time bomb": CI turns red the day a flag expires, so old flags get removed."""
        expired = [name for name, meta in FLAGS.items() if meta["expires"] < dt.date.today()]
        self.assertEqual(expired, [], f"remove expired flags and their old code paths: {expired}")

    def test_every_flag_has_an_owner_and_a_type(self):
        for name, meta in FLAGS.items():
            self.assertIn(meta["type"], {"release", "experiment", "ops", "permission"}, name)
            self.assertTrue(meta["owner"], name)


class QuoteEndpointTests(TestCase):
    def setUp(self):
        service._cache.clear()

    def test_flag_off_serves_v1(self):
        Flag.objects.update_or_create(name="new_pricing", defaults={"enabled": False, "percent": 100})
        body = self.client.get("/api/quote?customer=c-1&total_cents=6000").json()
        self.assertEqual((body["engine"], body["discount_cents"]), ("v1", 0))

    def test_flag_fully_on_serves_v2(self):
        Flag.objects.update_or_create(name="new_pricing", defaults={"enabled": True, "percent": 100})
        body = self.client.get("/api/quote?customer=c-1&total_cents=6000").json()
        self.assertEqual((body["engine"], body["discount_cents"]), ("v2", 300))
