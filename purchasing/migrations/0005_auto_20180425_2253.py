# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('purchasing', '0004_auto_20180417_2206'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchasingorder',
            name='skus',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='trackingorderitems',
            name='old_price',
            field=models.FloatField(null=True, blank=True),
        ),
    ]
