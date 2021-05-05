__all__ = ["codegeographique", "codification", "correcteurorgues", "grep"]


from .correcteurorgues import detecter_type_edifice
from .correcteurorgues import corriger_nom_edifice
from .correcteurorgues import _simplifier_nom_edifice
from .correcteurorgues import reduire_edifice

