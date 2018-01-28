# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='refunditem',
            name='FBAReturnFee',
            field=models.FloatField(null=True, verbose_name='\u9000\u8d27\u670d\u52a1\u8d39', blank=True),
        ),
    ]
