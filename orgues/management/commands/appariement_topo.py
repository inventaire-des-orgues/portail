from orgues.models import Orgue
from django.core.management.base import BaseCommand
from tqdm import tqdm
import requests
import json
import re
from django.db.models import Q
import logging

import orgues.utilsorgues.correcteurorgues as co
import orgues.utilsorgues.codification as codif

logger_echec_requete = logging.getLogger('echecrequete')
logger_appariement_reussite = logging.getLogger('appariementreussi')
logger_appariement_multiple = logging.getLogger('appariementmultiple')
logger_appariement_correlation = logging.getLogger('appariementcorrelation')
logger_appariement_nul = logging.getLogger('appariementnul')

class Command(BaseCommand):
    """
    Cherche dans la BD Topo les bâtiments. Si le bâtiment est trouvé, alors renvoie le barycentre du bâtiment.
    Les résultats sont retournés sous forme d'un fichier json.
    """
    help = 'Appariement des édifices avec la BD Topo'

    def __init__(self):
        self.coordonnees = []
        self.compte_echec_requete = 0
        self.compte_appariement_direct = 0
        self.compte_appariement_multiple_reussite = 0
        self.compte_appariement_correlation_reussite = 0
        self.compte_appariement_correlation_echec = 0
        self.compte_appariement_direct_sans_nom_reussite = 0  
        self.compte_appariement_direct_sans_nom_echec = 0 
        
    
    def handle(self, *args, **options):
        # Récupération des orgues à traiter
        bdo = Orgue.objects.all()
        #bdo = bdo.filter(Q(code_insee__isnull=False) & Q(osm_id__isnull=True) & Q(region="Île-de-France")).distinct()
        bdo = bdo.filter(Q(code_insee__isnull=False) & Q(osm_id__isnull=True)).distinct()

        with open("BD_TOPO_batiments.geojson", "r", encoding="utf-8") as f:
            logger_appariement_reussite.info('Lecture du fichier JSON')
            rows = json.load(f)
        
            for orgue in tqdm(bdo):
                self.tenter_appariement_osm_via_nom(orgue, rows["features"])

        print("compte_appariement_direct : {}".format(self.compte_appariement_direct))
        print("compte_appariement_multiple_reussite : {}".format(self.compte_appariement_multiple_reussite))
        print("compte_appariement_correlation_reussite : {}".format(self.compte_appariement_correlation_reussite))
        print("compte_appariement_correlation_echec : {}".format(self.compte_appariement_correlation_echec))
        print("compte_appariement_direct_sans_nom_reussite : {}".format(self.compte_appariement_direct_sans_nom_reussite))
        print("compte_appariement_direct_sans_nom_echec : {}".format(self.compte_appariement_direct_sans_nom_echec))
        
        with open("orgues/temp/appariements_topo.json", 'w') as f:
            json.dump(self.coordonnees, f)

    def correlation_nom(self, decompo_query, nom_topo):
        """
        Renvoie True s'il y a un mot en commun dans decompo_query et nom_topo
        """
        if nom_topo:
            nom_topo_decompo = re.split("-| |'|’", nom_topo.lower())
            for mot in decompo_query:
                if mot.lower() in nom_topo_decompo:
                    return True
        return False

    def trouver_nature_batiment(self, decompo_query):
        """
        Retourne trois booléens qui caractérisent le type de bâtiment : bâtiment d'enseignement, lieu de culte protestant, lieu de culte chrétien
        """

        mots_enseignement = ['collège', 'lycée', 'école', 'pensionnat', 'conservatoire', 'ecole', 'lycee']
        mots_protestants = ['temple', 'protestant', 'réformé', 'réformée', 'protestante', 'anglicane', 'luthérien' ]
        mots_chretiens = ['église', 'catholique', 'collégiale', 'cathédrale', 'basilique', 'couvent', 'monastère', 'abbaye', 'abbatiale', 'chapelle', 'séminaire']

        for mot in mots_enseignement:
            if mot in decompo_query:
                return True, False, False
        for mot in mots_protestants:
            if mot in decompo_query:
                return False, True, False
        for mot in mots_chretiens:
            if mot in decompo_query:
                return False, False, True
        return False, False, False

    def nature_correspond(self, enseignement, protestant, chretien, proprietes):
        """
        Retourne vrai si la nature du bâtiment dans la BD Topo correspond à celle déterminée dans la fonction trouver_nature_batiment().
        Retourne vrai si le bâtiment n'est ni un bâtiment d'enseignement, ni un lieu de culte protestant ou chrétien.
        """
        if not (enseignement or protestant or chretien):
            return True
        if enseignement and proprietes["CATEGORIE"] == "Science et enseignement":
            return True
        if protestant and proprietes["NAT_DETAIL"] == "Temple protestant":
            return True
        if chretien and proprietes["NATURE"] == "Culte chrétien":
            return True
        return False

    def tenter_appariement_osm_via_nom(self, orgue, rows):
        """
        Récupère les bâtiments de la BD Topo qui peuvent correspondre à l'édifice de l'orgue.
        """
        logger_appariement_reussite.info("")
        logger_appariement_reussite.info("")
        logger_appariement_reussite.info("")
        logger_appariement_reussite.info("")
        logger_appariement_reussite.info("Orgue {} de la ville de {}".format(orgue, orgue.commune))
        # Récupération du nom de l'édifice de l'orgue
        nom_edifice, type_edifice = co.detecter_type_edifice(orgue.edifice)
        if nom_edifice != "":
            # Décomposition du nom en une liste de mots
            decompo = re.split("-| |'|’", nom_edifice)
        else :
            # Cas particulier des édifices sans dédicaces (par exemple, "temple réformé" ou "chapelle du lycée")
            # On prend alors le nom complet plutôt que la dédicace.
            # Décomposition du nom en une liste de mots
            decompo = re.split("-| |'|’", orgue.edifice)

        decompo_query = []
        for mot in decompo:
            if len(mot) > 2: #Filtre pour ne pas rechercher les mots de liaisons (de, l, la, en...)
                decompo_query.append(mot)

        #Récupère le type de bâtiment
        enseignement, protestant, chretien = self.trouver_nature_batiment(re.split("-| |'|’", orgue.edifice.lower()))

        response = []
        for row in rows:
            INSEE_topo = row["properties"]["INSEE_COM"]
            if self.nature_correspond( enseignement, protestant, chretien, row["properties"]):
                if INSEE_topo == orgue.code_insee :
                    if self.correlation_nom(decompo_query, row["properties"]["TOPONYME"]):
                        response.append(row)
        self.traitement_reponse_osm(response, orgue, rows)

    def traitement_reponse_osm(self, response, orgue, rows):
        """
        Oriente la suite de l'algorithme en fonction du nombre de résultats
        """
        if len(response) == 1:  # Si un seul élément dans response, il y a un appariement unique, c'est donc validé :
            logger_appariement_reussite.info("Appariement direct")
            self.compte_appariement_direct += 1
            logger_appariement_reussite.info("L'orgue {} de la ville de {} a été associé à l'édifice {} de la ville de {}".format(orgue, orgue.commune, response[0]["properties"]["TOPONYME"], response[0]["properties"]["NOM"]))
            self.calculer_barycentre(response[0], orgue)
        elif len(response) > 1:  # Si plusieurs possibilités, alors on essaye l'appariement par taux de correspondance entre les deux noms :
            logger_appariement_reussite.info("Appariement réponse multiple")
            self.traitement_reponse_multiple(response, orgue)     
        else:  # Si aucune possibilité, alors on essaye l'appariement uniquement à partir de la fonction du bâtiment
            logger_appariement_reussite.info("Appariement aucune réponse")
            self.tenter_appariement_sans_nom(orgue, rows)

    def calculer_barycentre(self, batiment, orgue):
        """
        Calcule le barycentre du bâtiment
        """
        coords = batiment["geometry"]["coordinates"][0][0]
        latitude = 0
        longitude = 0
        for point in coords:
            longitude += point[0]
            latitude += point[1]
        self.coordonnees.append({"codification" : orgue.codification, "latitude" : latitude / len(coords), "longitude" : longitude / len(coords)})
     
    def traitement_reponse_multiple(self, elements, orgue):
        """
        Recherche le bâtiment le plus adapté à partir d'un taux de correspondance sur les noms
        """
        # Découpe du nom de l'édifice de l'orgue
        dec_orgue = re.split("-| |'|’",orgue.edifice.lower())
        dec_orgue = [i for i in dec_orgue if len(i) >2]
        resultat = []
        for elem in elements:
            logger_appariement_reussite.info("Possibilité : {} de la ville de {}".format(elem["properties"]["TOPONYME"], elem["properties"]["NOM"]))
            nom_topo = elem["properties"]["TOPONYME"]
            if nom_topo:
                # Découpe du nom du bâtiment OSM
                dec_osm = re.split("-| |'|’", nom_topo.lower())
                dec_osm = [i for i in dec_osm if len(i) >2]

                # Calcul du taux (entre 0 et 1) de correspondance pour le nom de l'édifice de l'orgue
                # (taux de présence des mots du nom de l'édifice de l'orgue dans le nom du bâtiment OSM)
                cor_org = 0
                for mot in dec_orgue:
                    if mot in dec_osm:
                        cor_org += 1/len(dec_orgue)

                # Calcul du taux (entre 0 et 1) de correspondance pour le nom de l'édifice de l'orgue
                # (taux de présence des mots du nom du bâtiment OSM dans le nom de l'édifice de l'orgue)
                cor_osm = 0
                for mot in dec_osm:
                    if mot in dec_orgue:
                        cor_osm += 1/len(dec_osm)

                # Calcul du taux moyen de correspondance
                cor_moy = (cor_org+cor_osm)/2
                if cor_moy>0.6:
                    # Si le taux est assez important, le bâtiment OSM est conservé dans une liste d'appariement partiel
                    resultat.append({"Correspondance": cor_moy, "elem":elem})
                    logger_appariement_multiple.info("L'orgue {} a une corrélation de {} avec {}".format(orgue, cor_moy, nom_topo))
        
        if len(resultat) != 0:
            maximum = max([edifice["Correspondance"] for edifice in resultat])
            nb_edifice = len([i for i in resultat if i["Correspondance"] == maximum])
            edifices_max = [edifice["elem"] for edifice in resultat if edifice["Correspondance"] == maximum]
            if nb_edifice == 1:
                self.compte_appariement_multiple_reussite += 1
                logger_appariement_reussite.info("L'orgue {} a été associé à l'édifice {} de la ville de {}".format(orgue, edifices_max[0]["properties"]["TOPONYME"], edifices_max[0]["properties"]["NOM"]))
                self.calculer_barycentre(edifices_max[0], orgue)
            else:
                logger_appariement_multiple.info("Il y a au moins deux possibilités avec l'orgue {}. On teste la corrélation".format(orgue))
                self.correlation(edifices_max, orgue)
        else:
            logger_appariement_multiple.info("Il n'y a aucune possibilité avec l'orgue {}. On teste la corrélation".format(orgue))
            self.correlation(elements, orgue)
    
    def correlation(self, elements, orgue):
        """
        Cherche le bâtiment le plus adapté à partir d'une corrélation sur la codification des deux bâtiments
        """
        correspondances = []
        for elem in elements:
            nom_topo = elem["properties"]["TOPONYME"]
            if  nom_topo:
                edifice_test, type_edifice_test = co.reduire_edifice(nom_topo, orgue.commune)
                codification_test = codif.codifier_instrument(orgue.code_insee, orgue.commune, edifice_test, type_edifice_test, '')
                correlation_codification = self.calcul_correlation_codification(orgue.codification, codification_test)
                if correlation_codification <= 4:
                    correspondances.append({"Correlation": correlation_codification, "elem":elem})
                    logger_appariement_correlation.info("L'orgue {} a une corrélation de {} avec {}".format(orgue, correlation_codification, nom_topo))
        if len(correspondances) != 0:
            minimum = min([edifice["Correlation"] for edifice in correspondances])
            nb_edifice = len([i for i in correspondances if i["Correlation"] == minimum])
            edifices_max = [edifice["elem"] for edifice in correspondances if edifice["Correlation"] == minimum]
            if nb_edifice == 1 and minimum <= 2:
                logger_appariement_reussite.info("L'orgue {} a été associé à l'édifice {} de la ville de {}".format(orgue, nom_topo, edifices_max[0]["properties"]["NOM"]))
                self.compte_appariement_correlation_reussite += 1
                self.calculer_barycentre(edifices_max[0], orgue)
            else: 
                self.compte_appariement_correlation_echec += 1
                logger_appariement_nul.error("Pas d'appariement possible pour {}.".format(orgue))
        else: 
            self.compte_appariement_correlation_echec += 1
            logger_appariement_nul.error("Pas d'appariement possible pour {}.".format(orgue))
            
    def calcul_correlation_codification(self, codif1, codif2):
        """
        Retourne une erreur si la taille des deux codifications n'est pas égale
        """
        erreur = 0
        if len(codif1) != len (codif2):
            logger_appariement_correlation.error("Taille de codif différente : {}, {}".format(codif1, codif2))
            return 10
        else:
            for i in range(len(codif1)):
                if codif1[i] != codif2[i]:
                    erreur += 1
        return erreur    

    def tenter_appariement_sans_nom(self, orgue, rows):
        """
        Effectue l'appariement uniquement sur le type de bâtiment. Par exemple, si l'église est un temple protestant 
        et qu'il n'y a qu'un seul lieu de culte protestant dans la commune, alors on considère que l'orgue s'y trouve.
        """
        nom_edifice, type_edifice = co.detecter_type_edifice(orgue.edifice)
        if nom_edifice != "":
            # Décomposition du nom en une liste de mots
            decompo = re.split("-| |'|’", nom_edifice)
        else :
            # Cas particulier des édifices sans dédicaces (par exemple, "temple réformé" ou "chapelle du lycée")
            # On prend alors le nom complet plutôt que la dédicace.
            # Décomposition du nom en une liste de mots
            decompo = re.split("-| |'|’", orgue.edifice)

        decompo_query = []
        for mot in decompo:
            if len(mot) > 2: #Filtre pour ne pas rechercher les mots de liaisons (de, l, la, en...)
                decompo_query.append(mot)

        enseignement, protestant, chretien = self.trouver_nature_batiment(re.split("-| |'|’", orgue.edifice.lower()))

        response = []
        for row in rows:
            INSEE_topo = row["properties"]["INSEE_COM"]
            if self.nature_correspond( enseignement, protestant, chretien, row["properties"]):
                if INSEE_topo == orgue.code_insee :
                    response.append(row)

        if len(response) == 1:  # Si un seul élément dans response, il y a un appariement unique, c'est donc validé :
            logger_appariement_reussite.info("Appariement direct sans nom")
            self.compte_appariement_direct_sans_nom_reussite += 1
            logger_appariement_reussite.info("L'orgue {} de la ville de {} a été associé à l'édifice {} de la ville de {}".format(orgue, orgue.commune, response[0]["properties"]["TOPONYME"], response[0]["properties"]["NOM"]))
            self.calculer_barycentre(response[0], orgue)
        else:
            self.compte_appariement_direct_sans_nom_echec += 1
            logger_appariement_reussite.info("compte_appariement_direct_sans_nom_echec. Nombre de réponses : {}".format(len(response)))