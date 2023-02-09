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
        index = client.index('orgues')

        client.index('orgues').update_settings({
            'pagination': {
                'maxTotalHits': 100000
            },
            "faceting": {
                "maxValuesPerFacet": 150
            }

        })

        index.update_stop_words(['Le', 'le', 'La', 'la', 'Les', 'les', 'du', 'et', 'de', 'en'])

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
            'etat',
            'region',
            'resume_composition_clavier',
            'facet_facteurs',
            'jeux',
            'jeux_count',
            'monument_historique'
        ])

        index.update_displayed_attributes([
            'id',
            'designation',
            'edifice',
            'commune',
            'ancienne_commune',
            'departement',
            'monument_historique',
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
            'modified_date',
        ])

        index.update_ranking_rules([
            'typo',
            'words',
            'proximity',
            'attribute',
            'sort',
            'completion:desc',
            'modified_date:desc',
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
        if orgues:
            index.add_documents(orgues)

        # types de jeux
        index = client.index('types_jeux')
        index.update_searchable_attributes(['nom'])
        index.delete_all_documents()
        typesJeu = TypeJeu.objects.all()
        if typesJeu:
            index.add_documents([{'id': t.id, 'nom': str(t)} for t in typesJeu])
