from orgues.models import Orgue
from django.core.management.base import BaseCommand
from tqdm import tqdm
import json
import numpy as np
import os


class Command(BaseCommand):
    """
    Importe les coordonnées latitude/longitude du fichier fourni dans la base de données. Le fichier à fournir doit être celui 
    créé par la fonction calcul_barycenter_osm. Par défaut, la fonction ne complète les champs latitude/longitude que pour les orgues 
    où ces deux champs ne sont pas déjà renseignés.
    L'option --ecraseif écrase les latitude/longitude si l'écart entre les anciennes et les nouvelles est supérieur à 30 mètres.
    L'option --ecraseall écrase toutes les latitude/longitude.
    """
    help = ''

    def add_arguments(self, parser):
        parser.add_argument('path', nargs=1, type=str,
                            help='Nom du facteur à retirer de la base de données.')
        parser.add_argument('--ecraseif',
                help="Ecrase la position latitude/longitude de l'orgue si la distance est supérieure à 30 mètres.")
        parser.add_argument('--ecraseall',
                help="Ecrase la position latitude/longitude de l'orgue.")

    def handle(self, *args, **options):
        if not os.path.exists(options['path'][0]):
            return "Path does not exist"
        with open(options['path'][0], "r", encoding="utf-8") as f:
            print('Lecture JSON et import des coordonnées des orgues.')
            rows = json.load(f)
            compte = 0
            for row in tqdm(rows):
                codification = row['codification']
                orgue = Orgue.objects.get(codification=codification)
                if orgue.latitude == None or orgue.longitude == None:
                    orgue.latitude = row['latitude']
                    orgue.longitude = row['longitude']
                else:
                    if options['ecraseif']:
                        phi1 = row['latitude'] * np.pi / 180
                        phi2 = orgue.latitude * np.pi / 180
                        l1 = row['longitude'] * np.pi / 180
                        l2 = orgue.longitude * np.pi / 180
                        d = 2 * 6378137 * np.arcsin(np.sqrt(np.sin((phi1 - phi2)/2)**2 + np.cos(phi1) * np.cos(phi2) * np.sin((l1 - l2)/2)**2))
                        if d >= 30:
                            orgue.latitude = row['latitude']
                            orgue.longitude = row['longitude']
                    elif options['ecraseall']:
                        orgue.latitude = row['latitude']
                        orgue.longitude = row['longitude']
                orgue.save()