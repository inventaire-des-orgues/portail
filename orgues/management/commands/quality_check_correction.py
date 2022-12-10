import requests
import time
from django.core.management.base import BaseCommand
import logging

from orgues.models import Orgue


overpass_url = "http://overpass-api.de/api/interpreter"
logger_echec_requete = logging.getLogger('echecrequete')


class Command(BaseCommand):
    help = 'Contrôle des données'

    def handle(self, *args, **options):

        for orgue in Orgue.objects.all():
            # Désignation
            if orgue.designation is None:
                orgue.designation = "orgue"
                print("INFO : L'orgue {} a une nouvelle désignation : {}".format(orgue, orgue.designation))
                orgue.save()

            #Nom de l'édifice
            if len(orgue.edifice) <= 6 and orgue.edifice != 'temple' and orgue.edifice != 'mairie':
                print("WARN : {} {} édifice incomplet pour l'orgue {}".format(orgue.codification, orgue.edifice, orgue))
                if orgue.osm_type is None or orgue.osm_id is None:
                    print("WARN : pas de type ou d'id OSM pour faire la requête")
                else :
                    overpass_query = "[out:json];{}({})->.a;.a out;".format(orgue.osm_type, orgue.osm_id)
                    done = False
                    while not done:
                        response = requests.get(overpass_url, params={'data': overpass_query})
                        if response.status_code == 429 or response.status_code == 504:
                            time.sleep(30)
                        else:
                            done = True

                    # Erreur dans la requête QL Overpass
                    if response.status_code != 200:
                        logger_echec_requete.error("Echec de la requête QL Overpass avec l'orgue {} dans la commune {}. Status code : {}".format(orgue, orgue.code_insee, response.status_code))
                        if response.status_code == 400:
                            logger_echec_requete.info(overpass_query)
                    # Résultats
                    else:
                        data = response.json()
                        if "name" in data["elements"][0]["tags"]:
                            orgue.edifice = data["elements"][0]["tags"]["name"]
                            orgue.save()
                            print("INFO : L'orgue {} ({}) a un nouvel édifice : {}".format(orgue, orgue.codification, orgue.edifice))
                        else:
                            print("WARN : Aucun nom n'a été trouvé pour l'orgue")
                print("")