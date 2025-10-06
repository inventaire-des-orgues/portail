from orgues.models import Orgue, Accessoire
from django.core.management.base import BaseCommand
import os


class Command(BaseCommand):
    """
    Remplace dans tous les orgues un accessoire par un autre déjà existant.
    La fonction prend un argument obligatoire et un optionnel:
    - Le fichier csv séparateur ";" contenant les modifications : une colonne pour les accessoires à remplacer, une autre pour les accessoires qui remplacent;
    - optionnel : --delete : efface de la base de données les accessoires à retirer.
    La fonction renvoie un message d'erreur si l'un des accessoires du fichier csv n'existe pas dans la base de données ou s'il existe plusieurs fois.
    Ex :
    py manage.py replace_organ_builder --delete fic.csv
    """
    help = "Remplace un accessoire par un autre déjà existant"

    def add_arguments(self, parser):
        parser.add_argument('codestable', nargs=1, type=str,
                            help='Chemin vers le fichier (CSV, points-virgules, utf-8) contenant au moins deux colonnes : accessoires à remplacer dans la première et accesoires qui remplacent dans les suivantes.')
        parser.add_argument('--delete', action='store_true',
                            help="Efface le facteur d'orgues de la base de données")

    def handle(self, *args, **options):
        if not os.path.exists(options['codestable'][0]):
            return "Fichier introuvable".format(options['codestable'][0])
        else:
            with open(options['codestable'][0], "r", encoding="utf-8") as f:
                print("Début traitement d'une liste de codes à remplacer.")
                couples_accessoires = [ligne.rstrip('\n').split(';') for ligne in f.readlines()]
                for couple_accessoires in couples_accessoires:
                    accessoire_avant = couple_accessoires[0]
                    accessoire_delete = Accessoire.objects.filter(nom=accessoire_avant)
                    if accessoire_delete.count() == 0:
                        print("ERROR : Le nom de l'accessoire à remplacer n'existe pas : {}".format(accessoire_avant))
                    elif accessoire_delete.count() > 1:
                        print("ERROR : Deux accessoires à effacer portent le même nom : {}".format(accessoire_avant))
                    else:
                        liste_accessoires_apres = []
                        erreur = False
                        for f in range(1, len(couple_accessoires)):
                            accessoire_apres = couple_accessoires[f]
                            accessoire_replace = Accessoire.objects.filter(nom=accessoire_apres)
                            liste_accessoires_apres.append(accessoire_replace)
                            if accessoire_replace.count() == 0:
                                erreur = True
                                print("ERROR : Le nom de l'accessoire qui doit prendre place n'existe pas : {}".format(accessoire_apres))
                            elif accessoire_replace.count() > 1:
                                erreur = True
                                print("ERROR : Deux accessoires à mettre portent le même nom : {}".format(accessoire_apres))
                        if not erreur:
                            print("INFO : Je cherche à remplacer {} par {}".format(accessoire_delete, liste_accessoires_apres))
                            orgues = Orgue.objects.filter(accessoires=accessoire_delete[0])
                            for orgue in orgues:
                                for accessoire_replace in liste_accessoires_apres:
                                    orgue.accessoires.add(accessoire_replace[0])
                                orgue.accessoires.remove(accessoire_delete[0])
                                print("INFO : Changement effectué pour l'orgue de {}.".format(orgue))
                                orgue.save()
                            if options['delete']:
                                print("INFO : L'accessoire {} a été retiré de la liste.".format(accessoire_delete))
                                accessoire_delete[0].delete()