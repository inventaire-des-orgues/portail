from django.core.management.base import BaseCommand
from tqdm import tqdm

from orgues.models import Orgue

class Command(BaseCommand):
    help = 'Calcul et enregistrement en base de données des facteurs stockés dans les évenements des orgues'

    def handle(self, *args, **options):

        for orgue in tqdm(Orgue.objects.all()):
            orgue.calcul_facteurs()
