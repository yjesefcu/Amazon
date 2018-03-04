# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('products', '0003_settleorderitem_refund_order'),
        ('purchasing', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrderFee',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('fee', models.FloatField()),
                ('create_time', models.DateTimeField()),
                ('comment', models.CharField(max_length=255, null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='PaymentRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('need_payed', models.FloatField(null=True, blank=True)),
                ('payed', models.FloatField()),
                ('pay_time', models.DateTimeField()),
                ('fee_comment', models.CharField(max_length=100, null=True, blank=True)),
                ('payment_comment', models.CharField(max_length=255, null=True, blank=True)),
                ('creator', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='PurchasingOrderItems',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('SellerSKU', models.CharField(max_length=50)),
                ('name', models.CharField(max_length=255, null=True, blank=True)),
                ('total_price', models.FloatField(null=True, blank=True)),
                ('count', models.IntegerField(null=True, blank=True)),
                ('price', models.FloatField(null=True, blank=True)),
                ('expect_count', models.IntegerField(default=0, null=True, blank=True)),
                ('received_count', models.IntegerField(default=0, null=True, blank=True)),
                ('damage_count', models.IntegerField(default=0, null=True, blank=True)),
                ('total_fee', models.FloatField(null=True, blank=True)),
                ('traffic_fee', models.FloatField(null=True, blank=True)),
                ('other_fee', models.FloatField(null=True, blank=True)),
                ('unit_price', models.FloatField(null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='TrackingOrder',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('shipping_date', models.DateField()),
                ('input_date', models.DateField(null=True, blank=True)),
                ('tracking_company', models.CharField(max_length=255, null=True, blank=True)),
                ('tracking_number', models.CharField(max_length=255, null=True, blank=True)),
                ('traffic_fee', models.FloatField(null=True, blank=True)),
                ('traffic_fee_payed', models.FloatField(null=True, blank=True)),
                ('expect_count', models.IntegerField(null=True, blank=True)),
                ('received_count', models.IntegerField(default=0, null=True, blank=True)),
                ('damage_count', models.IntegerField(default=0, null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='TrackingOrderItems',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('shipping_date', models.DateField(null=True, blank=True)),
                ('input_date', models.DateField(null=True, blank=True)),
                ('expect_count', models.IntegerField(null=True, blank=True)),
                ('received_count', models.IntegerField(default=0, null=True, blank=True)),
                ('damage_count', models.IntegerField(default=0, null=True, blank=True)),
                ('product', models.ForeignKey(to='products.Product')),
            ],
        ),
        migrations.RemoveField(
            model_name='financerecord',
            name='creator',
        ),
        migrations.RemoveField(
            model_name='financerecord',
            name='order',
        ),
        migrations.RemoveField(
            model_name='inboundproducts',
            name='order',
        ),
        migrations.RemoveField(
            model_name='inboundproducts',
            name='product',
        ),
        migrations.RemoveField(
            model_name='inboundproducts',
            name='status',
        ),
        migrations.RemoveField(
            model_name='purchasingorder',
            name='SellerSKU',
        ),
        migrations.RemoveField(
            model_name='purchasingorder',
            name='contract',
        ),
        migrations.RemoveField(
            model_name='purchasingorder',
            name='name',
        ),
        migrations.RemoveField(
            model_name='purchasingorder',
            name='price',
        ),
        migrations.RemoveField(
            model_name='purchasingorder',
            name='product',
        ),
        migrations.RemoveField(
            model_name='purchasingorder',
            name='unit_price',
        ),
        migrations.AddField(
            model_name='purchasingorder',
            name='contact_person',
            field=models.CharField(max_length=50, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='purchasingorder',
            name='contact_phone',
            field=models.CharField(max_length=50, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='purchasingorder',
            name='contract_number',
            field=models.CharField(default=None, max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='purchasingorder',
            name='damage_count',
            field=models.IntegerField(default=0, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='purchasingorder',
            name='expect_count',
            field=models.IntegerField(default=0, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='purchasingorder',
            name='next_payment_comment',
            field=models.TextField(max_length=255, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='purchasingorder',
            name='next_to_pay',
            field=models.FloatField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='purchasingorder',
            name='operator',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='purchasingorder',
            name='supplier',
            field=models.CharField(default=None, max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='purchasingorder',
            name='total_payed',
            field=models.FloatField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='purchasingorder',
            name='traffic_comment',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='purchasingorder',
            name='count',
            field=models.IntegerField(default=0, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='purchasingorder',
            name='received_count',
            field=models.IntegerField(default=0, null=True, blank=True),
        ),
        migrations.DeleteModel(
            name='Contract',
        ),
        migrations.DeleteModel(
            name='FinanceRecord',
        ),
        migrations.DeleteModel(
            name='InboundProducts',
        ),
        migrations.AddField(
            model_name='trackingorderitems',
            name='purchasing_order',
            field=models.ForeignKey(to='purchasing.PurchasingOrder'),
        ),
        migrations.AddField(
            model_name='trackingorderitems',
            name='traffic_order',
            field=models.ForeignKey(related_name='items', to='purchasing.TrackingOrder'),
        ),
        migrations.AddField(
            model_name='trackingorder',
            name='purchasing_order',
            field=models.ForeignKey(related_name='inbounds', to='purchasing.PurchasingOrder'),
        ),
        migrations.AddField(
            model_name='trackingorder',
            name='status',
            field=models.ForeignKey(to='purchasing.OrderStatus'),
        ),
        migrations.AddField(
            model_name='purchasingorderitems',
            name='order',
            field=models.ForeignKey(related_name='items', to='purchasing.PurchasingOrder'),
        ),
        migrations.AddField(
            model_name='purchasingorderitems',
            name='product',
            field=models.ForeignKey(related_name='purchasing_orders', to='products.Product'),
        ),
        migrations.AddField(
            model_name='paymentrecord',
            name='order',
            field=models.ForeignKey(related_name='payments', to='purchasing.PurchasingOrder'),
        ),
        migrations.AddField(
            model_name='paymentrecord',
            name='traffic_order',
            field=models.ForeignKey(blank=True, to='purchasing.TrackingOrder', null=True),
        ),
        migrations.AddField(
            model_name='orderfee',
            name='order',
            field=models.ForeignKey(related_name='fee_records', to='purchasing.PurchasingOrder'),
        ),
    ]
