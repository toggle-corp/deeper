# Generated by Django 3.2 on 2021-05-03 04:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('geo', '0036_auto_20190730_0617'),
    ]

    operations = [
        migrations.AlterField(
            model_name='adminlevel',
            name='geo_area_titles',
            field=models.JSONField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='geoarea',
            name='data',
            field=models.JSONField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='region',
            name='geo_options',
            field=models.JSONField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='region',
            name='key_figures',
            field=models.JSONField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='region',
            name='media_sources',
            field=models.JSONField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='region',
            name='population_data',
            field=models.JSONField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='region',
            name='regional_groups',
            field=models.JSONField(blank=True, default=None, null=True),
        ),
    ]
