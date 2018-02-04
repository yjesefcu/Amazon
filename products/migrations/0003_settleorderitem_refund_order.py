# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0002_refunditem_fbareturnfee'),
    ]

    operations = [
        migrations.AddField(
            model_name='settleorderitem',
            name='refund_order',
            field=models.ForeignKey(blank=True, to='products.RefundItem', null=True),
        ),
    ]
