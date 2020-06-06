from django.core.management.base import BaseCommand
from tqdm import tqdm

from orgues.models import Orgue


class Command(BaseCommand):
    help = 'Build search index'

    def handle(self, *args, **options):

        for orgue in tqdm(Orgue.objects.all()):
            orgue.save()
