# Generated by Django 5.0.1 on 2024-02-23 18:44

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('GPTCommunication', '0011_requirementdetail'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ReqGenDecision', models.IntegerField()),
                ('timestamp', models.DateTimeField(auto_now_add=True, null=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='requirementdetail',
            name='id',
        ),
        migrations.AlterField(
            model_name='requirementdetail',
            name='requirementID',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='GPTCommunication.requirementslist'),
        ),
    ]