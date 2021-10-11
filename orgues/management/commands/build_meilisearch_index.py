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
            'edifice',
            'facteurs',
            'departement',
            'region',
            'ancienne_commune',
            'placeholder',
            'latitude',
            'longitude'
        ])

        index.update_filterable_attributes([
            'departement',
            'region',
            'resume_composition_clavier',
            'facet_facteurs',
            'jeux',
        ])

        index.update_displayed_attributes([
            'id',
            'designation',
            'edifice',
            'commune',
            'ancienne_commune',
            'departement',
            'region',
            'completion',
            'vignette',
            'emplacement',
            'resume_composition',
            'facteurs',
            'facet_facteurs',
            'url',
            'latitude',
            'longitude',
            'construction',
        ])

        index.update_ranking_rules([
            'typo',
            'words',
            'proximity',
            'attribute',
            'sort',
            'completion:desc',
            'exactness',
        ])
        index.update_sortable_attributes([
            'commune',
            'completion',
            'jeux_count',
            'construction',
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
