from orgues.models import Orgue
from django.core.management.base import BaseCommand
from tqdm import tqdm
import requests
import json
import time
import csv
from django.db.models import Q

class Command(BaseCommand):
    """
    Renvoie sous format csv la liste des orgues qui n'ont pas d'identifiants Open Street Map et qui n'ont pas de localisation.
    Si l'argument lonlat vaut True, les orgues renvoyés sont ceux qui ne disposent ni de l'identifiant OSM, ni d'une localisation en latitude/longitude
    Si l'argument lonlat vaut False, les orgues renvoyés sont ceux qui ne disposent pas de l'identifiant OSM
    """

    def add_arguments(self, parser):
        parser.add_argument('lonlat', help="Si présent, renvoie la liste des orgues dont les latitudes et longitudes ne sont pas renseigné.")

    def handle(self, *args, **options):
        bdo = Orgue.objects.all()
        bdo = bdo.filter(Q(osm_id__isnull=True) or Q(osm_type__isnull=True)).distinct()
        if options['lonlat']:
            bdo = bdo.filter(Q(latitude__isnull=True) or Q(longitude__isnull=True)).distinct()

        with open('organ_without_lonlat.csv', 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, delimiter=';')
            writer.writerow(["Codification", "Edifice", "Commune", "Code Insee", "Département", "lonlat"])
            for organ in bdo:
                liste = [organ.codification, organ.edifice, organ.commune, organ.code_insee, organ.departement]
                if organ.latitude == None or organ.longitude == None:
                    liste.append("Non renseigné")
                else:
                    liste.append("Renseigné")
                writer.writerow(liste)
