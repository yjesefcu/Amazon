# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('purchasing', '0002_auto_20180304_1421'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='purchasingorder',
            name='next_payment_comment',
        ),
        migrations.RemoveField(
            model_name='purchasingorder',
            name='next_to_pay',
        ),
        migrations.RemoveField(
            model_name='purchasingorderitems',
            name='unit_price',
        ),
        migrations.AddField(
            model_name='purchasingorder',
            name='final_payment',
            field=models.FloatField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='trackingorder',
            name='final_payment',
            field=models.FloatField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='trackingorderitems',
            name='price',
            field=models.FloatField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='trackingorderitems',
            name='total_price',
            field=models.FloatField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='trackingorderitems',
            name='traffic_fee',
            field=models.FloatField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='trackingorder',
            name='damage_count',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='trackingorder',
            name='received_count',
            field=models.IntegerField(null=True, blank=True),
        ),
    ]
