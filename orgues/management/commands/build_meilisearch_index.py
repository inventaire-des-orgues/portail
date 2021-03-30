from django.core.management.base import BaseCommand
import meilisearch
from django.conf import settings
from orgues.api.serializers import OrgueResumeSerializer
from orgues.models import Orgue, TypeJeu


class Command(BaseCommand):
    help = 'Build search index'

    def handle(self, *args, **options):
        if not settings.MEILISEARCH_URL:
            print("Moteur meilisearch non configuré")
            return
        client = meilisearch.Client(settings.MEILISEARCH_URL, settings.MEILISEARCH_KEY)
        # orgues
        try:
            index = client.get_index(uid='orgues')
        except:
            index = client.create_index(uid='orgues')

        index.update_searchable_attributes([
            'commune',
            'ancienne_commune',
            'edifice',
            'region',
            'facteurs',
            'departement',
            'placeholder'
        ])

        index.update_attributes_for_faceting([
            'departement'
        ])

        index.update_ranking_rules([
            'typo',
            'words',
            'proximity',
            'attribute',
            'wordsPosition',
            'exactness',
            'desc(completion)',
        ])
        orgues = OrgueResumeSerializer(Orgue.objects.all(), many=True).data
        index.delete_all_documents()
        index.add_documents(orgues)

        # types de jeux
        try:
            index = client.get_index(uid='types_jeux')
        except:
            index = client.create_index(uid='types_jeux')

        index.update_searchable_attributes(['nom'])
        index.delete_all_documents()
        index.add_documents([{'id':t.id,'nom':str(t)} for t in TypeJeu.objects.all()])
