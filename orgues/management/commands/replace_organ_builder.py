from orgues.models import Orgue
from orgues.models import Facteur
from orgues.models import Evenement
from django.core.management.base import BaseCommand
import os


class Command(BaseCommand):
    """
    Remplace dans tous les événements un facteur d'orgue par un autre.
    La fonction prend un argument obligatoire et un optionnel:
    - Le fichier csv contenant les modifications : une colonne pour les facteurs à remplacer, une autre pour les facteurs qui remplacent;
    - optionnel : --delete : efface de la base de données les facteurs à retirer.
    La fonction renvoie un message d'erreur si l'un des facteurs du fichier csv n'existe pas dans la base de données ou s'il existe plusieurs fois 
    (dans ce dernier cas, utiliser le script manage.py delete_organ_builder_duplication).

    Ex :
    py manage.py replace_organ_builder --delete facteurs_remplacement.csv
    """
    help = "Change le facteur d'orgue"

    def add_arguments(self, parser):
        parser.add_argument('codestable', nargs=1, type=str,
                            help='Chemin vers le fichier (CSV, points-virgules, utf-8) contenant deux colonnes : facteurs à remplacer et facteurs qui remplacent.')
        parser.add_argument('--delete', action='store_true',
                            help="Efface le facteur d'orgue de la base de données")

    def handle(self, *args, **options):
        if not os.path.exists(options['codestable'][0]):
            return "Fichier introuvable".format(options['codestable'][0])
        else:
            with open(options['codestable'][0], "r", encoding="utf-8") as f:
                print("Début traitement d'une liste de codes à remplacer.")
                couples_facteurs = [ligne.rstrip('\n').split(';') for ligne in f.readlines()]
                for couple_facteur in couples_facteurs:
                    facteur_avant = couple_facteur[0]
                    facteur_delete = Facteur.objects.filter(nom=facteur_avant)
                    if facteur_delete.count() == 0:
                        print("ERROR : Le nom du facteur à remplacer n'existe pas : {}".format(facteur_avant))
                    elif facteur_delete.count() > 1:
                        print("ERROR : Deux facteurs à effacer portent le même nom : {}".format(facteur_avant))
                    else:
                        liste_facteur_apres = []
                        erreur = False
                        for f in range(1, len(couple_facteur)):
                            facteur_apres = couple_facteur[f]
                            facteur_replace = Facteur.objects.filter(nom=facteur_apres)
                            liste_facteur_apres.append(facteur_replace)
                            if facteur_replace.count() == 0:
                                erreur = True
                                print("ERROR : Le nom du facteur qui doit prendre place n'existe pas : {}".format(facteur_apres))
                            elif facteur_replace.count() > 1:
                                erreur = True
                                print("ERROR : Deux facteurs à mettre portent le même nom : {}".format(facteur_apres))
                        if not erreur:
                            print("INFO : Je cherche à remplacer {} par {}".format(facteur_delete, liste_facteur_apres))
                            evenements = Evenement.objects.filter(facteurs=facteur_delete[0])
                            for evenement in evenements:
                                for facteur_replace in liste_facteur_apres:
                                    evenement.facteurs.add(facteur_replace[0])
                                evenement.facteurs.remove(facteur_delete[0])
                                print("INFO : Changement effectué pour l'orgue de {} pour l'événement {}.".format(evenement.orgue, evenement))
                                evenement.save()
                            orgues = Orgue.objects.filter(entretien=facteur_delete[0])
                            for orgue in orgues:
                                for facteur_replace in liste_facteur_apres:
                                    orgue.entretien.add(facteur_replace[0])
                                orgue.entretien.remove(facteur_delete[0])
                                print("INFO : Changement effectué pour l'entretien de l'orgue de {}.".format(orgue))
                                orgue.save()
                            if options['delete']:
                                print("INFO : Le facteur {} a été retiré de la liste.".format(facteur_delete))
                                facteur_delete[0].delete()