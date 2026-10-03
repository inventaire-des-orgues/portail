"""
Recherche des orgues affichés sur la carte : construction du filtre et accès à Meilisearch.
"""
import meilisearch
from django.conf import settings

OPTIONS_RECHERCHE_CARTE = {'facets': ['region', 'departement'], 'limit': 100000}


def _alternative(attribut, valeurs):
    return "(" + " OR ".join(f'{attribut} = "{valeur}"' for valeur in valeurs) + ")"


def construire_filtre_carte(cleaned_data):
    """
    Filtre Meilisearch correspondant aux données validées par OrgueCarteForm, ou None sans aucun filtre.
    """
    filtres = []
    if cleaned_data['etats']:
        filtres.append(_alternative("etat", cleaned_data['etats']))
    if cleaned_data['facteurs']:
        filtres.append(_alternative("facet_facteurs", [facteur.nom.strip() for facteur in cleaned_data['facteurs']]))
    if cleaned_data['manufactures']:
        filtres.append(_alternative("facet_manufactures",
                                    [manufacture.nom.strip() for manufacture in cleaned_data['manufactures']]))
    if cleaned_data['jeux']:
        filtres.append(f"(jeux_count {cleaned_data['jeux'][0]} TO {cleaned_data['jeux'][1]})")
    if cleaned_data['monument']:
        filtres.append('(monument_historique = "true")')
    if cleaned_data['departements']:
        filtres.append(_alternative("departement", cleaned_data['departements']))
    return " AND ".join(filtres) or None


def rechercher_orgues_carte(filtre):
    """
    Résultats bruts de Meilisearch (orgues et totaux par région et département) pour le filtre donné.
    """
    client = meilisearch.Client(settings.MEILISEARCH_URL, settings.MEILISEARCH_KEY)
    return client.index(uid='orgues').search(None, {**OPTIONS_RECHERCHE_CARTE, 'filter': filtre})
