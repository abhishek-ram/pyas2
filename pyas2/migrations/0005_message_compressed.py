# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pyas2', '0004_auto_20150311_1258'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='compressed',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
