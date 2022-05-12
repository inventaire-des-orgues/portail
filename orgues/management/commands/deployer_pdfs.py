import os
import shutil
import tarfile


from project import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Déploiement des fichiers PDF pour chaque orgue depuis un dossier d'archives .tar."

    def add_arguments(self, parser):
        parser.add_argument('path', nargs=1, type=str,
                            help="Chemin vers le dossier contenant l'archive ou les archives à déployer")

    def handle(self, *args, **options):
        """
        http://inventaire-des-orgues.fr/media/<code_dep>/<code_orgue>/fichiers/<nomdufichier>
        """
        if not os.path.exists(options['path'][0]):
            print("Dossier introuvable !")
        else:
            for file in os.listdir(options['path'][0]):
                chemin_tar = os.path.join(options['path'][0], file)
                tar = tarfile.open(chemin_tar)
                rep_temp_pdf = os.path.join(settings.BASE_DIR, 'temp_pdf')
                print("Création d'un répertoire temporaire : {}".format(rep_temp_pdf))
                if os.path.exists(rep_temp_pdf):
                    shutil.rmtree(rep_temp_pdf)
                os.makedirs(rep_temp_pdf)
                tar.extractall(rep_temp_pdf)
                tar.close()

                print("Parcours des PDF du dossier : {}".format(rep_temp_pdf))
                for pdf in os.listdir(rep_temp_pdf):
                    print("[DEBUG] Fichier PDF : {}".format(pdf))
                    chemin_pdf = os.path.join(rep_temp_pdf, pdf)
                    print("[DEBUG] Chemin : {}".format(chemin_pdf))
                    dossier_dest = os.path.join(settings.MEDIA_ROOT, pdf[3:5], pdf.rstrip('.pdf'), 'fichiers')
                    print("[DEBUG] Dossier destination : {}".format(dossier_dest))
                    if not os.path.exists(dossier_dest):
                        os.makedirs(dossier_dest)
                        print("Création dossier : {}".format(dossier_dest))
                    dest = os.path.join(dossier_dest, pdf)
                    print("Copie fichier {} vers {}".format(chemin_pdf, dest))
                    shutil.copyfile(chemin_pdf, dest)
                shutil.rmtree(rep_temp_pdf)
