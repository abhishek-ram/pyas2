# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pyas2', '0011_auto_20150427_1029'),
    ]

    operations = [
        migrations.AddField(
            model_name='publiccertificate',
            name='verify_cert',
            field=models.BooleanField(default=True, help_text='Uncheck this option to disable certificate verification.', verbose_name='Verify Certificate'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='message',
            name='mdn_mode',
            field=models.CharField(max_length=5, null=True, choices=[(b'SYNC', 'Synchronous'), (b'ASYNC', 'Asynchronous')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='partner',
            name='as2_name',
            field=models.CharField(max_length=100, serialize=False, verbose_name='AS2 Identifier', primary_key=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='partner',
            name='cmd_receive',
            field=models.TextField(help_text='Command executed after successful message receipt, replacements are $filename, $fullfilename, $sender, $recevier, $messageid and any message header such as $Subject', null=True, verbose_name='Command on Message Receipt', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='partner',
            name='cmd_send',
            field=models.TextField(help_text='Command executed after successful message send, replacements are $filename, $sender, $recevier, $messageid and any message header such as $Subject', null=True, verbose_name='Command on Message Send', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='partner',
            name='name',
            field=models.CharField(max_length=100, verbose_name='Partner Name'),
            preserve_default=True,
        ),
    ]
