from django.core.management.base import BaseCommand, CommandError

from flags.models import Flag
from flags.registry import FLAGS


class Command(BaseCommand):
    help = "Show or change a feature flag at runtime: flag new_pricing --percent 10 | --on | --off"

    def add_arguments(self, parser):
        parser.add_argument("name")
        parser.add_argument("--percent", type=int)
        state = parser.add_mutually_exclusive_group()
        state.add_argument("--on", action="store_true")
        state.add_argument("--off", action="store_true", help="kill switch: off for everyone")

    def handle(self, *args, name, percent, on, off, **options):
        if name not in FLAGS:
            raise CommandError(f"unknown flag {name}")
        flag, _ = Flag.objects.get_or_create(name=name)
        if percent is not None:
            if not 0 <= percent <= 100:
                raise CommandError("percent must be 0-100")
            flag.percent = percent
            flag.enabled = True
        if on:
            flag.enabled = True
        if off:
            flag.enabled = False
        flag.save()
        self.stdout.write(str(flag))
