# Generated by Django 4.1.7 on 2023-05-04 09:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0024_apirequsetper'),
    ]

    operations = [
        migrations.CreateModel(
            name='augmenTestNode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nodeID', models.IntegerField(blank=True, null=True)),
                ('actionName', models.CharField(max_length=120)),
                ('perList', models.CharField(blank=True, default='', max_length=120)),
                ('apiList', models.CharField(blank=True, default='', max_length=120)),
            ],
        ),
        migrations.CreateModel(
            name='augmenTestRel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sourceID', models.IntegerField()),
                ('sourceAct', models.CharField(blank=True, default='', max_length=200)),
                ('targetID', models.IntegerField()),
                ('targetAct', models.CharField(blank=True, default='', max_length=200)),
                ('relation', models.CharField(blank=True, max_length=120)),
            ],
        ),
    ]
