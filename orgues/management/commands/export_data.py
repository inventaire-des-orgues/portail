import json

from django.core.management.base import BaseCommand
from orgues.models import Orgue


class Command(BaseCommand):
    help = "Exporte l'orgue le plus récemment modifié en format JSON"

    def handle(self, *args, **options):
        orgue = Orgue.objects.order_by('-modified_date').first()

        o = {
            "nom": orgue.nom,
            "codification": orgue.codification,
            "edifice": orgue.edifice,
            "commune": orgue.commune,
            "code_insee": orgue.code_insee,
            "ancienne_commune": orgue.commune,
            "departement": orgue.departement,
            "region": orgue.region,
            "resume": orgue.resume,
            "references_palissy": orgue.references_palissy,
            "latitude": orgue.latitude,
            "longitude": orgue.longitude,
            "association": orgue.association,
            "association_lien": orgue.association_lien,
            "transmission_notes": orgue.transmission_notes.nom,
            "tirage_jeux": orgue.tirage_jeux.nom,
            "diapason": orgue.diapason,
            "commentaire_tuyauterie": orgue.commentaire_tuyauterie,
            "claviers": [],
            "evenements": [],
            "images":[],
            "fichiers":[],
        }

        for clavier in orgue.claviers.all():
            c = {
                "type": clavier.type.nom,
                "facteur": str(clavier.facteur),
                "is_expressif": clavier.is_expressif,
                "jeux": []
            }
            for jeu in clavier.jeux.all():
                j = {
                    "type": {
                        "nom":jeu.type.nom,
                        "hauteur":jeu.type.hauteur,
                    },
                    "commentaire": jeu.commentaire
                }
                c["jeux"].append(j)

            o["claviers"].append(c)

        for evenement in orgue.evenements.all():
            e = {
                "annee": evenement.annee,
                "type": evenement.type.nom,
                "facteur": str(evenement.facteur),
                "description": evenement.resume
            }
            o["evenements"].append(e)


        for image in orgue.images.all():
            i = {
                "chemin":image.image.name,
                "credit":image.credit
            }
            o["images"].append(i)

        with open('exemple_orgue.json', 'w') as f:
            json.dump(o, f)
