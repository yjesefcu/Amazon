# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0003_settleorderitem_refund_order'),
    ]

    operations = [
        migrations.CreateModel(
            name='GiftPacking',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('count', models.IntegerField()),
                ('create_time', models.DateTimeField()),
            ],
        ),
        migrations.AddField(
            model_name='product',
            name='gifts',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='MarketplaceId',
            field=models.CharField(db_index=True, max_length=30, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='giftpacking',
            name='product',
            field=models.ForeignKey(to='products.Product'),
        ),
    ]
