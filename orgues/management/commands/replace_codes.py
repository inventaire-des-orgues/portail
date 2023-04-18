import os
import shutil

from project import settings
from django.core.management.base import BaseCommand
from orgues.models import Orgue
from pathlib import Path


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

                    chemin_avant_propre = Path(chemin_avant)
                    chemin_apres_propre = Path(chemin_apres)

                    code_avant = chemin_avant_propre.name
                    code_apres = chemin_apres_propre.name

                    print("Je remplace {} par {}".format(chemin_avant, chemin_apres))
                    orgue = Orgue.objects.get(codification__exact=code_avant)
                    
                    # On met à jour le code et le numéro du département de l'orgue
                    orgue.codification = code_apres
                    orgue.code_departement = chemin_apres_propre.parent

                    #On met à jour le nom du département
                    for dep in Orgue.CHOIX_DEPARTEMENT:
                        if dep[0] == str(orgue.code_departement):
                            orgue.departement = dep[1]

                    # On met à jour les fichiers images
                    for img in orgue.images.all():
                        pathimage_avant = Path(img.image.path)
                        path_media = pathimage_avant.parents[3]
                        name = pathimage_avant.name
                        pathimage_apres = Path(path_media, chemin_apres_propre, "images", name)

                        if not pathimage_apres.parent.exists():
                            os.makedirs(pathimage_apres.parent)
                        if not pathimage_apres.exists():
                            os.rename(pathimage_avant, pathimage_apres)

                        if img.thumbnail_principale:
                            thumbnail_principale_path_avant = img.thumbnail_principale.path
                            chemin_thumbnail_avant = Path(img.thumbnail_principale.name)
                            img.thumbnail_principale.name = str(Path(chemin_apres_propre, "images", chemin_thumbnail_avant.name))
                            shutil.move(thumbnail_principale_path_avant, img.thumbnail_principale.path)

                        pathimage_avant = Path(img.image.name)
                        img.image.name = str(Path(chemin_apres_propre, "images", pathimage_avant.name))
                        img.save()
                    
                    # On met à jour les autres fichiers
                    for fic in orgue.fichiers.all():
                        pathfichier_avant = Path(fic.file.path)
                        path_media = pathfichier_avant.parents[3]
                        name = pathfichier_avant.name
                        pathfichier_apres = Path(path_media, chemin_apres_propre, "fichiers", name)


                        # Create dir if necessary
                        if not pathfichier_apres.parent.exists():
                            os.makedirs(pathfichier_apres.parent)

                        # Déplacement des fichiers sur le disque
                        if pathfichier_avant.exists() and not pathfichier_apres.exists():
                            os.rename(pathfichier_avant, pathfichier_apres)

                            # On renomme en particulier le fichier PDF de livre d'inventaire s'il existe
                            print(pathfichier_apres.name, code_avant + '.pdf')
                            if pathfichier_apres.name == code_avant + '.pdf':
                                os.rename(pathfichier_apres, Path(pathfichier_apres.parent, code_apres + '.pdf'))
                                # Renommage du lien vers le fichier PDF de livre d'inventaire s'il existe
                                fic.file.name = str(Path(chemin_apres_propre, "fichiers", code_apres + '.pdf'))

                        # Renommage de tous les liens
                        pathfile_avant = Path(fic.file.name)
                        fic.file.name = str(Path(chemin_apres_propre, "fichiers", pathfile_avant.name))                        

                        fic.save()
                    orgue.save()
                    
                    # On efface l'ancien répertoire
                    p = Path(settings.MEDIA_ROOT, chemin_avant_propre)
                    if p.exists():
                        shutil.rmtree(p)
                    if len(orgue.images.all())>=1:
                        p_thumbnail = Path(Path(img.thumbnail.path).parents[4], chemin_avant_propre)
                        print(img.thumbnail.path)
                        print(Path(img.thumbnail.path))
                        print(Path(img.thumbnail.path).parents[4])
                        print(p_thumbnail)
                        if p_thumbnail.exists():
                            shutil.rmtree(p_thumbnail)
                    
                    
                print('Fin de la modification des codes.')
                
