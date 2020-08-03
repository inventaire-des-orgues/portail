import os
import shutil

from project import settings
from django.core.management.base import BaseCommand
from orgues.models import Orgue


class Command(BaseCommand):
    help = 'Population initiale de la base de données avec les types'

    def add_arguments(self, parser):
        parser.add_argument('codestable', nargs=1, type=str,
                            help='Chemin vers le fichier (CSV, points-virgules, utf-8) contenant les codifications des orgues à remplacer')

    def handle(self, *args, **options):
        if not os.path.exists(options['codestable'][0]):
            return "Fichier introuvable".format(options['codestable'][0])
        else:
            with open(options['codestable'][0], "r", encoding="utf-8") as f:
                print("Début traitement d'une liste de codes à remplacer.")
                couples_codes = [ligne.rstrip('\n').split(';') for ligne in f.readlines()]
                for couple_code in couples_codes:
                    (code_avant, code_apres) = couple_code
                    orgue = Orgue.objects.get(codification__exact=code_apres)
                    print("Orgue {} : je remplace {} par {}".format(str(orgue), code_avant, code_apres))
                    # On met à jour le code de l'orgue
                    orgue.codification = code_apres
                    # On met à jour les fichiers images
                    for img in orgue.images.all():
                        pathimage_avant = img.image.path
                        pathimage_apres = img.image.path.replace(code_avant, code_apres)
                        # Create dir if necessary and move file
                        if not os.path.exists(os.path.dirname(pathimage_apres)):
                            os.makedirs(os.path.dirname(pathimage_apres))
                        if not os.path.exists(pathimage_apres):
                            os.rename(pathimage_avant, pathimage_apres)
                        img.image.name = img.image.name.replace(code_avant, code_apres)
                        img.image.save()
                    # On met à jour les autres fichiers
                    for fic in orgue.fichiers.all():
                        pathfichier_avant = fic.file.path
                        pathfichier_apres = fic.file.path.replace(code_avant, code_apres)
                        # Create dir if necessary and move file
                        if not os.path.exists(os.path.dirname(pathfichier_apres)):
                            os.makedirs(os.path.dirname(pathfichier_apres))
                        if not os.path.exists(pathfichier_apres):
                            os.rename(pathfichier_avant, pathfichier_apres)
                        fic.file.name = fic.file.name.replace(code_avant, code_apres)
                        fic.file.save()
                    # On efface l'ancien répertoire
                    p = os.path.join(settings.MEDIA_ROOT, orgue.code_departement, code_avant)
                    if os.path.exists(p):
                        shutil.rmtree(p)
                    orgue.save()
                print('Fin de la modification des codes.')
