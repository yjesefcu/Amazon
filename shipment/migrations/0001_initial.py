# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('purchasing', '0001_initial'),
        ('products', '0003_settleorderitem_refund_order'),
    ]

    operations = [
        migrations.CreateModel(
            name='BoxProductRelations',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('count', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='ShipmentBox',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('count', models.IntegerField(null=True, blank=True)),
                ('weight', models.FloatField(null=True, blank=True)),
                ('height', models.FloatField(null=True, blank=True)),
                ('length', models.FloatField(null=True, blank=True)),
                ('width', models.FloatField(null=True, blank=True)),
                ('itn_weight', models.FloatField(null=True, blank=True)),
                ('itn_height', models.FloatField(null=True, blank=True)),
                ('itn_length', models.FloatField(null=True, blank=True)),
                ('itn_width', models.FloatField(null=True, blank=True)),
                ('products', models.TextField(null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='ShipmentOrder',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('MarketplaceId', models.CharField(max_length=50)),
                ('create_time', models.DateTimeField()),
                ('count', models.IntegerField(null=True, blank=True)),
                ('product_count', models.IntegerField(null=True, blank=True)),
                ('company', models.CharField(max_length=100, null=True, blank=True)),
                ('tracking_number', models.CharField(max_length=100, null=True, blank=True)),
                ('code', models.CharField(max_length=100, null=True, blank=True)),
                ('ship_type', models.IntegerField(null=True, blank=True)),
                ('volume_args', models.IntegerField(null=True, blank=True)),
                ('boxed_count', models.IntegerField(default=0)),
                ('box_count', models.IntegerField(default=0)),
                ('total_weight', models.FloatField(default=0)),
                ('total_itn_weight', models.FloatField(default=0)),
                ('traffic_fee', models.FloatField(null=True, blank=True)),
                ('tax_fee', models.FloatField(null=True, blank=True)),
                ('status', models.ForeignKey(blank=True, to='purchasing.OrderStatus', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ShipmentOrderItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('SellerSKU', models.CharField(max_length=50)),
                ('count', models.IntegerField()),
                ('boxed_count', models.IntegerField(default=0)),
                ('order', models.ForeignKey(related_name='items', to='shipment.ShipmentOrder')),
                ('product', models.ForeignKey(related_name='shipments', to='products.Product')),
            ],
        ),
        migrations.AddField(
            model_name='shipmentbox',
            name='order',
            field=models.ForeignKey(related_name='boxs', to='shipment.ShipmentOrder'),
        ),
        migrations.AddField(
            model_name='boxproductrelations',
            name='box',
            field=models.ForeignKey(to='shipment.ShipmentBox'),
        ),
        migrations.AddField(
            model_name='boxproductrelations',
            name='order',
            field=models.ForeignKey(to='shipment.ShipmentOrder'),
        ),
        migrations.AddField(
            model_name='boxproductrelations',
            name='order_item',
            field=models.ForeignKey(to='shipment.ShipmentOrderItem'),
        ),
    ]
