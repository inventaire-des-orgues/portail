from orgues.models import Orgue
from django.core.management.base import BaseCommand
from tqdm import tqdm
import requests
import json
import time

class Command(BaseCommand):
    """
    Récupère tous les commentaires des contributeurs sur les orgues et les sauvegarde dans un fichier commentaires.csv.
    """
    help = 'Récupère tous les commentaires des contributeurs sur les orgues et les sauvegarde dans un fichier commentaires.csv.'


    def handle(self, *args, **options):
        with open('commentaires.csv', 'w') as f:
            for orgue in tqdm(Orgue.objects.all()):
                if orgue.commentaire_admin:
                    commentaire = orgue.commentaire_admin.replace('\n', ' ').replace('\n', ' ')
                    f.write(f"{orgue};{orgue.codification};{commentaire}\n")
            

    
