from django.db import migrations


def seed(apps, schema_editor):
    """Create every registered flag OFF: the code ships dark; turning it on is a separate act (a release)."""
    from flags.registry import FLAGS

    Flag = apps.get_model("flags", "Flag")
    for name in FLAGS:
        Flag.objects.get_or_create(name=name, defaults={"enabled": False, "percent": 0})


class Migration(migrations.Migration):
    dependencies = [("flags", "0001_initial")]

    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
