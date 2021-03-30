import os
import json
from django.core.management.base import BaseCommand
from orgues.models import Facteur
from tqdm import tqdm

class Command(BaseCommand):
    help = "Modifie la longitude et la latitude des ateliers des facteurs d'orgue"

    def add_arguments(self, parser):
        parser.add_argument('path', nargs=1, type=str,
                            help='Chemin vers le dossier contenant les facteurs à importer')

    def handle(self, *args, **options):
        if not os.path.exists(options['path'][0]):
            return "Path does not exist"
        with open(options['path'][0], "r", encoding="utf-8") as f:
            print('Lecture JSON et import des orgues.')
            rows = json.load(f)
            compte = 0
            for row in tqdm(rows):
                facteur_result = Facteur.objects.filter(nom=row.get("facteur"))
                if facteur_result.count() == 1:
                    facteur = facteur_result[0]
                    facteur.latitude_atelier = float(row["latitude"])
                    facteur.longitude_atelier = float(row["longitude"])
                    facteur.save()
                elif facteur_result.count() > 1:
                    compte += 1
                    print("Il y a un doublon pour le facteur {}.".format(row.get("facteur")))
                else :
                    compte += 1
                    print("Aucun facteur trouvé pour {}.".format(row['facteur']))
            print("Problème pour {} facteurs.".format(compte))