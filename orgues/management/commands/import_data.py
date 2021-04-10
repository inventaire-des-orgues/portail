import os
import json
import requests
import tempfile
import traceback

from tqdm import tqdm
from django.core.files import File
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from orgues.models import Orgue, Accessoire, Evenement, Facteur, TypeClavier, Clavier, Jeu, TypeJeu, Image, Source, Fichier


class Command(BaseCommand):
    help = 'Population initiale de la base de données avec les types'

    def add_arguments(self, parser):
        parser.add_argument('path', nargs=1, type=str,
                            help='Chemin vers le dossier contenant les orgues à importer')

        parser.add_argument('--delete', help='Supprime les orgues, jeux et claviers existants')

        parser.add_argument('--create', help='Crée les données si elle n\'existe pas (facteur, acessoires, typejeux, ...)')

        parser.add_argument('--codesfile', nargs=1, type=str,
                            help='Chemin vers le dossier contenant les codifications des orgues à ne pas effacer')

        parser.add_argument('--delete_lazy', nargs=1, type=str,
                            help='Efface toute les fiches peu renseignées (<20%)')

    def handle(self, *args, **options):

        if not os.path.exists(options['path'][0]):
            return "Path does not exist"
        if options['delete']:
            print('Effacement de tous les objets de la base.')
            Orgue.objects.all().delete()
            Clavier.objects.all().delete()
            Jeu.objects.all().delete()
        if options.get('codesfiles'):
            if not os.path.exists(options['codesfile'][0]):
                return "Path does not exist"
            with open(options['codesfile'][0], "r", encoding="utf-8") as f:
                print("Traitement d'une liste d'orgues à conserver.")
                codes = [ligne.rstrip('\n') for ligne in f.readlines()]
                deleted = Orgue.objects.exclude(codification__in=codes)
                count_del = deleted.count()
                print("J'efface {} orgues et en garde {}".format(str(count_del), str(len(codes))))
                deleted.delete()
        if options.get('delete_lazy'):
            print("Efface toute les fiches peu renseignées (<20%)")
            to_delete = Orgue.objects.filter(completion__lt=20)
            count_to_del = to_delete.count()
            print("J'efface {} orgues".format(str(count_to_del)))
            to_delete.delete()
        getFns = "get_or_create" if options.get("create") else "get"
        with open(options['path'][0], "r", encoding="utf-8") as f:
            print('Lecture JSON et import des orgues.')
            rows = json.load(f)
            for row in tqdm(rows):
                orgue, created = Orgue.objects.get_or_create(
                    codification=row["codification"],
                )
                try:
                    assert row.get("proprietaire") in [c[0] for c in Orgue.CHOIX_PROPRIETAIRE] + [None]
                    assert row.get("etat") in [c[0] for c in Orgue.CHOIX_ETAT] + [None]
                    assert row.get("tirage_jeux") in [c[0] for c in Orgue.CHOIX_TIRAGE] + [None]
                    assert row.get("transmission_notes") in [c[0] for c in Orgue.CHOIX_TRANSMISSION] + [None]
                    assert row.get("departement") in [c[1] for c in Orgue.CHOIX_DEPARTEMENT] + [None]
                    assert row.get("code_departement") in [c[0] for c in Orgue.CHOIX_DEPARTEMENT] + [None]
                    assert row.get("region") in [c[0] for c in Orgue.CHOIX_REGION] + [None]
                    assert row.get("osm_type") in [c[0] for c in Orgue.CHOIX_TYPE_OSM] + [None]

                    orgue.designation = row.get("designation")
                    orgue.references_palissy = row.get("references_palissy")
                    orgue.resume = row.get("resume")
                    orgue.proprietaire = row.get("proprietaire")
                    orgue.organisme = row.get("organisme")
                    orgue.lien_reference = row.get("lien_reference")
                    orgue.is_polyphone = row.get("is_polyphone")
                    orgue.etat = row.get("etat")
                    orgue.emplacement = row.get("emplacement")
                    orgue.buffet = row.get("buffet")
                    orgue.console = row.get("console")
                    orgue.commentaire_admin = row.get("commentaire_admin")
                    orgue.edifice = row.get("edifice")
                    orgue.commune = row.get("commune")
                    orgue.code_insee = row.get("code_insee")
                    orgue.ancienne_commune = row.get("ancienne_commune")
                    orgue.adresse = row.get("adresse")
                    orgue.departement = row.get("departement")
                    orgue.code_departement = row.get("code_departement")
                    orgue.region = row.get("region")
                    orgue.osm_type = row.get("osm_type")
                    orgue.osm_id = row.get("osm_id")
                    orgue.diapason = row.get("diapason")
                    orgue.sommiers = row.get("sommiers")
                    orgue.soufflerie = row.get("soufflerie")
                    orgue.transmission_notes = row.get("transmission_notes")
                    orgue.temperament = row.get("temperament")
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
                        if options.get("create"):
                            acc, created = Accessoire.objects.get_or_create(nom=nom)
                        else:
                            acc = Accessoire.objects.get(nom=nom)
                        orgue.accessoires.add(acc)

                    for nom in row.get("entretien", []):
                        facteur = Orgue.objects.get(entretien=nom)
                        orgue.entretien.add(facteur)

                    for evenement in row.get("evenements", []):
                        e = Evenement.objects.create(
                            annee=evenement.get("annee"),
                            type=evenement.get("type"),
                            resume=evenement.get("resume"),
                            orgue=orgue
                        )

                        for nom in evenement.get("facteurs"):
                            if options.get("create"):
                                fac, created = Facteur.objects.get_or_create(nom=nom)
                            else:
                                fac = Facteur.objects.get(nom=nom)
                            e.facteurs.add(fac)

                    for clavier in row.get("claviers", []):
                        if options.get("create"):
                            type_clavier, created = TypeClavier.objects.get_or_create(nom=clavier["type"])
                        else:
                            type_clavier = TypeClavier.objects.get(nom=clavier["type"])
                        c = Clavier.objects.create(
                            type=type_clavier,
                            is_expressif=clavier.get("is_expressif"),
                            etendue=clavier.get("etendue"),
                            orgue=orgue
                        )
                        for jeu in clavier.get("jeux", []):
                            if options.get("create"):
                                type_jeu, created = TypeJeu.objects.get_or_create(nom=jeu["type"]["nom"], hauteur=jeu["type"]["hauteur"])
                            else:
                                type_jeu = TypeJeu.objects.get(nom=jeu["type"]["nom"], hauteur=jeu["type"]["hauteur"])
                            Jeu.objects.create(
                                type=type_jeu,
                                commentaire=jeu.get("commentaire"),
                                clavier=c,
                                configuration=jeu.get("configuration"),
                            )

                    for image in row.get("images", []):
                        if "chemin" in image:
                            im = Image.objects.create(orgue=orgue, credit=image.get("credit"))
                            im.image.save(os.path.basename(image["chemin"]), File(open(image["chemin"], 'rb')))
                        if "url" in image:
                            r = requests.get(image["url"])
                            with tempfile.NamedTemporaryFile(prefix=orgue.slug, suffix=".jpg", mode="wb") as f:
                                f.write(r.content)
                                im = Image.objects.create(orgue=orgue, credit=image.get("credit"))
                                im.image.save(orgue.slug+"jpg", File(open(f.name, "rb")))

                    for source in row.get("sources", []):
                        Source.objects.create(
                            type=source.get("type"),
                            description=source.get("description"),
                            lien=source.get("lien"),
                            orgue=orgue
                        )

                    for fichier in row.get("fichiers", []):
                        Fichier.objects.create(
                            orgue=orgue,
                            file=fichier.get("file"),
                            description=fichier.get("description")
                        )

                except Exception as e:
                    tqdm.write("Erreur sur l'orgue {} : {}".format(row['codification'], str(e)))
