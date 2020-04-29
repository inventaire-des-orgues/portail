import os
import json
from tqdm import tqdm
from django.core.files import File
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from orgues.models import Orgue, Accessoire, Evenement, Facteur, TypeClavier, Clavier, Jeu, TypeJeu, Image, Fichier


class Command(BaseCommand):
    help = 'Population initiale de la base de données avec les types'

    def add_arguments(self, parser):
        parser.add_argument('path', nargs=1, type=str,
                            help='Chemin vers le dossier contenant les orgues à importer')

        parser.add_argument('--delete', help='Supprime les orgues, jeux et claviers existants')

    def handle(self, *args, **options):

        if not os.path.exists(options['path'][0]):
            return "Path does not exist"
        if options['delete']:
            Orgue.objects.all().delete()
            Clavier.objects.all().delete()
            Jeu.objects.all().delete()
        with open(options['path'][0], "r", encoding="utf-8") as f:
            rows = json.load(f)
            for row in tqdm(rows):
                orgue, created = Orgue.objects.get_or_create(
                    codification=row["codification"],
                )
                try:
                    assert row.get("designation") in [c[0] for c in Orgue.CHOIX_DESIGNATION]
                    assert row.get("proprietaire") in [c[0] for c in Orgue.CHOIX_PROPRIETAIRE] + [None]
                    assert row.get("etat") in [c[0] for c in Orgue.CHOIX_ETAT] + [None]
                    assert row.get("elevation") in [c[0] for c in Orgue.CHOIX_ELEVATION] + [None]
                    assert row.get("tirage_jeux") in [c[0] for c in Orgue.CHOIX_TIRAGE] + [None]
                    assert row.get("transmission_notes") in [c[0] for c in Orgue.CHOIX_TRANSMISSION] + [None]

                    orgue.designation = row.get("designation")
                    orgue.references_palissy = row.get("references_palissy")
                    orgue.resume = row.get("resume")
                    orgue.proprietaire = row.get("proprietaire")
                    orgue.organisme = row.get("organisme")
                    orgue.lien_reference = row.get("lien_reference")
                    orgue.is_polyphone = row.get("is_polyphone")
                    orgue.etat = row.get("etat")
                    orgue.elevation = row.get("elevation")
                    orgue.buffet = row.get("buffet")
                    orgue.console = row.get("console")
                    orgue.commentaire_admin = row.get("commentaire_admin")
                    orgue.edifice = row.get("edifice")
                    orgue.commune = row.get("commune")
                    orgue.code_insee = row.get("code_insee")
                    orgue.ancienne_commune = row.get("ancienne_commune")
                    orgue.departement = row.get("departement")
                    orgue.code_departement = row.get("code_departement")
                    orgue.region = row.get("region")
                    orgue.osm_type = row.get("osm_type")
                    orgue.osm_id = row.get("osm_id")
                    orgue.diapason = row.get("diapason")
                    orgue.sommiers = row.get("sommiers")
                    orgue.soufflerie = row.get("soufflerie")
                    orgue.transmission_notes = row.get("transmission_notes")
                    orgue.transmission_commentaire = row.get("transmission_commentaire")
                    orgue.tirage_jeux = row.get("tirage_jeux")
                    orgue.tirage_commentaire = row.get("tirage_commentaire")
                    orgue.commentaire_tuyauterie = row.get("commentaire_tuyauterie")

                    orgue.slug = "orgue-{}-{}-{}".format(slugify(orgue.commune), slugify(orgue.edifice), orgue.pk)
                    if row["latitude"]:
                        orgue.latitude = float(row["latitude"])
                    if row["longitude"]:
                        orgue.longitude = float(row["longitude"])
                    orgue.save()

                    for nom in row.get("accessoires", []):
                        acc = Accessoire.objects.get(nom=nom)
                        orgue.accessoires.add(acc)

                    for evenement in row.get("evenements", []):
                        e = Evenement.objects.create(
                            annee=evenement.get("annee"),
                            type=evenement.get("type"),
                            resume=evenement.get("resume"),
                            orgue=orgue
                        )

                        for nom in evenement.get("facteurs"):
                            fac = Facteur.objects.get(nom=nom)
                            e.facteurs.add(fac)

                    for clavier in row.get("claviers", []):
                        type = TypeClavier.objects.get(nom=clavier["type"])
                        c = Clavier.objects.create(
                            type=type,
                            is_expressif=clavier.get("is_expressif"),
                            etendue=clavier.get("etendue"),
                            orgue=orgue
                        )
                        for jeu in clavier.get("jeux", []):
                            type = TypeJeu.objects.get(nom=jeu["type"]["nom"], hauteur=jeu["type"]["hauteur"])
                            Jeu.objects.create(
                                type=type,
                                commentaire=jeu.get("commentaire"),
                                clavier=c,
                                configuration=jeu.get("configuration"),
                            )

                    for image in row.get("images", []):
                        im = Image.objects.create(orgue=orgue, credit=image.get("credit"))
                        im.image.save(os.path.basename(image["chemin"]), File(open(image["chemin"], 'rb')))

                    for source in row.get("sources", []):
                        e = Source.objects.create(
                            type=source.get("type"),
                            description=source.get("description"),
                            lien=source.get("lien"),
                            orgue=orgue
                        )

                except Exception as e:
                    print("Erreur sur l'orgue {} : {}".format(row['codification'], str(e)))
