# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('purchasing', '0005_auto_20180425_2253'),
    ]

    operations = [
        migrations.AlterField(
            model_name='purchasingorder',
            name='supplier',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
    ]
