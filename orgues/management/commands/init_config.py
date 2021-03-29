import os
import json
from django.conf import settings
from django.core.management.base import BaseCommand

from orgues.models import TypeClavier, Facteur, TypeJeu, Accessoire


class Command(BaseCommand):
    help = 'Population de la base de donnée avec les types de clavier et les jeux les plus courants'

    def handle(self, *args, **options):

        with open(os.path.join(settings.BASE_DIR, "orgues", "management", "commands", "config.json"),
                  "r", encoding='utf-8') as f:
            data = json.load(f)

        for type_clavier in data["types_claviers"]:
            TypeClavier.objects.get_or_create(nom=type_clavier)

        for jeu in data["types_jeux"]:

            TypeJeu.objects.get_or_create(nom=jeu["nom"].strip(), hauteur=jeu["hauteur"].strip())

        for facteur in data["facteurs"]:
            Facteur.objects.get_or_create(nom=facteur)

        for accessoire in data["type_accessoire"]:
            Accessoire.objects.get_or_create(nom=accessoire)
