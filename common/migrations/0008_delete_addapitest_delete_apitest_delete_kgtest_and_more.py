# Generated by Django 4.0.1 on 2022-11-08 12:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0007_initial'),
    ]

    operations = [
        migrations.DeleteModel(
            name='AddApiTest',
        ),
        migrations.DeleteModel(
            name='ApiTest',
        ),
        migrations.DeleteModel(
            name='KgTest',
        ),
        migrations.DeleteModel(
            name='PerTest',
        ),
        migrations.DeleteModel(
            name='RepApiTest',
        ),
    ]
