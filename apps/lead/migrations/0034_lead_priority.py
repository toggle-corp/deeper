# Generated by Django 2.1.15 on 2020-07-29 04:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lead', '0033_auto_20200715_0546'),
    ]

    operations = [
        migrations.AddField(
            model_name='lead',
            name='priority',
            field=models.IntegerField(choices=[(300, 'High'), (200, 'Medium'), (100, 'Low')], default=100),
        ),
    ]
