from orgues.models import Orgue
from django.core.management.base import BaseCommand
from tqdm import tqdm
import json


class Command(BaseCommand):
    """
    Récupère les informations des orgues de la base de données qui n'ont pas le champs code_INSEE renseigné.
    """
    help = 'Listage des orgues sans code INSEE'

    def __init__(self):
        self.liste_insee_manquants = []

    def handle(self, *args, **options):
        nb = 0
        for orgue in tqdm(Orgue.objects.all()):
            # On recherche les orgues qui n'ont pas de code INSEE renseigné
            if not orgue.code_insee:
                nb += 1
                self.liste_insee_manquants.append({"codification": orgue.codification, "commune": orgue.commune})

        print("Il y a {} orgues dont le code INSEE n'est pas renseigné (voir le détail dans code_INSEE_manquants.json)".format(nb))        
        with open('code_INSEE_manquants.json', 'w') as f:
            json.dump(self.liste_insee_manquants, f)
