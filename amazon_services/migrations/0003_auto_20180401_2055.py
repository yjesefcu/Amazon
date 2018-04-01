# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('amazon_services', '0002_marketaccount_exchange_rate'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='requestrecords',
            name='market',
        ),
        migrations.RemoveField(
            model_name='marketaccount',
            name='id',
        ),
        migrations.AddField(
            model_name='marketaccount',
            name='account_name',
            field=models.CharField(max_length=50, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='marketaccount',
            name='MarketplaceId',
            field=models.CharField(max_length=20, serialize=False, primary_key=True),
        ),
        migrations.DeleteModel(
            name='RequestRecords',
        ),
    ]
