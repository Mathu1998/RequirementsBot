# Generated by Django 5.0.1 on 2024-01-22 16:15

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('GPTCommunication', '0010_delete_interaction'),
    ]

    operations = [
        migrations.CreateModel(
            name='RequirementDetail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reqUserStory', models.TextField()),
                ('reqAcceptanceCriteria', models.TextField()),
                ('requirementID', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='GPTCommunication.requirementslist')),
            ],
        ),
    ]
