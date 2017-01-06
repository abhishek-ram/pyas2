# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.files.storage


class Migration(migrations.Migration):

    dependencies = [
        ('pyas2', '0006_auto_20150313_0548'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='reties',
            field=models.IntegerField(null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='message',
            name='status',
            field=models.CharField(max_length=2, choices=[(b'S', b'Success'), (b'E', b'Error'), (b'W', b'Warning'), (b'P', b'Pending'), (b'R', b'Retry'), (b'IP', b'In Process')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='partner',
            name='cmd_receive',
            field=models.CharField(help_text=b'Command exectued after successful message receipt, replacements are ${filename}, ${fullfilename}, ${subject}, ${sender}, ${recevier}, ${messageid}', max_length=255, null=True, verbose_name=b'Command on Message Receipt', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='partner',
            name='cmd_send',
            field=models.CharField(help_text=b'Command exectued after successful message send, replacements are ${filename}, ${subject}, ${sender}, ${recevier}, ${messageid}', max_length=255, null=True, verbose_name=b'Command on Message Send', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='partner',
            name='encryption',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name=b'Encrypt Message', choices=[(b'des_ede3_cbc', b'3DES'), (b'des_ede_cbc', b'DES'), (b'rc2_40_cbc', b'RC2-40'), (b'rc4', b'RC4-40'), (b'aes_128_cbc', b'AES-128'), (b'aes_192_cbc', b'AES-192'), (b'aes_256_cbc', b'AES-256')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='partner',
            name='http_auth',
            field=models.BooleanField(default=False, verbose_name=b'Enable Authentication'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='partner',
            name='https_ca_cert',
            field=models.FileField(storage=django.core.files.storage.FileSystemStorage(base_url=b'/pyas2', location=b'/opt/pyapp/djproject'), upload_to=b'certificates', null=True, verbose_name=b'HTTPS Local CA Store', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='partner',
            name='keep_filename',
            field=models.BooleanField(default=False, help_text=b'Use Original Filename to to store file on receipt, use this option only if you are sure partner sends unique names', verbose_name=b'Keep Original Filename'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='partner',
            name='signature',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name=b'Sign Message', choices=[(b'sha1', b'SHA-1')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='privatecertificate',
            name='ca_cert',
            field=models.FileField(storage=django.core.files.storage.FileSystemStorage(base_url=b'/pyas2', location=b'/opt/pyapp/djproject'), upload_to=b'certificates', null=True, verbose_name=b'Local CA Store', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='publiccertificate',
            name='ca_cert',
            field=models.FileField(storage=django.core.files.storage.FileSystemStorage(base_url=b'/pyas2', location=b'/opt/pyapp/djproject'), upload_to=b'certificates', null=True, verbose_name=b'Local CA Store', blank=True),
            preserve_default=True,
        ),
    ]
