# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.files.storage


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Log',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(max_length=2, choices=[(b'S', b'Success'), (b'E', b'Error'), (b'W', b'Warning')])),
                ('text', models.CharField(max_length=255)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MDN',
            fields=[
                ('message_id', models.CharField(max_length=100, serialize=False, primary_key=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(max_length=2, choices=[(b'S', b'Sent'), (b'R', b'Received'), (b'P', b'Pending')])),
                ('file', models.CharField(max_length=255)),
                ('headers', models.TextField(null=True)),
                ('return_url', models.URLField(null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('message_id', models.CharField(max_length=100, serialize=False, primary_key=True)),
                ('headers', models.TextField(null=True)),
                ('direction', models.CharField(max_length=5, choices=[(b'IN', b'Inbound'), (b'OUT', b'Outbound')])),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(max_length=2, choices=[(b'S', b'Success'), (b'E', b'Error'), (b'W', b'Warning'), (b'P', b'Pending'), (b'IP', b'In Process')])),
                ('adv_status', models.CharField(max_length=255, null=True)),
                ('mic', models.CharField(max_length=100, null=True)),
                ('mdn_mode', models.CharField(max_length=2, null=True, choices=[(b'SYNC', b'Synchronous'), (b'ASYNC', b'Asynchronous')])),
                ('mdn', models.OneToOneField(related_name='omessage', null=True, to='pyas2.MDN')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('name', models.CharField(max_length=100)),
                ('as2_name', models.CharField(max_length=100, serialize=False, primary_key=True)),
                ('email_address', models.EmailField(max_length=75, null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Partner',
            fields=[
                ('name', models.CharField(max_length=100)),
                ('as2_name', models.CharField(max_length=100, serialize=False, primary_key=True)),
                ('http_auth', models.BooleanField(default=False, verbose_name=b'HTTP Authentication')),
                ('http_auth_user', models.CharField(max_length=100, null=True, blank=True)),
                ('http_auth_pass', models.CharField(max_length=100, null=True, blank=True)),
                ('target_url', models.URLField()),
                ('subject', models.CharField(default=b'EDI Message sent using pyas2', max_length=255)),
                ('content_type', models.CharField(default=b'application/edi-consent', max_length=100, choices=[(b'application/EDI-X12', b'application/EDI-X12'), (b'application/EDIFACT', b'application/EDIFACT'), (b'application/edi-consent', b'application/edi-consent'), (b'application/XML', b'application/XML')])),
                ('encryption', models.CharField(blank=True, max_length=20, null=True, choices=[(b'des_ede3_cbc', b'3DES'), (b'des_ede_cbc', b'DES'), (b'rc2_40_cbc', b'RC2-40'), (b'rc4', b'RC4-40'), (b'aes_128_cbc', b'AES-128'), (b'aes_192_cbc', b'AES-192'), (b'aes_256_cbc', b'AES-256')])),
                ('signature', models.CharField(blank=True, max_length=20, null=True, choices=[(b'sha1', b'SHA-1')])),
                ('mdn', models.BooleanField(default=True, verbose_name=b'Request MDN')),
                ('mdn_mode', models.CharField(default=b'SYNC', max_length=20, choices=[(b'SYNC', b'Synchronous'), (b'ASYNC', b'Asynchronous')])),
                ('mdn_sign', models.BooleanField(default=False, verbose_name=b'Request Signed MDN')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Payload',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('content_type', models.CharField(max_length=255)),
                ('file', models.CharField(max_length=255)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PrivateCertificate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('certificate', models.FileField(storage=django.core.files.storage.FileSystemStorage(base_url=b'/pyas2', location=b'/opt/pyapp/djproject'), upload_to=b'certificates')),
                ('ca_cert', models.FileField(storage=django.core.files.storage.FileSystemStorage(base_url=b'/pyas2', location=b'/opt/pyapp/djproject'), null=True, upload_to=b'certificates', blank=True)),
                ('certificate_passphrase', models.CharField(max_length=100)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PublicCertificate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('certificate', models.FileField(storage=django.core.files.storage.FileSystemStorage(base_url=b'/pyas2', location=b'/opt/pyapp/djproject'), upload_to=b'certificates')),
                ('ca_cert', models.FileField(storage=django.core.files.storage.FileSystemStorage(base_url=b'/pyas2', location=b'/opt/pyapp/djproject'), null=True, upload_to=b'certificates', blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='partner',
            name='encryption_key',
            field=models.ForeignKey(related_name='enc_partner', blank=True, to='pyas2.PublicCertificate', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='partner',
            name='signature_key',
            field=models.ForeignKey(related_name='sign_partner', blank=True, to='pyas2.PublicCertificate', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='organization',
            name='encryption_key',
            field=models.ForeignKey(related_name='enc_org', blank=True, to='pyas2.PrivateCertificate', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='organization',
            name='signature_key',
            field=models.ForeignKey(related_name='sign_org', blank=True, to='pyas2.PrivateCertificate', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='message',
            name='organization',
            field=models.ForeignKey(to='pyas2.Organization', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='message',
            name='partner',
            field=models.ForeignKey(to='pyas2.Partner', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='message',
            name='payload',
            field=models.OneToOneField(related_name='message', null=True, to='pyas2.Payload'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='log',
            name='message',
            field=models.ForeignKey(to='pyas2.Message'),
            preserve_default=True,
        ),
    ]
