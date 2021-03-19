from orgues.models import Orgue
from django.core.management.base import BaseCommand
from tqdm import tqdm
import requests


class Command(BaseCommand):
    """
    Calcule la position latitude/longitude pour tous les orgues dont les champs id_osm et id_type sont définis. Par défaut, le calcul ne concerne que les orgues pour lesquels  les champs latitude et longitude ne sont pas renseignés. Pour écraser ces deux champs, utiliser l'option --ecrase ECRASE.
    L'API Overpass ne peut recevoir plus de 10000 requêtes par jour.
    """
    help = 'Calcul barycenters of osm object'

    def add_arguments(self, parser):
        parser.add_argument('--ecrase',
                help="Ecrase la position latitude/longitude de l'orgue.")

    def handle(self, *args, **options):
        for orgue in tqdm(Orgue.objects.all()):
            if (orgue.osm_type and orgue.osm_id):
                if options['ecrase']:
                    self.mettre_a_jour_barycentre(orgue)
                else:
                    if orgue.latitude == None or orgue.longitude == None:
                        self.mettre_a_jour_barycentre(orgue)

    def mettre_a_jour_barycentre(self, orgue):
        overpass_url = "http://overpass-api.de/api/interpreter"
        overpass_query = """[out:json];{}({});(._;>;);out;""".format(orgue.osm_type, orgue.osm_id)
        response = requests.get(overpass_url,params={'data': overpass_query})
        if response.status_code == 200:
            data = response.json()
            if len(data['elements']) > 0:
                orgue.latitude, orgue.longitude, coef=self.calculer_barycentre(orgue, data['elements'], orgue.osm_type)
                orgue.save()
        else:
            print("Erreur avec l'orgue : ", orgue)
            print("Status code : ", response.status_code)
            print("")

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
                response = requests.get(overpass_url, params={'data': overpass_query})
                if response.status_code == 200:
                    data = response.json()
                    latitude, longitude, coef = calculer_barycentre(orgue, data['elements'], element['type'])
                    sum_latitude += latitude*coef
                    sum_longitude += longitude*coef
                    sum_coef += coef
        return sum_latitude/sum_coef, sum_longitude/sum_coef, sum_coef