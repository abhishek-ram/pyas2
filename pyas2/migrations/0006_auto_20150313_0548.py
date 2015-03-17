# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.files.storage


class Migration(migrations.Migration):

    dependencies = [
        ('pyas2', '0005_message_compressed'),
    ]

    operations = [
        migrations.AddField(
            model_name='partner',
            name='cmd_receive',
            field=models.CharField(max_length=255, null=True, verbose_name=b'Command on Message Receipt', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='partner',
            name='cmd_send',
            field=models.CharField(max_length=255, null=True, verbose_name=b'Command on Successful Message Send', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='partner',
            name='email_address',
            field=models.EmailField(max_length=75, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='partner',
            name='https_ca_cert',
            field=models.FileField(storage=django.core.files.storage.FileSystemStorage(base_url=b'/pyas2', location=b'/opt/pyapp/djproject'), null=True, upload_to=b'certificates', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='partner',
            name='keep_filename',
            field=models.BooleanField(default=False, verbose_name=b'Keep Original Filename'),
            preserve_default=True,
        ),
    ]
