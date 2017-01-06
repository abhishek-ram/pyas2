# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pyas2', '0003_auto_20150311_1141'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='message',
            name='encryption',
        ),
        migrations.RemoveField(
            model_name='message',
            name='signature',
        ),
        migrations.AddField(
            model_name='mdn',
            name='signed',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='message',
            name='encrypted',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='message',
            name='signed',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
