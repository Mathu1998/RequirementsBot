# Generated by Django 5.0.1 on 2024-01-20 17:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('GPTCommunication', '0008_remove_requirementslist_id_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='requirementslist',
            old_name='RequirementDescription',
            new_name='requirementDescription',
        ),
        migrations.RenameField(
            model_name='requirementslist',
            old_name='RequirementID',
            new_name='requirementID',
        ),
        migrations.RenameField(
            model_name='requirementslist',
            old_name='RequirementName',
            new_name='requirementName',
        ),
    ]
