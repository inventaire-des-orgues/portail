from django.core.management.base import BaseCommand
from tqdm import tqdm

from orgues.models import Orgue


class Command(BaseCommand):
    help = "Calcul et enregistrement en base de données le taux d'avancement des fiches"

    def handle(self, *args, **options):

        for orgue in tqdm(Orgue.objects.all()):
            orgue.completion = orgue.calcul_completion()
            orgue.save()
