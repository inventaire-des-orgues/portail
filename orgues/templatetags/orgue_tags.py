import re

from django import template

register = template.Library()


@register.simple_tag
def resume_clavier(count, has_pedalier):
    """
    Affiche l'information Clavier et Pédale de façon commune, sous le format :
    [nombre de claviers en chiffres romains]["/P" si Pédale]
    """

    chiffres_romains = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII", "XIV", "XV",
                        "XVI", "XVII","XVIII","XIX","XX","XXI","XXII","XXIII","XIV","XV"]
    if count == 0:
        resume = "?"
    else:
        resume = chiffres_romains[count-1]
    if has_pedalier:
        resume += "/P"
    return resume
