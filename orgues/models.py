import os
import re
import uuid

import meilisearch
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.urls import reverse
from django.utils.text import slugify
from imagekit.models import ImageSpecField, ProcessedImageField
from pilkit.processors import ResizeToFill, ResizeToFit, Transpose
from PIL import Image as PilImage
from django import forms

from accounts.models import User


class Facteur(models.Model):
    """
    Pas celui qui distribue le courrier
    """
    nom = models.CharField(max_length=100)
    latitude_atelier = models.FloatField(null=True, blank=True, verbose_name="Latitude de l'atelier")
    longitude_atelier = models.FloatField(null=True, blank=True, verbose_name="Longitude de l'atelier")
    updated_by_user = models.ForeignKey(User, null=True, editable=False, on_delete=models.SET_NULL)

    def __str__(self):
        return self.nom

    class Meta:
        ordering = ['latitude_atelier']


class Orgue(models.Model):
    CHOIX_TYPE_OSM = (
        ("node", "Nœud (Node)"),
        ("way", "Chemin (Way)"),
        ("relation", "Relation (Relation)"),
    )

    CHOIX_PROPRIETAIRE = (
        ("commune", "Commune"),
        ("interco", "Intercommunalité"),
        ("etat", "Etat"),
        ("association_culturelle", "Association culturelle"),
        ("diocese", "Diocèse"),
        ("paroisse", "Paroisse"),
        ("congregation", "Congrégation"),
        ("etablissement_scolaire", "Etablissement scolaire"),
        ("conservatoire", "Conservatoire ou Ecole de musique"),
        ("hopital", "Hôpital"),
    )

    CHOIX_ETAT = (
        ('tres_bon', "Très bon, tout à fait jouable"),
        ('bon', "Bon : jouable, défauts mineurs"),
        ('altere', "Altéré : difficilement jouable"),
        ('degrade', "Dégradé ou en ruine : injouable"),
        ('restauration', "En restauration (ou projet initié)")
    )

    CHOIX_TRANSMISSION = (
        ("mecanique", "Mécanique"),
        ("mecanique_suspendue", "Mécanique suspendue"),
        ("mecanique_balanciers", "Mécanique à balanciers"),
        ("mecanique_barker", "Mécanique Barker"),
        ("numerique", "Numérique"),
        ("electrique", "Electrique"),
        ("electrique_proportionnelle", "Electrique proportionnelle"),
        ("electro_pneumatique", "Electro-pneumatique"),
        ("pneumatique", "Pneumatique"),
    )

    CHOIX_TIRAGE = (
        ("mecanique", "Mécanique"),
        ("pneumatique_haute_pression", "Pneumatique haute pression"),
        ("pneumatique_basse_pression", "Pneumatique basse pression"),
        ("numerique", "Numérique"),
        ("electrique", "Electrique"),
        ("electro_pneumatique", "Electro-pneumatique"),
    )

    CHOIX_REGION = (
        ('Auvergne-Rhône-Alpes', 'Auvergne-Rhône-Alpes'),
        ('Bourgogne-Franche-Comté', 'Bourgogne-Franche-Comté'),
        ('Bretagne', 'Bretagne'),
        ('Centre-Val de Loire', 'Centre-Val de Loire'),
        ('Corse', 'Corse'),
        ('Grand Est', 'Grand Est'),
        ('Guadeloupe', 'Guadeloupe'),
        ('Guyane', 'Guyane'),
        ('Hauts-de-France', 'Hauts-de-France'),
        ('Île-de-France', 'Île-de-France'),
        ('La Réunion', 'La Réunion'),
        ('Martinique', 'Martinique'),
        ('Normandie', 'Normandie'),
        ('Nouvelle-Aquitaine', 'Nouvelle-Aquitaine'),
        ('Nouvelle-Calédonie', 'Nouvelle-Calédonie'),
        ('Occitanie', 'Occitanie'),
        ('Pays de la Loire', 'Pays de la Loire'),
        ("Provence-Alpes-Côte d'Azur", "Provence-Alpes-Côte d'Azur"),
        ('Saint-Pierre-et-Miquelon', 'Saint-Pierre-et-Miquelon')
    )

    CHOIX_DEPARTEMENT = (
        ('01', 'Ain'),
        ('02', 'Aisne'),
        ('03', 'Allier'),
        ('04', 'Alpes-de-Haute-Provence'),
        ('05', 'Hautes-Alpes'),
        ('06', 'Alpes-Maritimes'),
        ('07', 'Ardèche'),
        ('08', 'Ardennes'),
        ('09', 'Ariège'),
        ('10', 'Aube'),
        ('11', 'Aude'),
        ('12', 'Aveyron'),
        ('13', 'Bouches-du-Rhône'),
        ('14', 'Calvados'),
        ('15', 'Cantal'),
        ('16', 'Charente'),
        ('17', 'Charente-Maritime'),
        ('18', 'Cher'),
        ('19', 'Corrèze'),
        ('2A', 'Corse-du-Sud'),
        ('2B', 'Haute-Corse'),
        ("21", "Côte-d'Or"),
        ("22", "Côtes-d'Armor"),
        ('23', 'Creuse'),
        ('24', 'Dordogne'),
        ('25', 'Doubs'),
        ('26', 'Drôme'),
        ('27', 'Eure'),
        ('28', 'Eure-et-Loir'),
        ('29', 'Finistère'),
        ('30', 'Gard'),
        ('31', 'Haute-Garonne'),
        ('32', 'Gers'),
        ('33', 'Gironde'),
        ('34', 'Hérault'),
        ('35', 'Ille-et-Vilaine'),
        ('36', 'Indre'),
        ('37', 'Indre-et-Loire'),
        ('38', 'Isère'),
        ('39', 'Jura'),
        ('40', 'Landes'),
        ('41', 'Loir-et-Cher'),
        ('42', 'Loire'),
        ('43', 'Haute-Loire'),
        ('44', 'Loire-Atlantique'),
        ('45', 'Loiret'),
        ('46', 'Lot'),
        ('47', 'Lot-et-Garonne'),
        ('48', 'Lozère'),
        ('49', 'Maine-et-Loire'),
        ('50', 'Manche'),
        ('51', 'Marne'),
        ('52', 'Haute-Marne'),
        ('53', 'Mayenne'),
        ('54', 'Meurthe-et-Moselle'),
        ('55', 'Meuse'),
        ('56', 'Morbihan'),
        ('57', 'Moselle'),
        ('58', 'Nièvre'),
        ('59', 'Nord'),
        ('60', 'Oise'),
        ('61', 'Orne'),
        ('62', 'Pas-de-Calais'),
        ('63', 'Puy-de-Dôme'),
        ('64', 'Pyrénées-Atlantiques'),
        ('65', 'Hautes-Pyrénées'),
        ('66', 'Pyrénées-Orientales'),
        ('67', 'Bas-Rhin'),
        ('68', 'Haut-Rhin'),
        ('69', 'Rhône'),
        ('70', 'Haute-Saône'),
        ('71', 'Saône-et-Loire'),
        ('72', 'Sarthe'),
        ('73', 'Savoie'),
        ('74', 'Haute-Savoie'),
        ('75', 'Paris'),
        ('76', 'Seine-Maritime'),
        ('77', 'Seine-et-Marne'),
        ('78', 'Yvelines'),
        ('79', 'Deux-Sèvres'),
        ('80', 'Somme'),
        ('81', 'Tarn'),
        ('82', 'Tarn-et-Garonne'),
        ('83', 'Var'),
        ('84', 'Vaucluse'),
        ('85', 'Vendée'),
        ('86', 'Vienne'),
        ('87', 'Haute-Vienne'),
        ('88', 'Vosges'),
        ('89', 'Yonne'),
        ('90', 'Territoire de Belfort'),
        ('91', 'Essonne'),
        ('92', 'Hauts-de-Seine'),
        ('93', 'Seine-Saint-Denis'),
        ('94', 'Val-de-Marne'),
        ("95", "Val-d'Oise"),
        ('971', 'Guadeloupe'),
        ('972', 'Martinique'),
        ('976', 'Mayotte'),
        ('973', 'Guyane'),
        ('974', 'La Réunion'),
        ('975', 'Saint-Pierre-et-Miquelon'),
        ('988', 'Nouvelle-Calédonie'),

    )

    # Informations générales
    designation = models.CharField(max_length=300, null=True, verbose_name="Désignation de l'orgue", default="orgue",
                                   blank=True, help_text="Type d'orgue : grand orgue, orgue coffre, orgue portatif, etc.")
    is_polyphone = models.BooleanField(default=False, verbose_name="Orgue polyphone de la manufacture Debierre ?")
    codification = models.CharField(max_length=24, unique=True, db_index=True)
    references_palissy = models.CharField(max_length=60, null=True, blank=True,
                                          verbose_name="Référence(s) Palissy pour les monuments historiques.",
                                          help_text="Séparer les codes par des virgules.")
    references_inventaire_regions = models.CharField(verbose_name="Code inventaire régional", max_length=60, null=True, blank=True)
    resume = models.TextField(max_length=500, null=True, verbose_name="Résumé", blank=True,
                              help_text="Présentation en quelques lignes de l'instrument \
                              en insistant sur son originalité (max 500 caractères).")
    proprietaire = models.CharField(max_length=40, null=True, choices=CHOIX_PROPRIETAIRE, default="commune",
                                    verbose_name="Propriétaire")
    organisme = models.CharField(verbose_name="Organisme auquel s'adresser", max_length=100, null=True, blank=True,
                                 help_text="Notamment pour accéder à l'instrument.")
    lien_reference = models.URLField(verbose_name="Lien de référence", max_length=300, null=True, blank=True,
                                     help_text="Lien internet de l'organisme auquel s'adresser.")

    entretien = models.ManyToManyField(Facteur, blank=True, verbose_name="Facteur en charge de l'entretien")

    etat = models.CharField(max_length=20, choices=CHOIX_ETAT, null=True, blank=True,
                            help_text="Se rapporte au fait que l'orgue est jouable ou non.")
    emplacement = models.CharField(max_length=60, null=True, blank=True, verbose_name="Emplacement",
                                   help_text="Emplacement dans l'édifice : sol, tribune, crypte ...")
    buffet = models.TextField(verbose_name="Description du buffet", null=True, blank=True,
                              help_text="Description du buffet et de son état.")
    console = models.TextField(verbose_name="Description de la console", null=True, blank=True,
                               help_text="Description de la console (ex: en fenêtre, \
                               séparée organiste tourné vers l'orgue ...).")

    commentaire_admin = models.TextField(verbose_name="Commentaire contributeurs", null=True, blank=True,
                                         help_text="Commentaire uniquement visible par les contributeurs.")

    # Localisation
    code_dep_validator = RegexValidator(regex='^(97[12346]|0[1-9]|[1-8][0-9]|9[0-5]|2[AB])$',
                                        message="Renseigner un code de département valide")

    edifice = models.CharField(max_length=300)
    adresse = models.CharField(max_length=300, null=True, blank=True)
    commune = models.CharField(max_length=100)
    code_insee = models.CharField(max_length=5, verbose_name="Code_INSEE")
    ancienne_commune = models.CharField(max_length=100, null=True, blank=True)
    departement = models.CharField(verbose_name="Département", choices=[(c[1], c[1]) for c in CHOIX_DEPARTEMENT],
                                   max_length=50)
    code_departement = models.CharField(choices=[(c[0], c[0]) for c in CHOIX_DEPARTEMENT],
                                        verbose_name="Code département", max_length=3)
    region = models.CharField(verbose_name="Région", choices=CHOIX_REGION, max_length=50)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    osm_type = models.CharField(choices=CHOIX_TYPE_OSM, verbose_name="Type OpenStreetMap", max_length=20, null=True,
                                blank=True, help_text="Type OSM de l'objet représenant l'édifice.")
    osm_id = models.CharField(verbose_name="Id OpenStreetMap", max_length=20, null=True, blank=True,
                              help_text="Identifiant OSM de l'objet décrivant l'édifice.")

    # Partie instrumentale
    diapason = models.CharField(max_length=20, null=True, blank=True,
                                help_text="Hauteur en Hertz du A2 joué par le prestant 4, à une température donnée.")
    sommiers = models.TextField(null=True, blank=True)
    soufflerie = models.TextField(null=True, blank=True)
    transmission_notes = models.CharField(verbose_name="Transmission des notes",
                                          max_length=30,
                                          choices=CHOIX_TRANSMISSION,
                                          null=True, blank=True)
    temperament = models.CharField(verbose_name="Tempérament",
                                   max_length=50,
                                   help_text="Mention la plus précise possible. Ex: mésotonique au sixième modifié.",
                                   null=True, blank=True)
    transmission_commentaire = models.CharField(max_length=100, null=True, blank=True, help_text="Max 100 caractères.")
    tirage_jeux = models.CharField(verbose_name="Tirage des jeux", max_length=30, choices=CHOIX_TIRAGE, null=True,
                                   blank=True)
    tirage_commentaire = models.CharField(max_length=100, null=True, blank=True, help_text="Max 100 caractères.")
    commentaire_tuyauterie = models.TextField(verbose_name="Description de la tuyauterie", blank=True, null=True)
    accessoires = models.ManyToManyField('Accessoire', blank=True, help_text="Nous contacter si un accessoire manque.")

    # Auto générés
    created_date = models.DateTimeField(auto_now_add=True, auto_now=False, verbose_name='Creation date')
    modified_date = models.DateTimeField(auto_now=True, auto_now_add=False, verbose_name='Update date')
    updated_by_user = models.ForeignKey(User, null=True, editable=False, on_delete=models.SET_NULL)
    uuid = models.UUIDField(db_index=True, default=uuid.uuid4, unique=True, editable=False)
    slug = models.SlugField(max_length=255, editable=False, null=True, blank=True)
    completion = models.IntegerField(default=False, editable=False)
    resume_composition = models.CharField(max_length=30, null=True, blank=True, editable=False)

    def __str__(self):
        return "{} {} {}".format(self.designation, self.edifice, self.commune)

    class Meta:
        ordering = ['-created_date']
        permissions = [
            ('edition_avancee', "Peut modifier les champs structurels d'un orgue (ex : code_insee ...)")
        ]

    def save(self, *args, **kwargs):
        """
        Le calcul de l'avancement se fait à chaque nouvel enregistrement
        """
        self.completion = self.calcul_completion()
        if not self.slug:
            self.slug = slugify("orgue-{}-{}-{}".format(self.commune, self.edifice, self.codification))
        super().save(*args, **kwargs)

    @property
    def is_expressif(self):
        """
        Un orgue est expressif si au moins un de ses claviers l'est
        """
        return self.claviers.filter(is_expressif=True).exists()

    @property
    def vignette(self):
        """
        Récupère la vignette l'instrument, ou une vignette par défaut si elle n'existe pas
        """
        image_principale = self.image_principale
        if not image_principale:
            return "/static/img/default.png"
        elif image_principale.thumbnail_principale:
            return image_principale.thumbnail_principale.url
        elif image_principale.thumbnail:
            return image_principale.thumbnail.url

    @property
    def image_principale(self):
        """
        Récupère l'image principale de l'instrument
        """
        return self.images.filter(is_principale=True).first()

    @property
    def has_pedalier(self):
        """
        Est-ce que l'instrument possède un pédalier ?
        """
        return self.claviers.filter(type__nom__in=['Pédale', 'Pédalier', 'Pedalwerk', 'Pedal', 'Pedalero', 'Pedaliera']).exists()

    @property
    def construction(self):
        """
        Evenement de construction de l'orgue (contient année et facteur)
        """
        return self.evenements.filter(type="construction").first()

    @property
    def jeux_count(self):
        """
        Nombre de jeux de l'instrument
        """
        return Jeu.objects.filter(clavier__orgue=self).count()

    @property
    def liens_pop(self):
        """
        Liens vers le site des classements du patrimoine mobilier (PM) du ministère de la culture
        """
        liens = []

        if not self.references_palissy:
            return liens

        for reference in self.references_palissy.split(","):
            reference = reference.strip()
            if reference:
                liens.append(
                    {
                        "href": "https://www.pop.culture.gouv.fr/notice/palissy/" + reference,
                        "title": reference
                    }
                )
        return liens

    def get_absolute_url(self):
        return reverse('orgues:orgue-detail', args=(self.slug,))

    def get_short_url(self):
        return reverse('orgues:orgue-detail', args=(self.codification,))

    def get_update_url(self):
        return reverse('orgues:orgue-update', args=(self.uuid,))

    def get_delete_url(self):
        return reverse('orgues:orgue-delete', args=(self.uuid,))

    def calcul_resume_composition(self):
        """
        On stocke dans la base de données l'information Clavier et Pédale de façon commune, sous le format :
        [nombre de claviers en chiffres romains]["/P" si Pédale]
        """

        has_pedalier = self.has_pedalier
        claviers_count = self.claviers.count()
        jeux_count = self.jeux_count
        cr = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII", "XIV", "XV",
              "XVI", "XVII", "XVIII", "XIX", "XX", "XXI", "XXII", "XXIII", "XIV", "XV"]
        if claviers_count == 0:
            return

        if has_pedalier and claviers_count > 1:
            return "{}, {}/P".format(jeux_count, cr[claviers_count - 2])

        elif has_pedalier and claviers_count == 1:
            return "{}, P".format(jeux_count)

        return "{}, {}".format(jeux_count, cr[claviers_count - 1])

    def infos_completions(self):
        """
        Informations et liens pour comprendre le calcul du taux d'avancement
        """
        return {
            "Commune définie": {
                "points": 5,
                "logique": bool(self.commune),
                "lien": reverse('orgues:orgue-update-localisation', args=(self.uuid,))
            },
            "Région définie": {
                "points": 0,
                "logique": bool(self.region),
                "lien": reverse('orgues:orgue-update-localisation', args=(self.uuid,)),
            },
            "Département défini": {
                "points": 5,
                "logique": bool(self.departement),
                "lien": reverse('orgues:orgue-update-localisation', args=(self.uuid,))
            },
            "Nom de l'édifice défini": {
                "points": 15,
                "logique": len(self.edifice) > 6,
                "lien": reverse('orgues:orgue-update', args=(self.uuid,)) + "#id_edifice"
            },
            "Etat de l'orgue défini": {
                "points": 20,
                "logique": bool(self.etat),
                "lien": reverse('orgues:orgue-update-localisation', args=(self.uuid,)) + "#id_etat"
            },
            "Image principale définie": {
                "points": 30,
                "logique": self.images.filter(is_principale=True).exists(),
                "lien": reverse('orgues:image-list', args=(self.uuid,))
            },
            "Au moins un clavier": {
                "points": 20,
                "logique": self.claviers.count() >= 1,
                "lien": reverse('orgues:orgue-update-composition', args=(self.uuid,))
            },
            "Résumé de l'orgue complété": {
                "points": 10,
                "logique": bool(self.resume),
                "lien": reverse('orgues:orgue-update', args=(self.uuid,)) + "#id_resume"
            },
            "Informations sur le buffet présentes": {
                "points": 10,
                "logique": bool(self.buffet),
                "lien": reverse('orgues:orgue-update-buffet', args=(self.uuid,))
            },
            "Informations sur les sommiers présentes": {
                "points": 0,
                "logique": bool(self.sommiers),
                "lien": reverse('orgues:orgue-update-instrumentale', args=(self.uuid,)) + "#id_sommiers"
            },
            "Informations sur la soufflerie présentes": {
                "points": 10,
                "logique": bool(self.soufflerie),
                "lien": reverse('orgues:orgue-update-instrumentale', args=(self.uuid,)) + "#id_soufflerie "
            }
        }

    def calcul_completion(self):
        """
        Pourcentage de remplissage de la fiche instrument
        """
        score_max = 0
        score_courant = 0
        for key, value in self.infos_completions().items():
            if value["logique"]:
                score_courant += value["points"]
            score_max += value["points"]
        return int(100 * score_courant / score_max)


class TypeClavier(models.Model):
    """
    Type de clavier
    Ex :
    Grand Orgue
    Récit
    Pédalier
    """
    nom = models.CharField(max_length=100)

    def __str__(self):
        return self.nom

    class Meta:
        verbose_name = "Type de clavier"
        verbose_name_plural = "Types de claviers"


def validate_etendue(value):
    if not re.match("^(([CDEFGAB][#♭]?)+)([0-7])-([CDEFGAB][#♭]?)([1-8])$", value):

        raise ValidationError("De la forme F1-G5. Absence du premier Ut dièse notée CD1-F5.")
    notes = count_notes(value)
    if notes is None:
        raise ValidationError("L'etendue du clavier est invalide.")
    if notes <= 0:
        raise ValidationError("L'etendue du clavier est invalide, borne inversées.")
    if notes < 5:
        raise ValidationError("L'etendue du clavier est invalide, moins de 5 notes.")
    if notes > 88:
        raise ValidationError("L'etendue du clavier est invalide, trop de notes.")


def note_to_hauteur(value):
    """
    Prend le nom d'une note et retourne la hauteur de la note :
    C = 0
    """
    etendu_diese = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    etendu_bemole = ['B#', 'D♭', 'D', 'E♭', 'F♭', 'E#', 'G♭', 'G', 'A♭', 'A', 'B♭', 'C♭']
    return etendu_diese.index(value) if value in etendu_diese else etendu_bemole.index(value)


def count_notes(etendu):
    """
    Retourne le nombre de note en fonction d'une étendu de clavier de la forme :
    Groupe de note initiale (format internationnal CDEFGAB suivit eventuellement d'un #)
    L'octave initiale
    Un tiret de séparation -
    Une note et une octave finale

    IE:
    C1-G5
    CD1-G5
    CFDGEAA#BC1-C4 : Octave courte italienne : Do Fa Ré Sol Mi La Sib Si Do
    """
    val = re.match(r"""^
    #Premier groupe Suite de Note (ABDC#) avec une note final et un octave
    (?P<notes> # Bloc contenant toutes les notes
        (?P<startNote>[CDEFGAB][#♭]?) # Match une note (et garde en mémoire la dernière)
    +)
    (?P<start>[0-7]) # Octave de début
    -
    (?P<endNote>[CDEFGAB][#♭]?)(?P<end>[1-8]) # Deuxième groupe Une note et une octave de fin
    $""", etendu, re.X)
    if not val:
        raise ValidationError("Etendue vide")

    start = note_to_hauteur(val.group("startNote")) + (int(val.group("start")) * 12)
    end = note_to_hauteur(val.group("endNote")) + (int(val.group("end")) * 12)
    # Compte le nombre de note dans le groupe de note initiale
    notes = len(re.findall(r'([ABCDEFG]#?)', val.group('notes')))
    count = end - start + notes
    if count <= 0:
        raise ValidationError("Etendue inversé")
    if count < 5:
        raise ValidationError("Clavier court")
    return end - start + notes


class Clavier(models.Model):
    """
    Un orgue peut avoir plusieurs claviers et un pédalier.
    """

    type = models.ForeignKey(TypeClavier, verbose_name="Nom", null=True, on_delete=models.CASCADE, db_index=True)
    is_expressif = models.BooleanField(verbose_name="Cocher si expressif", default=False)
    etendue = models.CharField(validators=[validate_etendue], max_length=10, null=True, blank=True,
                               help_text="De la forme F1-G5, CD1-G5 (pour absence premier Ut dièse), FGC1-G5 (pour un ravalement), ...")
    commentaire = models.CharField(max_length=200, null=True, blank=True,
                                   help_text="Particularités specifiques du clavier (transmission, ravalement, etc.)")

    # Champs automatiques
    orgue = models.ForeignKey(Orgue, null=True, on_delete=models.CASCADE, related_name="claviers", db_index=True)
    created_date = models.DateTimeField(
        auto_now_add=True,
        auto_now=False,
        verbose_name='Creation date'
    )
    modified_date = models.DateTimeField(
        auto_now=True,
        auto_now_add=False,
        verbose_name='Update date'
    )

    @property
    def expressif(self):
        """
        Affiche le terme expressif en fonction du type de clavier
        """
        if self.is_expressif:
            return "expressive" if self.type.nom in ["Pédale", "Bombarde", "Résonnance"] else "expressif"
        return ""

    @property
    def notes(self):
        """
        Retourne le nombre de notes en fonction de l'étendu du clavier
        """
        try:
            return count_notes(self.etendue)
        except:
            return None

    def save(self, *args, **kwargs):
        self.orgue.completion = self.orgue.calcul_completion()
        super().save(*args, **kwargs)

    def __str__(self):
        return "{} | {}".format(self.type.nom, self.orgue.designation)

    class Meta:
        verbose_name = "Plan sonore"


class Evenement(models.Model):
    """
    Décrit les différents événements relatifs à un orgue

    Les événements sont affichés via le plugin : https://timeline.knightlab.com/

    Relavage : simple opération de conservation de l'instrument, menée à intervalles réguliers.
    Reconstruction : des éléments nouveaux sont ajoutés en grand nombre, la structure de l'instrument est modifiée.
    Restauration : opération d'importance, à caractère patrimonial visant à retrouver un état antérieur de l'instrument.
    Destruction : dégâts sur l'ensemble de l'instrument, rendu totalement inutilisable.
    Disparition : distincte de destruction, car l'orgue a pu connaître un déménagement, ou être stocké.

    """

    CHOIX_TYPE = (
        ("construction", "Construction"),
        ("inauguration", "Inauguration"),
        ("reconstruction", "Reconstruction"),
        ("destruction", "Destruction"),
        ("restauration", "Restauration"),
        ("deplacement", "Déplacement"),
        ('demontage', "Démontage et stockage"),
        ("relevage", "Relevage"),
        ("modifications", "Modifications"),
        ("disparition", "Disparition"),
        ("degats", "Dégâts"),
        ("classement_mh", "Classement au titre des monuments historiques"),
        ("inscription_mh", "Inscription au titre des monuments historiques"),
    )

    annee = models.IntegerField(verbose_name="Année de début de l'évènement")
    annee_fin = models.IntegerField(verbose_name="Année de fin de l'évènement", null=True, blank=True,
                                    help_text="Optionnelle")
    circa = models.BooleanField(default=False, verbose_name="Cocher si dates approximatives")
    type = models.CharField(max_length=20, choices=CHOIX_TYPE)
    facteurs = models.ManyToManyField(Facteur, blank=True, related_name="evenements")
    resume = models.TextField(verbose_name="Résumé", max_length=700, blank=True, null=True,
                              help_text="700 caractères max")

    # Champs automatiques
    orgue = models.ForeignKey(Orgue, on_delete=models.CASCADE, related_name="evenements")

    @property
    def dates(self):
        """
        Logique d'affichage des dates
        """
        result = str(self.annee)
        if self.circa:
            result = "~" + result
        if self.annee_fin and self.annee_fin != self.annee:
            result += "-{}".format(self.annee_fin)
        return result

    @property
    def is_locked(self):
        return self.type in ["classement_mh", "inscription_mh"]

    def __str__(self):
        return "{} ({})".format(self.type, self.dates)

    class Meta:
        ordering = ["annee"]


class TypeJeu(models.Model):
    """
    Lorsque l'on définit les jeux d'un clavier, on pioche parmi les types de jeu existants
    """
    nom = models.CharField(max_length=50)
    hauteur = models.CharField(max_length=20, null=True, blank=True,
                               help_text="La hauteur est indiquée par convention en pieds, en chiffres arabes, "
                                         "sans précision de l'unité. La nombre de rangs des fournitures, plein-jeux,"
                                         " cornet, etc. est indiqué en chiffres romains,"
                                         " sans précision du terme \"rangs\" (ni \"rgs\").")

    created_date = models.DateTimeField(auto_now_add=True, auto_now=False, verbose_name='Creation date')
    modified_date = models.DateTimeField(auto_now=True, auto_now_add=False, verbose_name='Update date')
    updated_by_user = models.ForeignKey(User, null=True, editable=False, on_delete=models.SET_NULL)

    def __str__(self):
        return "{} {}".format(self.nom, self.hauteur)

    class Meta:
        verbose_name_plural = "Types de jeux"


class Jeu(models.Model):
    """
    Un Jeu est un TypeJeu associé à un clavier
    """
    CHOIX_CONFIGURATION = (
        ('basse', 'Basse'),
        ('dessus', 'Dessus'),
        ('basse_et_dessus', 'Basse et Dessus séparés')
    )

    type = models.ForeignKey(TypeJeu, on_delete=models.CASCADE, related_name='jeux', db_index=True)
    commentaire = models.CharField(max_length=200, null=True, blank=True)
    clavier = models.ForeignKey(Clavier, null=True, on_delete=models.CASCADE, related_name="jeux", db_index=True)
    configuration = models.CharField(max_length=20, choices=CHOIX_CONFIGURATION, null=True, blank=True)

    def __str__(self):
        if self.configuration == "basse":
            return "{} (B)".format(self.type)
        elif self.configuration == "dessus":
            return "{} (D)".format(self.type)
        return str(self.type)

    class Meta:
        verbose_name_plural = "Jeux"


def chemin_fichier(instance, filename):
    return os.path.join(str(instance.orgue.code_departement), instance.orgue.codification, "fichiers", filename)


class Source(models.Model):
    """
    Source bibliographique ou discographique.
    """
    CHOIX_SOURCE = (
        ("disque", "Disque"),
        ("web", "Web"),
        ("ouvrage", "Ouvrage"),
        ("video", "Video"),
    )

    type = models.CharField(max_length=20, verbose_name="Type de source", choices=CHOIX_SOURCE)
    description = models.CharField(max_length=100, verbose_name="Description de la source", blank=False)
    lien = models.URLField(max_length=200, verbose_name="Lien", blank=True)
    orgue = models.ForeignKey(Orgue, null=True, on_delete=models.CASCADE, related_name="sources")

    def __str__(self):
        return "{} ({})".format(self.type, self.description)


class Contribution(models.Model):
    """
    Historique des contributions
    """
    date = models.DateTimeField(
        auto_now_add=False,
        auto_now=True,
        verbose_name='Date de contribution'
    )
    description = models.CharField(max_length=500, verbose_name="Description de la contribution", blank=False)
    user = models.ForeignKey(User, null=True, editable=False, related_name="contributions", on_delete=models.SET_NULL)
    orgue = models.ForeignKey(Orgue, null=True, on_delete=models.CASCADE, related_name="contributions")

    def __str__(self):
        return "{}: {} ({})".format(self.date, self.user, self.description)


class Fichier(models.Model):
    """
    Fichiers liés à un instrument
    """
    file = models.FileField(upload_to=chemin_fichier, verbose_name="Fichier")
    description = models.CharField(max_length=100, verbose_name="Nom de fichier à afficher")
    orgue = models.ForeignKey(Orgue, null=True, on_delete=models.CASCADE, related_name="fichiers")

    # Champs automatiques
    created_date = models.DateTimeField(
        auto_now_add=True,
        auto_now=False,
        verbose_name='Creation date'
    )
    modified_date = models.DateTimeField(
        auto_now=True,
        auto_now_add=False,
        verbose_name='Update date'
    )

    def delete(self):
        if self.file:
            print("Fichier présent")
            self.file.delete()
        return super().delete()


def chemin_image(instance, filename):
    return os.path.join(str(instance.orgue.code_departement), instance.orgue.codification, "images", filename)


class Image(models.Model):
    """
    Images liées à un instrument.
    La variable MAX_PIXEL_WIDTH définie la largeur maximale en pixels qu'une image peut avoir.
    Une librairie javascript (filepond) s'occupe de faire le redimensionnement directement
    dans le naviguateur.
    """
    MAX_PIXEL_WIDTH = 2000
    image = models.ImageField(upload_to=chemin_image,
                              help_text="Taille maximale : 2 Mo. Les images doivent être libres de droits.")
    is_principale = models.BooleanField(default=False, editable=False)
    legende = models.CharField(verbose_name="Légende", max_length=400, null=True, blank=True)
    credit = models.CharField(verbose_name="Crédit", max_length=200, null=True, blank=True)
    order = models.IntegerField(default=0, verbose_name="Ordre d'affichage")
    # Champs automatiques
    thumbnail_principale = ProcessedImageField(upload_to=chemin_image,
                                               processors=[Transpose(), ResizeToFill(600, 450)],
                                               format='JPEG',
                                               options={'quality': 100})

    thumbnail = ImageSpecField(source='image',
                               processors=[Transpose(), ResizeToFill(600, 450)],
                               format='JPEG',
                               options={'quality': 100})

    orgue = models.ForeignKey(Orgue, null=True, on_delete=models.CASCADE, related_name="images")
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_date = models.DateTimeField(
        auto_now_add=True,
        auto_now=False,
        verbose_name='Creation date'
    )
    modified_date = models.DateTimeField(
        auto_now=True,
        auto_now_add=False,
        verbose_name='Update date'
    )

    def save(self, *args, **kwargs):
        self.orgue.completion = self.orgue.calcul_completion()
        super().save(*args, **kwargs)

    def is_blackandwhite(self):
        """
        Vérifie si une image est en noir et blanc en analysant la couleur de 100 pixels
        """
        if not self.image:
            return
        img = PilImage.open(self.thumbnail.path)
        width, height = img.size
        for x in range(0, width, width // 10):
            for y in range(0, height, height // 10):
                r, g, b = img.getpixel((x, y))
                if abs(r-g) > 30 or abs(g-b) > 30:
                    return False
        return True

    def delete(self):
        if self.image:
            self.image.delete()
            self.thumbnail_principale.delete()
        return super().delete()

    class Meta:
        ordering = ['order', 'created_date']


class Accessoire(models.Model):
    """
    Ex : Tremblant, Trémolo, Accouplement Pos./G.O.
    """
    nom = models.CharField(max_length=100)

    def __str__(self):
        return self.nom


@receiver([post_save, post_delete], sender=Evenement)
def save_evenement_calcul_facteurs(sender, instance, **kwargs):
    """
    La modification d'un événement doit entrainement le recalcul du taux d'avancement.
    On passe par la meéthode orgue.save() pour relancer le calcul
    """
    orgue = instance.orgue
    orgue.save()


@receiver(post_save, sender=Orgue)
def update_orgue_in_index(sender, instance, **kwargs):
    """
    Quand un orgue est modifié, on met à jour l'index des orgues
    """
    if settings.MEILISEARCH_URL:
        from orgues.api.serializers import OrgueResumeSerializer
        client = meilisearch.Client(settings.MEILISEARCH_URL, settings.MEILISEARCH_KEY)
        orgue = OrgueResumeSerializer(instance).data
        index = client.get_index(uid='orgues')
        index.add_documents([orgue])


@receiver(post_save, sender=TypeJeu)
def update_type_jeu_in_index(sender, instance, **kwargs):
    """
    Quand un type de jeu est modifié, on met à jour l'index des types de jeux
    """
    if settings.MEILISEARCH_URL:
        client = meilisearch.Client(settings.MEILISEARCH_URL, settings.MEILISEARCH_KEY)
        index = client.get_index(uid='types_jeux')
        index.add_documents([{"id": instance.id, "nom": str(instance)}])


@receiver(post_save, sender=Image)
def update_image_in_index(sender, instance, **kwargs):
    """
    Quand une vignette est modifiée, on met à jour l'index des orgues
    """
    if settings.MEILISEARCH_URL and instance.is_principale:
        from orgues.api.serializers import OrgueResumeSerializer
        client = meilisearch.Client(settings.MEILISEARCH_URL, settings.MEILISEARCH_KEY)
        orgue = OrgueResumeSerializer(instance.orgue).data
        index = client.get_index(uid='orgues')
        index.add_documents([orgue])
