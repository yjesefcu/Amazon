# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('amazon_services', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='marketaccount',
            name='exchange_rate',
            field=models.FloatField(default=6.0),
        ),
    ]
