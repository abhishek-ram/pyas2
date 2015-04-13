# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pyas2', '0008_auto_20150317_0450'),
    ]

    operations = [
        migrations.RenameField(
            model_name='message',
            old_name='reties',
            new_name='retries',
        ),
    ]
