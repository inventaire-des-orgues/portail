# Generated by Django 2.2.13 on 2021-04-26 12:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orgues', '0040_auto_20210426_1201'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contribution',
            name='date',
            field=models.DateTimeField(auto_now=True, verbose_name='Date de contribution'),
        ),
        migrations.AlterField(
            model_name='contribution',
            name='description',
            field=models.CharField(max_length=500, verbose_name='Description de la contribution'),
        ),
    ]