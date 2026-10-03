"""
Fond de carte Plan IGN « gris » épuré, servi par le portail : seuls l'eau, les limites et les noms de lieux
restent, comme l'ancien fond Mapbox « light ». Les tuiles, polices et sprites restent ceux de la Géoplateforme.
"""
import re

URL_STYLE_IGN = "https://data.geopf.fr/annexes/ressources/vectorTiles/styles/PLAN.IGN/gris.json"

COUCHES_RETIREES = re.compile(r"^(routier|ferre|oro|ocs|bati_ponc|bati_lin|bati_zai|toponyme_(?!localite|hydro|limite))")


def epurer_style_ign(style):
    """
    Style MapLibre de l'IGN sans les routes, voies ferrées, relief, végétation, bâti et noms secondaires.
    """
    couches = [couche for couche in style["layers"] if not COUCHES_RETIREES.match(couche.get("source-layer", ""))]
    return {**style, "layers": couches, "metadata": {"portail:source": URL_STYLE_IGN}}
