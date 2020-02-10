import re

from django import template

register = template.Library()


@register.simple_tag
def resume_clavier(jeux_count, claviers_count, has_pedalier):
    """
    Affiche l'information Clavier et Pédale de façon commune, sous le format :
    [nombre de claviers en chiffres romains]["/P" si Pédale]
    """

    cr = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII", "XIV", "XV",
                        "XVI", "XVII", "XVIII", "XIX", "XX", "XXI", "XXII", "XXIII", "XIV", "XV"]
    print(jeux_count,claviers_count,has_pedalier)
    if claviers_count == 0:
         return "?"

    if has_pedalier and claviers_count > 1:
        return "{}, {}/P".format(jeux_count, cr[claviers_count-2])

    elif has_pedalier and claviers_count == 1:
        return "{}, P".format(jeux_count)

    return "{}, {}".format(jeux_count, cr[claviers_count])
