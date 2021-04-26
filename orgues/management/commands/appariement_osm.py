from orgues.models import Orgue
from django.core.management.base import BaseCommand
from tqdm import tqdm
import requests
import json

import orgues.management.utilsorgues.correcteurorgues as co

AMENITY = ['place_of_worship', 'monastery', 'music_school', 'college', 'school', 'clinic', 'hospital']
BUILDING = ['yes', 'cathedral', 'chapel', 'church', 'monastery', 'religious', 'shrine', 'synagogue', 'temple']

"""
Langage de requête Overpass :
https://wiki.openstreetmap.org/wiki/FR:Overpass_API/Overpass_QL#Union

Test :
https://overpass-turbo.eu/
"""


class Command(BaseCommand):
    """
    Cherche id_osm et id_type pour tous les orgues pour lesquels ils ne sont pas définis en utilisant
    comme critères le code INSEE et le nom de l'édifice.
    Les résultats sont retournés sous forme d'un fichier json.

    L'API Overpass ne peut recevoir plus de 10 000 requêtes par jour.
    """
    help = 'Appariement des édifices avec la base de données osm'

    def __init__(self):
        self.liste_appariements = []

    def handle(self, *args, **options):
        for orgue in tqdm(Orgue.objects.all()):
            # On ne recherche que les osm_id qui ne sont pas déjà présents (et pour lesquels on a bien un code INSEE):
            if orgue.code_insee and not orgue.osm_id:
                self.tenter_appariement_osm_via_nom(orgue)
        with open('appariements_osm.json', 'w') as f:
            json.dump(self.liste_appariements, f)

    def tenter_appariement_osm_via_nom(self, orgue):        
        nom_edifice,type_edifice = co.detecter_type_edifice(orgue.edifice)
        overpass_url = "http://overpass-api.de/api/interpreter"
        overpass_query = "[out:json]; area[boundary=administrative]['ref:INSEE']['ref:INSEE'={}] -> .commune;".format(int(orgue.code_insee))
        filtre_type_commune = "[amenity~'{}'][building~'{}'] (area.commune)".format("|".join(AMENITY), "|".join(BUILDING))
        overpass_query +=" ((way[name~'{}',i] {}; ".format(orgue.edifice.capitalize(), filtre_type_commune) #On met ~ au lieu de = pour que l'option Insensible à la casse ",i" fonctionne
        overpass_query +=" relation[name~'{}',i] {}; ); ._;)->.a; ".format(orgue.edifice, filtre_type_commune)

        overpass_query +="if (a.count(wr)>0){ .a out; } else {"
        overpass_query +=" ((way[name~'{}',i] {}; ".format(nom_edifice, filtre_type_commune)
        overpass_query +=" relation[name~'{}',i] {}; ); ._;)->.b; ".format(nom_edifice, filtre_type_commune)
        overpass_query += ".b out; }"
        

        #L'Overpass_query fait un premier test sur le nom exact (avec insensibilité à la casse),
        #puis, en l'absence de résultat, teste en enlevant le type d'édifice dans la requête sur name
        #
        # Attention : - il existe de rares édifices OSM qui n'ont pas d'attribut "building".
        #            >> A vérifier si certains orgues ne peuvent pas être apparier.
        #             - Requête sur way. Faut-il repasser sur nwr pour inclure les édifices de type node ?
        response = requests.get(overpass_url, params={'data': overpass_query})

        # Erreur dans la requête QL Overpass
        if response.status_code != 200:
            print("Echec de la requête QL Overpass avec l'orgue : {}".format(orgue))
            print("Status code : {}".format(response.status_code))
            print("")
        # Résultats
        else:
            data = response.json()
            elements = data['elements']
            # Si un seul appariement, c'est gagné :
            if len(elements) == 1:
                elem = elements[0]
                print("Un seul objet OSM possibles pour cet orgue : {} {} {} {}"
                      .format(elem['tags']['name'], elem['type'], elem['tags']['amenity'], elem['tags']['building']))
                self.liste_appariements.append({"codification": orgue.codification,
                                                "type": data['elements'][0]['type'],
                                                "id": data['elements'][0]['id']})

            # Si plusieurs appariements, pour l'instant on ne fait que les sortir en traces :
            elif len(elements) > 1:
                for elem in data['elements']:
                    print("Plusieurs objets OSM possibles pour cet orgue : {} {} {} {}"
                          .format(elem['tags']['name'], elem['type'], elem['tags']['amenity'], elem['tags']['building']))

            # Si aucun appariement strict
            else:
                print("Aucun chemin ou relation OSM à apparier : {}".format(orgue))
                print ("Code INSEE de la commune : ", orgue.code_insee)
                print("Nom sans type d'édifice : ", nom_edifice)
        return

    def tenter_appariement_osm_via_codif(self, orgue):
        """
        :param list_osm:
        :param edifice:
        :return:
        Fonction d'appariement utilisant le code d'une orgue (Elliot)
        # Elle codifie le nom de l'edifice recherché et les noms de tous les édifices de la commune, afin de trouver des appariements.
        # entrée :
        #    la liste d'objets OSM de la commune récupérés : [objets osm]
        #           > pour avoir le nom du premier objet, list_osm[0]['name']
        #    le nom de l'édifice de l'orgue : str
        #sortie : une liste d'objets OSM plus réduite (il ne faut pas juste le nom, il faut l'objet osm complet)


        Rappel sur la codification :
        FR-<codeINSEE sur 5 car.>-<code commune sur 5 car.>-<code édifice sur 6 car.>-<index édifice sur 1 car.>-<désignation orgue sur 1 car.>
        Quelques remarques :
        - en passant par le code de l'orgue on est sûr de cibler la bonne commune (code INSEE)
        - en passage par le code de l'orgue on est presque sûr mais pas sûr de cibler le bon édifice (il n'y a pas bijection :
        ex : Saint-Martin et Sainte-Martine on le même code 'STMART')
        - il est très rare que l'index de l'édifice soit autre chose que 1 (i.e. il est très rare d'avoir plusieurs édifices sur la même commune avec un même nom)
        - il est courant d'avoir deux orgues ou plus dans le même édifice


        PSEUDO-CODE A IMPLEMENTER :

        - Lancer une requête OVERPASS QL pour trouver tous les édifices qui correspondent aux listes AMENITY et BUILDING
        - Comparer le nom des édifices du résultat de cette requête, une fois codifié, avec le code de l'orgue (cf. rappel ci-dessus pour construire l'heuristique de comparison).
        - Si une seule correspondance, dire que c'est OK et la conserver, si plusieurs, les afficher en traces, si aucune, erreur.
        """
        pass
        return

