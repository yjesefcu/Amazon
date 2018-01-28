# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ApiActions',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('desc', models.CharField(max_length=20)),
                ('name', models.CharField(max_length=50)),
                ('params', models.TextField(null=True, blank=True)),
                ('max_requests', models.IntegerField(null=True, blank=True)),
                ('recover_interval', models.IntegerField(null=True, blank=True)),
                ('recover_count', models.IntegerField(null=True, blank=True)),
                ('request_remain', models.IntegerField(null=True, blank=True)),
                ('last_request', models.DateTimeField(null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='ApiCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('desc', models.CharField(max_length=20)),
                ('uri', models.CharField(max_length=100)),
                ('version', models.CharField(max_length=10)),
            ],
        ),
        migrations.CreateModel(
            name='Market',
            fields=[
                ('id', models.CharField(max_length=10, serialize=False, primary_key=True)),
                ('cn', models.CharField(max_length=10)),
                ('en', models.CharField(max_length=10)),
            ],
        ),
        migrations.CreateModel(
            name='MarketAccount',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('country', models.CharField(max_length=10)),
                ('host', models.CharField(max_length=50)),
                ('MWSAuthToken', models.CharField(max_length=15)),
                ('AWSAccessKeyId', models.CharField(max_length=25)),
                ('SellerId', models.CharField(max_length=20)),
                ('SecretKey', models.CharField(max_length=50)),
                ('MarketplaceId', models.CharField(max_length=20)),
                ('currency_code', models.CharField(max_length=10)),
                ('period_start', models.DateField(null=True, blank=True)),
                ('period_days', models.IntegerField(default=14)),
                ('sync_report_status', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='ReportRequestRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('report_type', models.CharField(max_length=100)),
                ('start_time', models.DateTimeField(null=True, blank=True)),
                ('end_time', models.DateTimeField(null=True, blank=True)),
                ('request_time', models.DateTimeField()),
                ('request_report_id', models.CharField(max_length=50)),
                ('report_id', models.CharField(max_length=50, null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='RequestRecords',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uri', models.CharField(max_length=100)),
                ('action', models.CharField(max_length=50, null=True, blank=True)),
                ('params', models.TextField(null=True, blank=True)),
                ('create_time', models.DateTimeField()),
                ('sent_time', models.DateTimeField(null=True, blank=True)),
                ('result', models.IntegerField(default=0)),
                ('errors', models.TextField(null=True, blank=True)),
                ('market', models.ForeignKey(to='amazon_services.MarketAccount')),
            ],
        ),
        migrations.AddField(
            model_name='apiactions',
            name='category',
            field=models.ForeignKey(related_name='actions', to='amazon_services.ApiCategory'),
        ),
    ]
