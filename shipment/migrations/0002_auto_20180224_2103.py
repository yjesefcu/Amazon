# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shipment', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='shipmentorderitem',
            name='tax_fee',
            field=models.FloatField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='shipmentorderitem',
            name='traffic_fee',
            field=models.FloatField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='shipmentorderitem',
            name='unit_weight',
            field=models.FloatField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='shipmentorderitem',
            name='volume_weight',
            field=models.FloatField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='shipmentorder',
            name='ship_type',
            field=models.CharField(default=b'sea', max_length=10),
        ),
        migrations.AlterField(
            model_name='shipmentorder',
            name='volume_args',
            field=models.IntegerField(default=5000),
        ),
    ]
