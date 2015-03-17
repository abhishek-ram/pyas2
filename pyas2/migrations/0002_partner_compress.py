# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pyas2', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='partner',
            name='compress',
            field=models.BooleanField(default=True, verbose_name=b'Compress Message'),
            preserve_default=True,
        ),
    ]
