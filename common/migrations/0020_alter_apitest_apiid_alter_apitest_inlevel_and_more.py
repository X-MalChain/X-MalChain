# Generated by Django 4.1.7 on 2023-04-03 06:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0019_apisdk'),
    ]

    operations = [
        migrations.AlterField(
            model_name='apitest',
            name='apiID',
            field=models.IntegerField(blank=True),
        ),
        migrations.AlterField(
            model_name='apitest',
            name='inLevel',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AlterField(
            model_name='apitest',
            name='outLevel',
            field=models.CharField(blank=True, max_length=50),
        ),
    ]
