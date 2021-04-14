from orgues.models import Orgue
from django.core.management.base import BaseCommand
from tqdm import tqdm
import requests
import json

class Command(BaseCommand):
    """
    Cherche id_osm et id_type pour tous les orgues pour lesquels ils ne sont pas définis en utilisant
    comme critères le code INSEE et le nom de l'édifice.
    Les résultats sont retournés sous forme d'un fichier json.

    L'API Overpass ne peut recevoir plus de 10000 requêtes par jour.
    """
    help = 'Appariement des édifices avec la base de données osm'

    l_amenity = "place_of_worship|monastery|music_school"
    l_building = "cathedral|chapel|church|monastery|mosque|presbytery|religious|shrine|synagogue|temple"

    def handle(self, *args, **options):
        liste_appariements = []
        for orgue in tqdm(Orgue.objects.all()):
            if (orgue.code_insee) and not (orgue.osm_id):
                liste_appariements = self.mettre_a_jour_appariement(orgue, liste_appariements)
        with open('appariements_osm.json', 'w') as f:
            json.dump(liste_appariements, f)

    def mettre_a_jour_appariement(self, orgue, liste_appariements):
        overpass_url = "http://overpass-api.de/api/interpreter"
        overpass_query = """[out:json]; area[boundary=administrative]["ref:INSEE"]["ref:INSEE"={}] -> .searchArea; ( nwr [name={}] [amenity~{}] (area.searchArea);) ;(._;>;);out;""".format(int(orgue.code_insee), orgue.edifice, l_amenity)
        response = requests.get(overpass_url,params={'data': overpass_query})
        if response.status_code == 200:
            data = response.json()
            if len(data['elements']) == 0: #Aucun appariement strict
                #Lancer une requête sur la ville pour récupérer tous les édifices susceptibles d'héberger un orgue
                overpass_query_town = """[out:json]; area[boundary=administrative]["ref:INSEE"]["ref:INSEE"={}] -> .searchArea; ( nwr [amenity~{}] (area.searchArea);) ;(._;>;);out;""".format(int(orgue.code_insee), l_amenity)
                response_town = requests.get(overpass_url,params={'data': overpass_query_town})
                if response_town.status_code == 200:
                    data_town = response.json()

                    if len(data_town['elements']) == 0: #Aucun objet osm adapté
                        print("Erreur dans la requête INSEE avec l'orgue : ", orgue)
                        print("La commune ne comporte pas d'objet OSM susceptibles d'héberger un orgue")
                        print("")
                    else:
                        #Fonction d'appariement avec codification  
                        AC=self.appariement_codif(data_town['elements'], orgue.edifice)

                        if len(AC) ==0: #Aucun appariement codifié
                            print("Erreur dans la requête INSEE avec l'orgue : ", orgue)
                            print("La commune ne comporte pas d'objet OSM correspondant à l'édifice : ", orgue.edifice)
                            print("Liste des objets de la commune : ")
                            for elem in data_town['elements']:
                                print(elem['name'])
                        elif len(AC) == 1 : # 1 appariement codifié, c'est bon !
                            print("Appariement codifié réussi entre "+orgue.edifice+" et "+AC[0]['name'])
                            print("")
                            liste_appariements.append({"codification" : orgue.codification, "type" : AC[0]['type'], "id" : AC[0]['id']})
                        else: #Trop d'appariements codifiés pour le même édifice
                            print("Erreur dans l'appariement codifié pour l'édifice "+orgue.edifice+"de l'orgue : ", orgue)
                            print("La commune ne comporte pas d'objet OSM correspondant à l'édifice : ", orgue.edifice)
                            print("Liste des objets de la commune appariés : ")
                            for elem in AC:
                                print(elem['name'])                        

                else: #Erreur dans la requête QL Overpass
                    print("Erreur dans la requête INSEE avec l'orgue : ", orgue)
                    print("Status code : ", response.status_code)
                    print("")


            elif len(data['elements']) == 1: # 1 seul appariement
                liste_appariements.append({"codification" : orgue.codification, "type" : data['elements'][0]['type'], "id" : data['elements'][0]['id']})

            else: #Plusieurs appariements
                #Filtrage par l'attribut building afin de supprimer les sous-éléments captés par la requête
                data_filtre = []
                for elem in data['elements']:
                    if (elem['building']):
                        if elem['building'] in l_building:
                            data_filtre.append({ "type" : elem['type'], "id" : elem['id'], "building" : elem['building']  } )
                
                if len(data_filtre) ==1: #Appariement avec 1 seul objet type building
                    liste_appariements.append({"codification" : orgue.codification, "type" : data_filtre[0]['type'], "id" : data_filtre[0]['id']})
                else: # Soit toujours trop d'appariement avec le building, soit aucun appariement avec le critère building
                    print("Multi-appariement problématique pour l'orgue : ", orgue)
                    for elem in data['elements']:
                        print("Appariement possible : ", elem)
                        print("")


        else: #Erreur dans la requête QL Overpass
            print("Erreur avec l'orgue : ", orgue)
            print("Status code : ", response.status_code)
            print("")
        return liste_appariements



    def appariement_codif(self, list_osm, edifice):
        #Fonction d'appariement avec codification  (Elliot)
        #Elle codifie le nom de l'edifice recherché et les noms de tous les édifices de la commune, afin de trouver des appariements.
        #entrée : 
        #    la liste d'objets OSM de la commune récupérés : [objets osm]
        #           > pour avoir le nom du premier objet, list_osm[0]['name']
        #    le nom de l'édifice de l'orgue : str
        #sortie : une liste d'objets OSM plus réduite (il ne faut pas juste le nom, il faut l'objet osm complet)


        return 0

