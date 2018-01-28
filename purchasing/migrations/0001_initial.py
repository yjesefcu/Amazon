# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0002_refunditem_fbareturnfee'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Contract',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('contract_number', models.CharField(max_length=100)),
                ('supplier', models.CharField(max_length=255)),
                ('contact_person', models.CharField(max_length=50, null=True, blank=True)),
                ('contact_phone', models.CharField(max_length=50, null=True, blank=True)),
                ('traffic_comment', models.CharField(max_length=255, null=True, blank=True)),
                ('operator', models.CharField(max_length=100, null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='FinanceRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('fee_type', models.CharField(max_length=20)),
                ('need_payed', models.FloatField()),
                ('payed', models.FloatField()),
                ('pay_time', models.DateTimeField()),
                ('creator', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='InboundProducts',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('shipping_date', models.DateField()),
                ('traffic_info', models.CharField(max_length=255, null=True, blank=True)),
                ('count', models.IntegerField(null=True, blank=True)),
                ('inbound_time', models.DateTimeField(null=True, blank=True)),
                ('traffic_fee', models.FloatField(null=True, blank=True)),
                ('traffic_fee_payed', models.FloatField(null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='OrderStatus',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(max_length=50)),
                ('name', models.CharField(max_length=50)),
                ('next_status', models.IntegerField(null=True, blank=True)),
                ('role', models.CharField(max_length=50, null=True, blank=True)),
                ('permissions', models.CharField(max_length=100, null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='PurchasingOrder',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('MarketplaceId', models.CharField(max_length=50)),
                ('SellerSKU', models.CharField(max_length=50)),
                ('name', models.CharField(max_length=255, null=True, blank=True)),
                ('create_time', models.DateTimeField(null=True, blank=True)),
                ('count', models.IntegerField(null=True, blank=True)),
                ('price', models.FloatField(null=True, blank=True)),
                ('total_price', models.FloatField(null=True, blank=True)),
                ('traffic_fee', models.FloatField(null=True, blank=True)),
                ('other_fee', models.FloatField(null=True, blank=True)),
                ('deposit', models.FloatField(null=True, blank=True)),
                ('deposit_payed', models.FloatField(null=True, blank=True)),
                ('traffic_fee_payed', models.FloatField(null=True, blank=True)),
                ('other_fee_payed', models.FloatField(null=True, blank=True)),
                ('final_payment_payed', models.FloatField(null=True, blank=True)),
                ('expect_date', models.DateField(null=True, blank=True)),
                ('unit_price', models.FloatField(null=True, blank=True)),
                ('received_count', models.IntegerField(null=True, blank=True)),
                ('contract', models.ForeignKey(to='purchasing.Contract')),
                ('creator', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('parent', models.ForeignKey(related_name='children', blank=True, to='purchasing.PurchasingOrder', null=True)),
                ('product', models.ForeignKey(related_name='purchasing_orders', to='products.Product')),
                ('status', models.ForeignKey(to='purchasing.OrderStatus')),
            ],
        ),
        migrations.AddField(
            model_name='inboundproducts',
            name='order',
            field=models.ForeignKey(related_name='inbounds', to='purchasing.PurchasingOrder'),
        ),
        migrations.AddField(
            model_name='inboundproducts',
            name='product',
            field=models.ForeignKey(to='products.Product'),
        ),
        migrations.AddField(
            model_name='inboundproducts',
            name='status',
            field=models.ForeignKey(to='purchasing.OrderStatus'),
        ),
        migrations.AddField(
            model_name='financerecord',
            name='order',
            field=models.ForeignKey(to='purchasing.PurchasingOrder'),
        ),
    ]
