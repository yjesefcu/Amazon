# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('purchasing', '0003_auto_20180401_2055'),
    ]

    operations = [
        migrations.AlterField(
            model_name='purchasingorder',
            name='expect_date',
            field=models.CharField(max_length=50, null=True, blank=True),
        ),
    ]
