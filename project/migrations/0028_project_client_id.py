# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-07-13 07:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0027_merge_20180708_0706'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='client_id',
            field=models.CharField(blank=True, default=None, max_length=128, null=True, unique=True),
        ),
    ]
