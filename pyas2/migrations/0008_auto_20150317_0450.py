# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pyas2', '0007_auto_20150313_0707'),
    ]

    operations = [
        migrations.AlterField(
            model_name='partner',
            name='mdn_mode',
            field=models.CharField(blank=True, max_length=20, null=True, choices=[(b'SYNC', b'Synchronous'), (b'ASYNC', b'Asynchronous')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='partner',
            name='mdn_sign',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name=b'Request Signed MDN', choices=[(b'sha1', b'SHA-1')]),
            preserve_default=True,
        ),
    ]
