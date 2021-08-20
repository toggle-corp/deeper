# Generated by Django 2.1.15 on 2021-04-27 05:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('entry', '0029_entry_approved_by'),
    ]

    operations = [
        migrations.RenameField(
            model_name='entry',
            old_name='verified',
            new_name='controlled',
        ),
        migrations.RenameField(
            model_name='entry',
            old_name='verification_last_changed_by',
            new_name='controlled_changed_by',
        ),
        migrations.RenameField(
            model_name='entry',
            old_name='approved_by',
            new_name='verified_by',
        ),
    ]
