# Generated by Django 3.1.14 on 2024-03-29 14:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orgues', '0069_auto_20240329_1423'),
    ]

    operations = [
        migrations.AlterField(
            model_name='manufacture',
            name='facteur',
            field=models.ManyToManyField(blank=True, related_name='manufacture', to='orgues.FacteurManufacture', verbose_name='Facteur ayant travaillé dans la manufacture'),
        ),
    ]