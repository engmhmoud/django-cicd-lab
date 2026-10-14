from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("orders", "0001_initial")]

    operations = [
        # Unsafe for a rolling deploy: the column is NOT NULL and Django drops the temporary default afterwards,
        # so the PREVIOUS app version (which doesn't know this column) fails on every INSERT.
        migrations.AddField(
            model_name="order",
            name="currency",
            field=models.CharField(default="USD", max_length=3),
            preserve_default=False,
        ),
    ]
