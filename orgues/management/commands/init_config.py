import os
import json
from django.conf import settings
from django.core.management.base import BaseCommand

from orgues.models import TypeClavier, Facteur, TypeJeu, Accessoire


class Command(BaseCommand):
    help = 'Population de la base de donnée avec les types de clavier et les jeux les plus courants'
    def add_arguments(self, parser):
        parser.add_argument('path', nargs='?', type=str,
                        help='Chemin vers la config à importer')
        parser.add_argument('--delete', help='Supprime les données existantes', action='store_true')

    def handle(self, *args, **options):
        path = os.path.join(settings.BASE_DIR, "orgues", "management", "commands", "config.json");
        if options['path'] and os.path.exists(options['path']):
            path = options['path']
        if options['delete']:
            print('Effacement de tous les objets de la base.')
            TypeClavier.objects.all().delete()
            TypeJeu.objects.all().delete()
            Facteur.objects.all().delete()
            Accessoire.objects.all().delete()
        print('Import de la config '+path)
        with open(path,
                  "r", encoding='utf-8') as f:
            data = json.load(f)

        print('Import des types de claviers')
        for type_clavier in data["types_claviers"]:
            TypeClavier.objects.get_or_create(nom=type_clavier)

        print('Import des types de jeux')
        for jeu in data["types_jeux"]:
            hauteur = jeu["hauteur"].strip() if jeu["hauteur"] is not None else None
            TypeJeu.objects.get_or_create(nom=jeu["nom"].strip(), hauteur=hauteur)

        print('Import des facteurs')
        for facteur in data["facteurs"]:
            Facteur.objects.get_or_create(nom=facteur)

        print('Import des types d\'accessoires')
        for accessoire in data["type_accessoire"]:
            Accessoire.objects.get_or_create(nom=accessoire)

        print('Import terminé')
