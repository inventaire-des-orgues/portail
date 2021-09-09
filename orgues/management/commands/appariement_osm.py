from orgues.models import Orgue
from django.core.management.base import BaseCommand
from tqdm import tqdm
import requests
import json
import time
import re
from django.db.models import Q
import logging

import orgues.utilsorgues.correcteurorgues as co
import orgues.utilsorgues.tools.generiques as gen
import orgues.utilsorgues.codification as codif

#Initialisation de certaines variables utiles dans plusieurs méthodes
AMENITY = ['place_of_worship', 'monastery', 'music_school', 'college', 'school', 'clinic', 'hospital']
BUILDING = ['yes', 'cathedral', 'chapel', 'church', 'monastery', 'religious', 'shrine', 'synagogue', 'temple']
filtre_type_commune = "[amenity~'{}'][building~'{}'] (area.commune)".format("|".join(AMENITY), "|".join(BUILDING))
overpass_url = "http://overpass-api.de/api/interpreter"
        
logger_echec_requete = logging.getLogger('echecrequete')
logger_appariement_reussite = logging.getLogger('appariementreussi')
logger_appariement_multiple = logging.getLogger('appariementmultiple')
logger_appariement_correlation = logging.getLogger('appariementcorrelation')
logger_appariement_nul = logging.getLogger('appariementnul')



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
        self.compte_echec_requete = 0
        self.compte_appariement_direct = 0
        self.compte_appariement_multiple = 0
        self.compte_appariement_correlation = 0
        self.compte_appariement_nul = 0      
        
    def add_arguments(self, parser):
        parser.add_argument('dep', nargs=1, type=str,
                            help='Département à traiter. "all" pour traiter toute la base de données')

    def handle(self, *args, **options):
        #Récupération des orgues à traiter
        if options['dep'][0] =='all':
            BDO = Orgue.objects.all()
        else :
            BDO = Orgue.objects.filter(code_departement=options['dep'][0])
        
        # On ne recherche que les osm_id qui ne sont pas déjà présents (et pour lesquels on a bien un code INSEE):
        BDO = BDO.filter(Q(code_insee__isnull=False) & Q(osm_id__isnull=True)).distinct()
        
        for orgue in tqdm(BDO):
            self.tenter_appariement_osm_via_nom(orgue)
            
        logger_echec_requete.info("Nombre d'orgues : {}".format(self.compte_echec_requete))
        logger_appariement_reussite.info("Nombre d'orgues : {}".format(self.compte_appariement_direct))
        logger_appariement_multiple.info("Nombre d'orgues : {}".format(self.compte_appariement_multiple))
        logger_appariement_correlation.info("Nombre d'orgues : {}".format(self.compte_appariement_correlation))
        logger_appariement_nul.info("Nombre d'orgues : {}".format(self.compte_appariement_nul))
        
        #Ecriture des fichiers de résultats
        with open("orgues/temp/appariements_osm_"+options['dep'][0]+".json", 'w') as f:
            json.dump(self.liste_appariements, f)



    def tenter_appariement_osm_via_nom(self, orgue):
        #Récupération du nom de l'édifice de l'orgue
        nom_edifice,type_edifice = co.detecter_type_edifice(orgue.edifice)
        if nom_edifice!="":
            #Décomposition du nom en une liste de mots
            decompo = re.split("-| |'|’",nom_edifice)
        else :
            #Cas particulier des édifices sans dédicaces (par exemple, "temple réformé" ou "chapelle du lycée")
            #On prend alors le nom complet plutôt que la dédicace.
            #Décomposition du nom en une liste de mots
            decompo = re.split("-| |'|’",orgue.edifice)
        

        #Requête Overpass
        #Après délimitation de la zone de recherche sur le territoire de la commune, 
        #l'Overpass_query fait un premier test sur le nom exact (avec insensibilité à la casse),
        #puis, en l'absence de résultat, effectue un second test en cherchant de manière séparé les mots composant le nom.
        overpass_query = "[out:json]; area[boundary=administrative]['ref:INSEE']['ref:INSEE'={}] -> .commune;".format(orgue.code_insee)
        
        overpass_query +=" ((wr[name~{},i] {}; ); ._;)->.a; ".format('"'+orgue.edifice.capitalize()+'"', filtre_type_commune)
        overpass_query +="if (a.count(wr)>0){ .a out; } else {"
        
        overpass_query +=" ((wr"
        for mot in decompo:
            if len(mot) > 2: #Filtre pour ne pas rechercher les mots de liaisons (de, l, la, en...)
                overpass_query +=" [name~'{}',i]".format(mot)
        overpass_query +=" {}; ); ._;)->.b; ".format(filtre_type_commune)
        overpass_query += ".b out; }"
        
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
            self.compte_echec_requete += 1
            if response.status_code == 400:
                logger_echec_requete.info(overpass_query)
            logger_echec_requete.info("")
        # Résultats
        else:
            self.traitement_reponse_osm(response, orgue)

    def traitement_reponse_osm(self, response, orgue):
        data = response.json()
        elements = data['elements']
        if len(elements) == 1:# Si un seul élément dans data, il y a un appariement unique, c'est donc validé :
            logger_appariement_reussite.info("Appariement direct")
            self.reponse_unique(elements, orgue)
        elif len(elements) > 1:# Si plusieurs appariements, pour l'instant on ne fait que les sortir en traces :
            logger_appariement_reussite.info("Appariement réponse multiple")
            self.traitement_reponse_multiple(elements, orgue)     
        else:# Si aucun appariement 
            #Tentative d'appariement partiel (méthode à part)
            logger_appariement_reussite.info("Appariement partiel")
            self.tenter_appariement_partiel_osm_via_nom(orgue) 
    
    def reponse_unique(self, elements, orgue):
        logger_appariement_reussite.info("L'orgue {} a été associé à l'édifice {} d'id {} et de type {}".format(orgue, elements[0]['tags']['name'], elements[0]['id'], elements[0]['type']))
        logger_appariement_reussite.info("")
        self.compte_appariement_direct += 1
        self.liste_appariements.append({"codification": orgue.codification, "type": elements[0]['type'], "id": elements[0]['id']})
        
    def traitement_reponse_multiple(self, elements, orgue):
        #Découpe du nom de l'édifice de l'orgue
        dec_Orgue = re.split("-| |'|’",orgue.edifice.lower())
        dec_Orgue = [i for i in dec_Orgue if len(i) >2]
        resultat = []
        for elem in elements:
            if  'tags' in elem and  'name' in elem['tags']:
                #Découpe du nom du bâtiment OSM
                dec_OSM = re.split("-| |'|’",elem['tags']['name'].lower())
                dec_OSM = [i for i in dec_OSM if len(i) >2]

                #Calcul du taux (entre 0 et 1) de correspondance pour le nom de l'édifice de l'orgue
                # (taux de présence des mots du nom de l'édifice de l'orgue dans le nom du bâtiment OSM)
                cor_org = 0
                for mot in dec_Orgue:
                    if mot in dec_OSM:
                        cor_org += 1/len(dec_Orgue)

                #Calcul du taux (entre 0 et 1) de correspondance pour le nom de l'édifice de l'orgue
                # (taux de présence des mots du nom du bâtiment OSM dans le nom de l'édifice de l'orgue)
                cor_osm = 0
                for mot in dec_OSM:
                    if mot in dec_Orgue:
                        cor_osm += 1/len(dec_OSM)

                #Calcul du taux moyen de correspondance
                cor_moy = (cor_org+cor_osm)/2
                if cor_moy>0.6:
                    #Si le taux est assez important, le bâtiment OSM est conservé dans une liste d'appariement partiel
                    resultat.append({"Correspondance": cor_moy, "elem":elem})
                    logger_appariement_multiple.info("L'orgue {} a une corrélation de {} avec {}".format(orgue, cor_moy, elem['tags']['name']))
        if len(resultat) != 0:
            maximum = max([edifice["Correspondance"] for edifice in resultat])
            nb_edifice = len([i for i in resultat if i["Correspondance"] == maximum])
            edifices_max = [edifice["elem"] for edifice in resultat if edifice["Correspondance"] == maximum]
            if nb_edifice == 1:
                self.liste_appariements.append({"codification": orgue.codification, "type": edifices_max[0]['type'], "id": edifices_max[0]['id']})
                logger_appariement_reussite.info("L'orgue {} a été associé à l'édifice {} d'id {} et de type {}".format(orgue, edifices_max[0]['tags']['name'], edifices_max[0]['id'], edifices_max[0]['type']))
                logger_appariement_reussite.info("")
                self.compte_appariement_multiple += 1
            else:
                logger_appariement_multiple.info("Il y a au moins deux possibilités avec l'orgue {}. On teste la corrélation".format(orgue))
                self.correlation(edifices_max, orgue)
        else:
            logger_appariement_multiple.info("Il n'y a aucune possibilité avec l'orgue {}. On teste la corrélation".format(orgue))
            self.correlation(elements, orgue)
    
    def correlation(self, elements, orgue):
        correspondances = []
        for elem in elements:
            if  'tags' in elem and  'name' in elem['tags']:
                edifice_test, type_edifice_test = co.reduire_edifice(elem['tags']['name'], orgue.commune)
                codification_test = codif.codifier_instrument(orgue.code_insee, orgue.commune, edifice_test, type_edifice_test, '')
                correlation_codification = self.calcul_correlation_codification(orgue.codification, codification_test)
                if correlation_codification <= 4:
                    correspondances.append({"Correlation": correlation_codification, "elem":elem})
                    logger_appariement_correlation.info("L'orgue {} a une corrélation de {} avec {}".format(orgue, correlation_codification, elem['tags']['name']))
        if len(correspondances) != 0:
            minimum = min([edifice["Correlation"] for edifice in correspondances])
            nb_edifice = len([i for i in correspondances if i["Correlation"] == minimum])
            edifices_max = [edifice["elem"] for edifice in correspondances if edifice["Correlation"] == minimum]
            if nb_edifice == 1 and minimum <= 2:
                logger_appariement_reussite.info("L'orgue {} a été associé à l'édifice {} d'id {} et de type {}".format(orgue, edifices_max[0]['tags']['name'], edifices_max[0]['id'], edifices_max[0]['type']))
                logger_appariement_reussite.info("")
                self.compte_appariement_correlation += 1
                self.liste_appariements.append({"codification": orgue.codification, "type": edifices_max[0]['type'], "id": edifices_max[0]['id']}) 
            else: 
                logger_appariement_nul.error("Pas d'appariement possible pour {}.".format(orgue))
                logger_appariement_nul.info("")
                self.compte_appariement_nul += 1  
        else: 
            logger_appariement_nul.error("Pas d'appariement possible pour {}.".format(orgue))
            logger_appariement_nul.info("")
            self.compte_appariement_nul += 1
            
    def calcul_correlation_codification(self, codif1, codif2):
        erreur = 0
        if len(codif1) != len (codif2):
            logger_appariement_correlation.error("Taille de codif différente : {}, {}".format(codif1, codif2))
            return 10
        else:
            for i in range(len(codif1)):
                if codif1[i] != codif2[i]:
                    erreur += 1
        return erreur    
    
    def tenter_appariement_partiel_osm_via_nom(self, orgue):
        """
        Fonction d'appariement utilisant les noms des édifices de sorte à obtenir un pourcentage d'appariement entre l'édifice de l'orgue
        et les édifices religieux issus d'OSM de la même commune.

        Le but est de chercher à associer des cas comme "église Notre-Dame-de-l'Assomption" et "église Notre-Dame" (ce qui donnerait 87,5% de correspondance moyenne)
        """
        #Récupération des édifices potentiels de la commune
        overpass_query = "[out:json]; area[boundary=administrative]['ref:INSEE']['ref:INSEE'={}] -> .commune;".format(orgue.code_insee)
        overpass_query +=" ((wr {}; ); ._;)->.a; (.a;.a >;)->.a; .a out;".format(filtre_type_commune)
        #L'Overpass_query récupère tous les édifices susceptibles de comporter un orgue dans la commune où se trouve l'orgue
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
            self.compte_echec_requete += 1
            if response.status_code == 400:
                logger_echec_requete.info(overpass_query)
            logger_echec_requete.info("")
        # Résultats
        else:
            data = response.json()
            self.traitement_reponse_multiple(data['elements'], orgue)
            



