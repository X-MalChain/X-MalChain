# Generated by Django 4.0.1 on 2022-11-08 11:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='kgtest',
            name='apiList',
            field=models.CharField(max_length=120, null=True),
        ),
        migrations.AlterField(
            model_name='kgtest',
            name='perList',
            field=models.CharField(max_length=120, null=True),
        ),
    ]
