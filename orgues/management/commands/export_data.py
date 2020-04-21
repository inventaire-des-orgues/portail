import json

from django.core.management.base import BaseCommand
from orgues.models import Orgue


class Command(BaseCommand):
    help = "Exporte l'orgue le plus récemment modifié en format JSON"
    #TODO: A TESTER : Implémenter export des noms et chemins de fichers
    #TODO: Implémenter export des accessoires
    def handle(self, *args, **options):
        orgue = Orgue.objects.order_by('-modified_date').first()

        o = {
            "commentaire_admin": orgue.commentaire_admin,
            "designation": orgue.designation,
            "is_polyphone": orgue.is_polyphone,
            "elevation": orgue.elevation,
            "etat": orgue.etat,
            "codification": orgue.codification,
            "edifice": orgue.edifice,
            "commune": orgue.commune,
            "code_insee": orgue.code_insee,
            "ancienne_commune": orgue.ancienne_commune,
            "departement": orgue.departement,
            "code_departement": orgue.code_departement,
            "region": orgue.region,
            "resume": orgue.resume,
            "references_palissy": orgue.references_palissy,
            "latitude": orgue.latitude,
            "longitude": orgue.longitude,
            "osm_type": orgue.osm_type,
            "osm_id": orgue.osm_id,
            "organisme": orgue.organisme,
            "proprietaire": orgue.proprietaire,
            "lien_reference": orgue.lien_reference,
            "transmission_notes": orgue.transmission_notes,
            "transmission_commentaire": orgue.transmission_commentaire,
            "tirage_jeux": orgue.tirage_jeux,
            "tirage_commentaire": orgue.tirage_commentaire,
            "buffet": orgue.buffet,
            "console": orgue.console,
            "diapason": orgue.diapason,
            "sommiers": orgue.sommiers,
            "soufflerie": orgue.soufflerie,
            "commentaire_tuyauterie": orgue.commentaire_tuyauterie,
            "claviers": [],
            "evenements": [],
            "images": [],
            "fichiers": [],
            "accessoires": [],
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
                        "nom": jeu.type.nom,
                        "hauteur": jeu.type.hauteur,
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
                "chemin": image.image.name,
                "credit": image.credit
            }
            o["images"].append(i)

        for fichier in orgue.fichiers.all():
            f = {
                "chemin": fichier.file,
                "description": fichier.description
            }
            o["fichiers"].append(f)

        for accessoire in orgue.accessoires.all():
            o["accessoires"].append(str(accessoire))

        with open('exemple_orgue.json', 'w') as f:
            json.dump(o, f)
