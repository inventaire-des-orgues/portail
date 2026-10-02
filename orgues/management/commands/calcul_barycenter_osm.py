from orgues.models import Orgue
from django.core.management.base import BaseCommand
from tqdm import tqdm
import requests
import json
import time

class Command(BaseCommand):
    """
    Calcule la position latitude/longitude pour tous les orgues dont les champs id_osm et id_type sont définis et 
    les renvoie dans un fichier json. 
    Par défaut, le calcul ne concerne que les orgues pour lesquels  les champs latitude et longitude ne sont pas renseignés. 
    Pour écraser ces deux champs, utiliser l'option --calculall.
    L'API Overpass ne peut recevoir plus de 10000 requêtes par jour.
    """
    help = 'Calcul barycenters of osm object'

    def add_arguments(self, parser):
        parser.add_argument('--calculall',
                help="Calcule toutes les position latitude/longitude de l'orgue.")

    def handle(self, *args, **options):
        liste_coordonnees = []
        for orgue in tqdm(Orgue.objects.all()):
            if (orgue.osm_type and orgue.osm_id):
                if options['calculall']:
                    liste_coordonnees = self.mettre_a_jour_barycentre(orgue, liste_coordonnees)
                else:
                    if orgue.latitude == None or orgue.longitude == None:
                        liste_coordonnees = self.mettre_a_jour_barycentre(orgue, liste_coordonnees)
        with open('coordonnees_osm.json', 'w') as f:
            json.dump(liste_coordonnees, f)

    def mettre_a_jour_barycentre(self, orgue, liste_coordonnees):
        if orgue.osm_type=="way" or orgue.osm_type=="relation":
            url = f"https://www.openstreetmap.org/api/0.6/{orgue.osm_type}/{orgue.osm_id}/full.json"
        else:#Node
            url = f"https://www.openstreetmap.org/api/0.6/{orgue.osm_type}/{orgue.osm_id}.json"

        headers = {
            'User-Agent': 'InventairedesOrgues'
        }

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            latitudes = []
            longitudes = []
            if orgue.osm_type == 'way' or orgue.osm_type == 'relation':
                for node in data["elements"]:
                    if node['type'] == "node":
                        latitudes.append(node['lat'])
                        longitudes.append(node['lon'])
                if len(latitudes) > 0 and len(longitudes) > 0:
                    latitude = sum(latitudes) / len(latitudes)
                    longitude = sum(longitudes) / len(longitudes)
                    liste_coordonnees.append({"codification" : orgue.codification, "latitude" : latitude, "longitude" : longitude})
            else:
                latitude = data["elements"][0]['lat']
                longitude = data["elements"][0]['lon']
                liste_coordonnees.append({"codification" : orgue.codification, "latitude" : latitude, "longitude" : longitude})
        else:
            print(f"Erreur lors de la récupération des données OSM pour l'orgue {orgue} {orgue.codification} :")
            print(f"OSM type: {orgue.osm_type}, OSM id: {orgue.osm_id}")
            print(f"Erreur: {response.status_code}, response: {response.text}")
            print(url)
        time.sleep(1)  # Pause d'une seconde pour éviter de surcharger le serveur
        return liste_coordonnees
