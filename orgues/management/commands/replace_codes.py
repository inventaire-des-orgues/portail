import os
import shutil

from project import settings
from django.core.management.base import BaseCommand
from orgues.models import Orgue


class Command(BaseCommand):
    help = "Correction de codes d'orgues"

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
                    (chemin_avant, chemin_apres) = couple_code

                    code_avant = os.path.basename(chemin_avant)
                    departement_avant = os.path.dirname(chemin_avant)
                    code_apres = os.path.basename(chemin_apres)
                    departement_apres = os.path.dirname(chemin_apres)
                    chemin_avant_propre = os.path.join(departement_avant, code_avant)
                    chemin_apres_propre = os.path.join(departement_apres, code_apres)

                    orgue = Orgue.objects.get(codification__exact=code_avant)
                    print("Orgue {} : je remplace {} par {}".format(str(orgue), code_avant, code_apres))
                    
                    # On met à jour le code de l'orgue
                    orgue.codification = code_apres

                    # On met à jour les fichiers images
                    for img in orgue.images.all():
                        pathimage_avant = img.image.path
                        pathimage_apres = img.image.path.replace(chemin_avant_propre, chemin_apres_propre)

                        # Create dir if necessary and move file
                        if not os.path.exists(os.path.dirname(pathimage_apres)):
                            os.makedirs(os.path.dirname(pathimage_apres))
                        if not os.path.exists(pathimage_apres):
                            os.rename(pathimage_avant, pathimage_apres)

                        if img.thumbnail_principale:
                            chemin_thumbnail_avant = img.thumbnail_principale.path
                            img.thumbnail_principale.name = img.thumbnail_principale.name.replace(chemin_avant, chemin_apres)
                            chemin_thumbnail_apres = img.thumbnail_principale.path
                            shutil.move(chemin_thumbnail_avant, chemin_thumbnail_apres)

                        img.image.name = img.image.name.replace(chemin_avant, chemin_apres)
                        img.image.name = img.image.name.replace(chemin_avant_propre, chemin_apres_propre)
                        img.save()
                    
                    # On met à jour les autres fichiers
                    for fic in orgue.fichiers.all():
                        pathfichier_avant = fic.file.path
                        pathfichier_apres = fic.file.path.replace(chemin_avant_propre, chemin_apres_propre)

                        # Create dir if necessary
                        if not os.path.exists(os.path.dirname(pathfichier_apres)):
                            os.makedirs(os.path.dirname(pathfichier_apres))

                        # Déplacement des fichiers sur le disque
                        if os.path.exists(pathfichier_avant) and not os.path.exists(pathfichier_apres):
                            os.rename(pathfichier_avant, pathfichier_apres)

                            # On renomme en particulier le fichier PDF de livre d'inventaire s'il existe
                            if pathfichier_apres[-28:] == code_avant + '.pdf':
                                os.rename(pathfichier_apres, pathfichier_apres[:-28] + code_apres + '.pdf')
                                # Renommage du lien vers le fichier PDF de livre d'inventaire s'il existe
                                fic.file.name = fic.file.name[:-28] + code_apres + '.pdf'

                        # Renommage de tous les liens
                        fic.file.name = fic.file.name.replace(chemin_avant_propre, chemin_apres_propre)
                        fic.file.name = fic.file.name.replace(chemin_avant, chemin_apres)

                        fic.save()
                    orgue.save()
                    
                    # On efface l'ancien répertoire
                    p = os.path.join(settings.MEDIA_ROOT, chemin_avant_propre)
                    if os.path.exists(p):
                        shutil.rmtree(p)
                    p_thumbnail = os.path.join(img.thumbnail.path.split(chemin_apres_propre)[0], chemin_avant_propre)
                    if os.path.exists(p_thumbnail):
                        shutil.rmtree(p_thumbnail)
                    
                    
                print('Fin de la modification des codes.')
                
