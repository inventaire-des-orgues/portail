from orgues.models import Orgue
from django.core.management.base import BaseCommand
from tqdm import tqdm
import json
import os


class Command(BaseCommand):
    """
    Importe les id et les types de bâtiments Open Street Map du fichier fourni dans la base de données. Le fichier à fournir doit être celui 
    créé par la fonction appariement_osm.
    """
    help = ''

    def add_arguments(self, parser):
        parser.add_argument('path', nargs=1, type=str,
                            help='Fichier JSON contenant pour chaque orgue sa codification, son id OSM et son type OSM.')

    def handle(self, *args, **options):
        if not os.path.exists(options['path'][0]):
            return "Path does not exist"
        with open(options['path'][0], "r", encoding="utf-8") as f:
            print('Lecture JSON et import des identifiants OSM des orgues.')
            rows = json.load(f)
            for row in tqdm(rows):
                codification = row['codification']
                print(codification)
                orgue = Orgue.objects.get(codification=codification)
                orgue.osm_id = row['id']
                orgue.osm_type = row['type']
                orgue.save()