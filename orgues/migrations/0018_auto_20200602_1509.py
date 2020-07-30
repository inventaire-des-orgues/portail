# Generated by Django 2.2.7 on 2020-06-02 15:09

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('orgues', '0017_orgue_keywords'),
    ]

    operations = [
        migrations.AddField(
            model_name='orgue',
            name='console',
            field=models.TextField(blank=True, help_text="Description de la console (ex: en fenêtre, séparée organiste tourné vers l'orgue ...).", null=True, verbose_name='Description console'),
        ),
        migrations.AlterField(
            model_name='evenement',
            name='facteurs',
            field=models.ManyToManyField(blank=True, related_name='evenements', to='orgues.Facteur'),
        ),
        migrations.AlterField(
            model_name='orgue',
            name='code_departement',
            field=models.CharField(max_length=3, validators=[django.core.validators.RegexValidator(message='Renseigner un code de département valide', regex='^(97[12346]|0[1-9]|[1-8][0-9]|9[0-5]|2[AB])$')], verbose_name='Code département'),
        ),
        migrations.AlterField(
            model_name='orgue',
            name='diapason',
            field=models.CharField(blank=True, help_text='Hauteur en Hertz du A2 joué par le prestant 4', max_length=15, null=True),
        ),
        migrations.AlterField(
            model_name='orgue',
            name='proprietaire',
            field=models.CharField(choices=[('commune', 'Commune'), ('etat', 'Etat'), ('association_culturelle', 'Association culturelle'), ('diocese', 'Diocèse'), ('paroisse', 'Paroisse')], default='commune', max_length=20),
        ),
        migrations.AlterField(
            model_name='orgue',
            name='tirage_jeux',
            field=models.CharField(blank=True, choices=[('mecanique', 'Mécanique'), ('pneumatique', 'Pneumatique'), ('electrique', 'Electrique'), ('electro_pneumatique', 'Electro-pneumatique')], max_length=20, null=True, verbose_name='Tirage des jeux'),
        ),
        migrations.AlterField(
            model_name='orgue',
            name='transmission_notes',
            field=models.CharField(blank=True, choices=[('mecanique', 'Mécanique'), ('mecanique_suspendue', 'Mécanique suspendue'), ('mecanique_balanciers', 'Mécanique à balanciers'), ('mecanique_barker', 'Mécanique Barker'), ('pneumatique', 'Pneumatique'), ('electrique', 'Electrique'), ('electrique_proportionnelle', 'Electrique proportionnelle'), ('electro_pneumatique', 'Electro-pneumatique')], max_length=30, null=True),
        ),
        migrations.AlterField(
            model_name='typejeu',
            name='hauteur',
            field=models.CharField(help_text='La hauteur est indiquée par convention en pieds, en chiffres arabes, sans précision de l\'unité. La nombre de rangs des fournitures, plein-jeux, cornet, etc. est indiqué en chiffres romains, sans précision du terme "rangs" (ni "rgs").', max_length=20),
        ),
        migrations.CreateModel(
            name='Source',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('disque', 'Disque'), ('web', 'Web'), ('ouvrage', 'Ouvrage'), ('video', 'Video')], max_length=20, verbose_name='Type de source')),
                ('description', models.CharField(max_length=100, verbose_name='Description de la source')),
                ('lien', models.CharField(max_length=100, verbose_name='Lien')),
                ('orgue', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sources', to='orgues.Orgue')),
            ],
        ),
    ]