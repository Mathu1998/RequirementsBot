# Generated by Django 5.0.1 on 2024-01-18 18:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('GPTCommunication', '0004_dataupload_remove_interaction_inputdata'),
    ]

    operations = [
        migrations.AddField(
            model_name='dataupload',
            name='timestamp',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
