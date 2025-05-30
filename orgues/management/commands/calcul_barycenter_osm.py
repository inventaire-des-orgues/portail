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
        overpass_url = "http://overpass-api.de/api/interpreter"
        overpass_query = """[out:json];{}({});(._;>;);out;""".format(orgue.osm_type, orgue.osm_id)

        done = False
        while not done:
            response = requests.get(overpass_url,params={'data': overpass_query})
            if response.status_code == 429 or response.status_code == 504:
                time.sleep(30)
            else:
                done = True

        if response.status_code == 200:
            data = response.json()
            if len(data['elements']) > 0:
                latitude, longitude, coef=self.calculer_barycentre(orgue, data['elements'], orgue.osm_type)
                liste_coordonnees.append({"codification" : orgue.codification, "latitude" : latitude, "longitude" : longitude})
        return liste_coordonnees

    def calculer_barycentre(self, orgue, list_osm, osm_type):
        """
        Calcule le barycentre d'un objet osm de type osm_type. list_osm est la liste des éléments constituant cet objet.
        """
        if osm_type == 'way' or osm_type == 'relation':
            list_osm = list_osm[0:-1]
        sum_latitude = 0
        sum_longitude = 0
        sum_coef = 0
        for element in list_osm:
            if element['type'] == "node":
                sum_latitude += element['lat']
                sum_longitude += element['lon']
                sum_coef += 1
            else:
                overpass_url = "http://overpass-api.de/api/interpreter"
                overpass_query = """[out:json];{}({});(._;>;);out;""".format(element['type'], element['id'])

                done = False
                while not done:
                    response = requests.get(overpass_url, params={'data': overpass_query})
                    if response.status_code == 429 or response.status_code == 504:
                        time.sleep(30)
                    else:
                        done = True

                if response.status_code == 200 :
                    data = response.json()
                    latitude, longitude, coef = self.calculer_barycentre(orgue, data['elements'], element['type'])
                    sum_latitude += latitude*coef
                    sum_longitude += longitude*coef
                    sum_coef += coef
        return sum_latitude/sum_coef, sum_longitude/sum_coef, sum_coef