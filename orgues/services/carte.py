"""
Recherche des orgues affichés sur la carte : construction du filtre et accès à Meilisearch.
"""
import json
import logging

import meilisearch
from django.conf import settings
from meilisearch.errors import MeilisearchError
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)

DELAI_MEILISEARCH_SECONDES = 10
OPTIONS_RECHERCHE_CARTE = {'facets': ['region', 'departement'], 'limit': 100000}


class RechercheCarteIndisponible(Exception):
    """Le moteur de recherche ne peut pas répondre (non configuré, injoignable, en erreur)."""


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
    if not settings.MEILISEARCH_URL:
        # Un client créé sans URL ne lève une erreur (TypeError) qu'au moment de la recherche
        logger.warning("Recherche de la carte impossible : Meilisearch n'est pas configuré (MEILISEARCH_URL).")
        raise RechercheCarteIndisponible
    try:
        client = meilisearch.Client(settings.MEILISEARCH_URL, settings.MEILISEARCH_KEY,
                                    timeout=DELAI_MEILISEARCH_SECONDES)
        return client.index(uid='orgues').search(None, {**OPTIONS_RECHERCHE_CARTE, 'filter': filtre})
    # Une réponse d'erreur non JSON ou une URL mal formée échappent aux erreurs propres au client Meilisearch
    except (MeilisearchError, json.JSONDecodeError, RequestException) as erreur:
        logger.exception("Recherche de la carte en échec dans Meilisearch.")
        raise RechercheCarteIndisponible from erreur
