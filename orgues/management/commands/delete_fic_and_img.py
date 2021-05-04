import os
import shutil

from project import settings
from django.core.management.base import BaseCommand
from orgues.models import Orgue


class Command(BaseCommand):
    help = "Effacer les lien vers fichiers et images"

    def handle(self, *args, **options):
        print("Début effacement des liens vers fichiers et images.")
        for orgue in Orgue.objects.all():
            for img in orgue.images.all():
                img.delete()
            for fic in orgue.fichiers.all():
                fic.delete()
            orgue.save()
        print("Fin effacement des liens vers fichiers et images.")
