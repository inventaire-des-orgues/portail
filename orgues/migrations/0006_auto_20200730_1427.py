# Generated by Django 2.2.13 on 2020-07-30 14:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orgues', '0005_auto_20200730_1425'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orgue',
            name='designation',
            field=models.CharField(blank=True, default='orgue', max_length=300, verbose_name='Désignation'),
        ),
    ]
