# Generated by Django 3.1.14 on 2022-11-11 19:20

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('orgues', '0062_auto_20220512_1607'),
    ]

    operations = [
        migrations.AlterField(
            model_name='image',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Chargée par'),
        ),
        migrations.AlterField(
            model_name='orgue',
            name='lien_inventaire_regions',
            field=models.CharField(blank=True, max_length=60, null=True, verbose_name="Référence(s) IM de l'inventaire régional"),
        ),
    ]