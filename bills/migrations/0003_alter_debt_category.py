# Generated by Django 5.1.4 on 2025-01-07 20:16

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bills", "0002_remove_category_unique_category_per_user_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="debt",
            name="category",
            field=models.ForeignKey(
                default=9,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="debts",
                to="bills.category",
            ),
        ),
    ]
