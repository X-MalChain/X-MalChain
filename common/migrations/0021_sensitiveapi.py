# Generated by Django 4.1.7 on 2023-04-26 08:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0020_alter_apitest_apiid_alter_apitest_inlevel_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='sensitiveApi',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('api', models.CharField(blank=True, default='', max_length=200)),
                ('permission', models.CharField(blank=True, default='', max_length=200)),
            ],
        ),
    ]