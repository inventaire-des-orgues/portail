import os
import sqlite3

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from orgues.models import (
    Accessoire, Clavier, Evenement, Facteur, Jeu, Manufacture,
    Orgue, Provenance, Source, TypeClavier, TypeJeu,
)


class Command(BaseCommand):
    help = "Restaure les informations d'un orgue depuis une ancienne sauvegarde SQLite3"

    def add_arguments(self, parser):
        parser.add_argument(
            "codification",
            type=str,
            help="Codification de l'orgue à restaurer",
        )
        parser.add_argument(
            "backup_db",
            type=str,
            help="Chemin vers le fichier SQLite3 de sauvegarde",
        )

    def handle(self, *args, **options):
        codification = options["codification"]
        backup_db_path = options["backup_db"]

        if not os.path.isfile(backup_db_path):
            raise CommandError(f"Fichier de sauvegarde introuvable : {backup_db_path}")

        conn = sqlite3.connect(backup_db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("SELECT * FROM orgues_orgue WHERE codification = ?", [codification])
        orgue_row = cur.fetchone()
        if orgue_row is None:
            conn.close()
            raise CommandError(
                f"Codification '{codification}' introuvable dans la sauvegarde."
            )

        try:
            orgue = Orgue.objects.get(codification=codification)
        except Orgue.DoesNotExist:
            conn.close()
            raise CommandError(
                f"Codification '{codification}' introuvable dans la base courante."
            )

        with transaction.atomic():
            self._restore_fields(orgue, orgue_row)
            self._restore_entretien(orgue, orgue_row["id"], cur)
            self._restore_accessoires(orgue, orgue_row["id"], cur)
            self._restore_claviers(orgue, orgue_row["id"], cur)
            self._restore_evenements(orgue, orgue_row["id"], cur)
            self._restore_sources(orgue, orgue_row["id"], cur)
            # Recalcul après restauration complète des claviers/jeux
            orgue.resume_composition = orgue.calcul_resume_composition()
            orgue.save()

        conn.close()
        self.stdout.write(
            self.style.SUCCESS(f"Orgue '{codification}' restauré avec succès.")
        )

    # ------------------------------------------------------------------
    def _restore_fields(self, orgue, row):
        """Restaure les champs scalaires de l'orgue."""
        fields = [
            "designation", "qualification_palissy", "is_polyphone",
            "references_palissy", "references_inventaire_regions",
            "lien_inventaire_regions", "resume", "proprietaire", "organisme",
            "lien_reference", "etat", "emplacement", "buffet", "console",
            "commentaire_admin", "edifice", "adresse", "commune", "code_insee",
            "ancienne_commune", "departement", "code_departement", "region",
            "latitude", "longitude", "osm_type", "osm_id", "diapason",
            "sommiers", "soufflerie", "transmission_notes",
            "transmission_commentaire", "tirage_jeux", "tirage_commentaire",
            "commentaire_tuyauterie", "temperament", "buffet_vide",
        ]
        for field in fields:
            try:
                setattr(orgue, field, row[field])
            except IndexError:
                self.stderr.write(f"  Champ absent de la sauvegarde : {field}")
        orgue.save()

    # ------------------------------------------------------------------
    def _restore_entretien(self, orgue, backup_orgue_id, cur):
        """Restaure les facteurs et manufactures en charge de l'entretien."""
        orgue.entretien.clear()
        cur.execute(
            "SELECT f.nom FROM orgues_orgue_entretien oe "
            "JOIN orgues_facteur f ON f.id = oe.facteur_id "
            "WHERE oe.orgue_id = ?",
            [backup_orgue_id],
        )
        for row in cur.fetchall():
            facteur = Facteur.objects.filter(nom=row["nom"]).first()
            if facteur:
                orgue.entretien.add(facteur)
            else:
                self.stderr.write(f"  Facteur entretien introuvable : {row['nom']}")

        orgue.entretienManufacture.clear()
        cur.execute(
            "SELECT m.nom FROM orgues_orgue_entretienManufacture oe "
            "JOIN orgues_manufacture m ON m.id = oe.manufacture_id "
            "WHERE oe.orgue_id = ?",
            [backup_orgue_id],
        )
        for row in cur.fetchall():
            manufacture = Manufacture.objects.filter(nom=row["nom"]).first()
            if manufacture:
                orgue.entretienManufacture.add(manufacture)
            else:
                self.stderr.write(f"  Manufacture entretien introuvable : {row['nom']}")

    # ------------------------------------------------------------------
    def _restore_accessoires(self, orgue, backup_orgue_id, cur):
        """Restaure les accessoires."""
        orgue.accessoires.clear()
        cur.execute(
            "SELECT a.nom FROM orgues_orgue_accessoires oa "
            "JOIN orgues_accessoire a ON a.id = oa.accessoire_id "
            "WHERE oa.orgue_id = ?",
            [backup_orgue_id],
        )
        for row in cur.fetchall():
            accessoire = Accessoire.objects.filter(nom=row["nom"]).first()
            if accessoire:
                orgue.accessoires.add(accessoire)
            else:
                self.stderr.write(f"  Accessoire introuvable : {row['nom']}")

    # ------------------------------------------------------------------
    def _restore_claviers(self, orgue, backup_orgue_id, cur):
        """Supprime les claviers actuels et les recrée depuis la sauvegarde."""
        orgue.claviers.all().delete()

        cur.execute(
            "SELECT c.*, t.nom AS type_nom "
            "FROM orgues_clavier c "
            "JOIN orgues_typeclavier t ON t.id = c.type_id "
            "WHERE c.orgue_id = ?",
            [backup_orgue_id],
        )
        clavier_rows = cur.fetchall()

        # Correspondance id backup → objet Clavier courant (pour les emprunts de jeux)
        clavier_map = {}

        for crow in clavier_rows:
            type_clavier = TypeClavier.objects.filter(nom=crow["type_nom"]).first()
            if type_clavier is None:
                self.stderr.write(f"  TypeClavier introuvable : {crow['type_nom']}, clavier ignoré.")
                continue
            clavier = Clavier.objects.create(
                orgue=orgue,
                type=type_clavier,
                is_expressif=bool(crow["is_expressif"]),
                etendue=crow["etendue"],
                commentaire=crow["commentaire"],
            )
            clavier_map[crow["id"]] = clavier

        # Jeux : deux passes pour gérer les emprunts
        jeu_map = {}
        cur.execute(
            "SELECT j.*, t.nom AS type_nom, t.hauteur AS type_hauteur "
            "FROM orgues_jeu j "
            "JOIN orgues_typejeu t ON t.id = j.type_id "
            "WHERE j.clavier_id IN ({})".format(
                ",".join(str(k) for k in clavier_map) or "NULL"
            )
        )
        jeu_rows = cur.fetchall()

        # Première passe : jeux sans emprunt
        for jrow in jeu_rows:
            if jrow["emprunt_id"] is not None:
                continue
            if jrow["clavier_id"] not in clavier_map:
                continue
            type_jeu = TypeJeu.objects.filter(
                nom=jrow["type_nom"], hauteur=jrow["type_hauteur"]
            ).first()
            if type_jeu is None:
                type_jeu = TypeJeu.objects.filter(nom=jrow["type_nom"]).first()
            if type_jeu is None:
                self.stderr.write(f"  TypeJeu introuvable : {jrow['type_nom']} {jrow['type_hauteur']}, jeu ignoré.")
                continue
            jeu = Jeu.objects.create(
                clavier=clavier_map[jrow["clavier_id"]],
                type=type_jeu,
                commentaire=jrow["commentaire"],
                configuration=jrow["configuration"],
            )
            jeu_map[jrow["id"]] = jeu

        # Deuxième passe : jeux avec emprunt
        for jrow in jeu_rows:
            if jrow["emprunt_id"] is None:
                continue
            if jrow["clavier_id"] not in clavier_map:
                continue
            type_jeu = TypeJeu.objects.filter(
                nom=jrow["type_nom"], hauteur=jrow["type_hauteur"]
            ).first()
            if type_jeu is None:
                type_jeu = TypeJeu.objects.filter(nom=jrow["type_nom"]).first()
            if type_jeu is None:
                self.stderr.write(f"  TypeJeu introuvable : {jrow['type_nom']}, jeu ignoré.")
                continue
            emprunt = jeu_map.get(jrow["emprunt_id"])
            Jeu.objects.create(
                clavier=clavier_map[jrow["clavier_id"]],
                type=type_jeu,
                commentaire=jrow["commentaire"],
                configuration=jrow["configuration"],
                emprunt=emprunt,
            )

    # ------------------------------------------------------------------
    def _restore_evenements(self, orgue, backup_orgue_id, cur):
        """Supprime les événements actuels et les recrée depuis la sauvegarde."""
        orgue.evenements.all().delete()

        cur.execute(
            "SELECT * FROM orgues_evenement WHERE orgue_id = ?",
            [backup_orgue_id],
        )
        for erow in cur.fetchall():
            provenance = None
            if erow["provenance_id"] is not None:
                cur.execute(
                    "SELECT * FROM orgues_provenance WHERE id = ?",
                    [erow["provenance_id"]],
                )
                prow = cur.fetchone()
                if prow:
                    provenance, _ = Provenance.objects.get_or_create(
                        edifice=prow["edifice"],
                        commune=prow["commune"],
                        departement=prow["departement"],
                        code_departement=prow["code_departement"],
                        region=prow["region"],
                    )

            evenement = Evenement.objects.create(
                orgue=orgue,
                annee=erow["annee"],
                annee_fin=erow["annee_fin"],
                circa=bool(erow["circa"]),
                type=erow["type"],
                resume=erow["resume"],
                provenance=provenance,
            )

            # Facteurs de l'événement
            cur.execute(
                "SELECT f.nom FROM orgues_evenement_facteurs ef "
                "JOIN orgues_facteur f ON f.id = ef.facteur_id "
                "WHERE ef.evenement_id = ?",
                [erow["id"]],
            )
            for frow in cur.fetchall():
                facteur = Facteur.objects.filter(nom=frow["nom"]).first()
                if facteur:
                    evenement.facteurs.add(facteur)
                else:
                    self.stderr.write(f"  Facteur introuvable : {frow['nom']}")

            # Manufactures de l'événement
            cur.execute(
                "SELECT m.nom FROM orgues_evenement_manufactures em "
                "JOIN orgues_manufacture m ON m.id = em.manufacture_id "
                "WHERE em.evenement_id = ?",
                [erow["id"]],
            )
            for mrow in cur.fetchall():
                manufacture = Manufacture.objects.filter(nom=mrow["nom"]).first()
                if manufacture:
                    evenement.manufactures.add(manufacture)
                else:
                    self.stderr.write(f"  Manufacture introuvable : {mrow['nom']}")

    # ------------------------------------------------------------------
    def _restore_sources(self, orgue, backup_orgue_id, cur):
        """Supprime les sources actuelles et les recrée depuis la sauvegarde."""
        orgue.sources.all().delete()

        cur.execute(
            "SELECT * FROM orgues_source WHERE orgue_id = ?",
            [backup_orgue_id],
        )
        for srow in cur.fetchall():
            Source.objects.create(
                orgue=orgue,
                type=srow["type"],
                description=srow["description"],
                lien=srow["lien"] or "",
            )
