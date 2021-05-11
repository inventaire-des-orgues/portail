import os
import json
import requests
import tempfile
import traceback

from tqdm import tqdm
from django.core.files import File
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from orgues.models import Orgue, Accessoire, Evenement, Facteur, TypeClavier, Clavier, Jeu, TypeJeu, Image, Source, Fichier


class Command(BaseCommand):
    help = 'Contrôle des données'

    def handle(self, *args, **options):
        # Affichage des valeurs de certains champs :
        designations = Orgue.objects.values('designation')
        for des in set(designations.values()):
            print("INFO : Désignation {}".format(des))
        emplacements = Orgue.objects.values('emplacement')
        for emp in set(emplacements.values()):
            print("INFO : Emplacement {}".format(emp))
        for orgue in tqdm(Orgue.objects.all()):
            # Codification :
            if len(orgue.codification) != 24:  # TODO regexp
                print("ERROR : {} est un code mal formatté pour l'orgue {}".format(orgue.codification, orgue))
            # Palissy :
            if len(orgue.references_palissy.split(';')) > 6:
                print("ERROR : {} Référence Palissy trop longues pour l'orgue {}".format(orgue.references_palissy, orgue))
            # TODO organisme doit être une chaîne sans chiffres
            # TODO lien_reference doit être une URL
            # TODO commentaire_admin : afficher tous, ils doivent être rares.
            # TODO code_dep regex='^(97[12346]|0[1-9]|[1-8][0-9]|9[0-5]|2[AB])$'
            # TODO departement : dans la liste.
            # TODO code_insee : 5 chiffres
            # edifice
            if len(orgue.edifice) <= 6 and orgue.edifice != 'temple':
                print("WARN : {} édifice incomplet pour l'orgue {}".format(orgue.edifice, orgue))
            # TODO lat et lon
            # TODO osm_id
