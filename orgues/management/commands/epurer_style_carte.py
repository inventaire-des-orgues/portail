import json
import os

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from orgues.services.style_carte import URL_STYLE_IGN, epurer_style_ign


class Command(BaseCommand):
    help = "Télécharge le style Plan IGN gris et écrit sa version épurée, servie par la carte des orgues"

    def add_arguments(self, parser):
        parser.add_argument('--sortie', help='Fichier écrit (par défaut, le style servi par la carte)',
                            default=os.path.join(settings.BASE_DIR, "static", "static_dirs", "carte",
                                                 "plan-ign-gris-epure.json"))

    def handle(self, *args, **options):
        try:
            reponse = requests.get(URL_STYLE_IGN, timeout=30)
            reponse.raise_for_status()
            style = reponse.json()
        except (requests.RequestException, ValueError) as erreur:
            raise CommandError(f"Téléchargement du style IGN impossible : {erreur}") from erreur

        style_epure = epurer_style_ign(style)
        with open(options['sortie'], "w", encoding="utf-8") as fichier:
            json.dump(style_epure, fichier, ensure_ascii=False, separators=(",", ":"))
        self.stdout.write(f"{len(style_epure['layers'])} couches gardées sur {len(style['layers'])} : "
                          f"{options['sortie']}")
