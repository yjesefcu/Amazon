# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('amazon_services', '0003_auto_20180401_2055'),
    ]

    operations = [
        migrations.RenameField(
            model_name='marketaccount',
            old_name='account_name',
            new_name='account',
        ),
    ]
