import json

import meilisearch
from django.conf import settings
from django.core.management.base import BaseCommand

from orgues.views import OrgueCarte


class Command(BaseCommand):
    help = 'Mise en cache de la carte'

    def handle(self, *args, **options):
        if not settings.MEILISEARCH_URL:
            print("Moteur meilisearch non configuré")
            return
        client = meilisearch.Client(settings.MEILISEARCH_URL, settings.MEILISEARCH_KEY)
        index = client.index('orgues')
        results = index.search(None, {'facets': ['region', 'departement'], 'limit': 100000})
        cache_carte = OrgueCarte.meilisearch_results_to_map_json(results)
        with open(settings.CACHE_CARTE, 'w') as f:
            json.dump(cache_carte, f)
