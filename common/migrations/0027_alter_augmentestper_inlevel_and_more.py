# Generated by Django 4.1.7 on 2023-05-04 13:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0026_augmentestapi_augmentestper'),
    ]

    operations = [
        migrations.AlterField(
            model_name='augmentestper',
            name='inLevel',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AlterField(
            model_name='augmentestper',
            name='outLevel',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AlterField(
            model_name='augmentestper',
            name='perID',
            field=models.IntegerField(blank=True),
        ),
    ]