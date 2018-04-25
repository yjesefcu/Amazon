# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0004_auto_20180401_2055'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='purchasing_count',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='product',
            name='purchasing_expect_count',
            field=models.IntegerField(null=True, blank=True),
        ),
    ]
