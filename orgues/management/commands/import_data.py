import os
import json
import csv
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from orgues.models import Orgue


class Command(BaseCommand):
    help = 'Population de la base de donnée avec les types de clavier et les jeux les plus courants'

    def handle(self, *args, **options):

        with open(os.path.join(settings.BASE_DIR, "orgues", "management", "commands","data.csv"), "r") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                orgue,  created = Orgue.objects.get_or_create(
                    codification=row["Codification_instrument"],
                )
                try:
                    orgue.slug = "orgue-{}-{}-{}".format(slugify(orgue.commune),slugify(orgue.edifice),orgue.pk)
                    orgue.commune = row["Commune"]
                    orgue.code_insee = row["Code_insee"]
                    orgue.edifice = row["Edifice"]
                    orgue.departement = row["Nom_departement"]
                    orgue.region = row["Nom_region"]
                    if row["Latitude"]:
                        orgue.latitude = float(row["Latitude"])
                    if row["Longitude"]:
                        orgue.longitude = float(row["Longitude"])
                    orgue.save()
                except Exception as e:
                    print(str(e))
                    print(row["Codification_instrument"])
