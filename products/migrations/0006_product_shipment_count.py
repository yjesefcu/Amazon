# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0005_auto_20180425_2142'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='shipment_count',
            field=models.IntegerField(default=0, null=True, blank=True),
        ),
    ]
