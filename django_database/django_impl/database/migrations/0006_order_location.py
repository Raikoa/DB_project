# Generated by Django 5.2 on 2025-04-30 11:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('database', '0005_inbox'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='location',
            field=models.TextField(default='-'),
        ),
    ]
