from orgues.models import Orgue
from orgues.models import Facteur, Manufacture
from orgues.models import Evenement
from django.core.management.base import BaseCommand
import os
import logging


logger = logging.getLogger("facteur_to_manufacture")

class Command(BaseCommand):
    """
    Remplace dans tous les événements et entretien d'un facteur d'orgue par une manufacture.
    La fonction prend un argument obligatoire et un optionnel:
    - Le fichier csv séparateur ";" contenant les modifications : une colonne pour les facteurs à remplacer, une autre pour les facteurs qui remplacent;
    - optionnel : --delete : efface de la base de données les facteurs à retirer.
    La fonction renvoie un message d'erreur si l'un des facteurs du fichier csv n'existe pas dans la base de données ou s'il existe plusieurs fois.
    (dans ce dernier cas, utiliser le script manage.py delete_organ_builder_duplication).

    Ex :
    py manage.py replace_organ_builder --delete fic.csv
    """
    help = "Change le facteur d'orgue"

    def add_arguments(self, parser):
        parser.add_argument('codestable', nargs=1, type=str,
                            help='Chemin vers le fichier (CSV, points-virgules, utf-8) contenant au moins deux colonnes : facteurs à remplacer dans la première et facteurs qui remplacent dans les suivantes.')
        parser.add_argument('--delete', action='store_true',
                            help="Efface le facteur d'orgues de la base de données")

    def handle(self, *args, **options):
        if not os.path.exists(options['codestable'][0]):
            return "Fichier introuvable".format(options['codestable'][0])
        else:
            with open(options['codestable'][0], "r", encoding="utf-8") as f:
                logger.info("Début traitement d'une liste de codes à remplacer.")
                couples_facteurs = [ligne.rstrip('\n').split(';') for ligne in f.readlines()]
                for couple_facteur in couples_facteurs:
                    facteur_avant = couple_facteur[0]
                    facteur_delete = Facteur.objects.filter(nom=facteur_avant)
                    if facteur_delete.count() == 0:
                        logger.error("Le nom du facteur à remplacer n'existe pas : {}".format(facteur_avant))
                    elif facteur_delete.count() > 1:
                        logger.error("Deux facteurs à effacer portent le même nom : {}".format(facteur_avant))
                    else:
                        liste_manufacture_apres = []
                        erreur = False
                        for f in range(1, len(couple_facteur)):
                            manufacture_apres = couple_facteur[f]
                            manufacture_replace = Manufacture.objects.filter(nom=manufacture_apres)
                            liste_manufacture_apres.append(manufacture_replace)
                            if manufacture_replace.count() == 0:
                                erreur = True
                                logger.error("Le nom de la manufacture qui doit prendre place n'existe pas : {}".format(manufacture_apres))
                            elif manufacture_replace.count() > 1:
                                erreur = True
                                logger.error("Deux manufactures à mettre portent le même nom : {}".format(manufacture_apres))
                        if not erreur:
                            logger.info("Je cherche à remplacer {} par {}".format(facteur_delete, liste_manufacture_apres))
                            evenements = Evenement.objects.filter(facteurs=facteur_delete[0])
                            for evenement in evenements:
                                for manufacture_replace in liste_manufacture_apres:
                                    evenement.manufactures.add(manufacture_replace[0])
                                evenement.facteurs.remove(facteur_delete[0])
                                logger.info("Changement effectué pour l'orgue de {} pour l'événement {}.".format(evenement.orgue, evenement))
                                evenement.save()
                            orgues = Orgue.objects.filter(entretien=facteur_delete[0])
                            for orgue in orgues:
                                for manufacture_replace in liste_manufacture_apres:
                                    orgue.entretienManufacture.add(manufacture_replace[0])
                                orgue.entretien.remove(facteur_delete[0])
                                logger.info("Changement effectué pour l'entretien de l'orgue de {}.".format(orgue))
                                orgue.save()
                            if options['delete']:
                                logger.info("Le facteur {} a été retiré de la liste.".format(facteur_delete))
                                facteur_delete[0].delete()