from django.core.management.base import BaseCommand
from tqdm import tqdm

from orgues.models import Orgue


class Command(BaseCommand):
    help = 'Calcul et enregistrement en base de données du résumé clavier pour tous les orgues'

    def handle(self, *args, **options):

        for orgue in tqdm(Orgue.objects.all()):
            orgue.resume_composition = orgue.calcul_resume_composition()
            orgue.save(updated_fields=['resume_composition'])
