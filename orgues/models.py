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
from pilkit.processors import ResizeToFill, ResizeToFit,Transpose

from accounts.models import User


class Facteur(models.Model):
    """
    Pas celui qui distribue le courrier
    """
    nom = models.CharField(max_length=100)
    def __str__(self):
        return self.nom

    latitude_atelier = models.FloatField(null=True, blank=True, verbose_name="Latitude de l'atelier")
    longitude_atelier = models.FloatField(null=True, blank=True, verbose_name="Longitude de l'atelier")


class Orgue(models.Model):
    CHOIX_TYPE_OSM = (
        ("node", "Nœud"),
        ("way", "Chemin"),
        ("relation", "Relation"),
    )

    CHOIX_PROPRIETAIRE = (
        ("commune", "Commune"),
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
        ("electrique", "Electrique"),
        ("electrique_proportionnelle", "Electrique proportionnelle"),
        ("electro_pneumatique", "Electro-pneumatique"),
        ("pneumatique", "Pneumatique"),
    )

    CHOIX_TIRAGE = (
        ("mecanique", "Mécanique"),
        ("pneumatique_haute_pression", "Pneumatique haute pression"),
        ("pneumatique_basse_pression", "Pneumatique basse pression"),
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
        ('Ain', 'Ain'),
        ('Aisne', 'Aisne'),
        ('Allier', 'Allier'),
        ('Alpes-de-Haute-Provence', 'Alpes-de-Haute-Provence'),
        ('Hautes-Alpes', 'Hautes-Alpes'),
        ('Alpes-Maritimes', 'Alpes-Maritimes'),
        ('Ardennes', 'Ardennes'),
        ('Ardèche', 'Ardèche'),
        ('Ariège', 'Ariège'),
        ('Aube', 'Aube'),
        ('Aude', 'Aude'),
        ('Aveyron', 'Aveyron'),
        ('Bouches-du-Rhône', 'Bouches-du-Rhône'),
        ('Calvados', 'Calvados'),
        ('Cantal', 'Cantal'),
        ('Charente', 'Charente'),
        ('Charente-Maritime', 'Charente-Maritime'),
        ('Cher', 'Cher'),
        ('Corrèze', 'Corrèze'),
        ('Corse-du-Sud', 'Corse-du-Sud'),
        ('Haute-Corse', 'Haute-Corse'),
        ("Côte-d'Or", "Côte-d'Or"),
        ("Côtes-d'Armor", "Côtes-d'Armor"),
        ('Creuse', 'Creuse'),
        ('Dordogne', 'Dordogne'),
        ('Doubs', 'Doubs'),
        ('Drôme', 'Drôme'),
        ('Eure', 'Eure'),
        ('Eure-et-Loir', 'Eure-et-Loir'),
        ('Finistère', 'Finistère'),
        ('Gard', 'Gard'),
        ('Haute-Garonne', 'Haute-Garonne'),
        ('Gers', 'Gers'),
        ('Gironde', 'Gironde'),
        ('Hérault', 'Hérault'),
        ('Ille-et-Vilaine', 'Ille-et-Vilaine'),
        ('Indre', 'Indre'),
        ('Indre-et-Loire', 'Indre-et-Loire'),
        ('Isère', 'Isère'),
        ('Jura', 'Jura'),
        ('Landes', 'Landes'),
        ('Loir-et-Cher', 'Loir-et-Cher'),
        ('Loire', 'Loire'),
        ('Haute-Loire', 'Haute-Loire'),
        ('Loire-Atlantique', 'Loire-Atlantique'),
        ('Loiret', 'Loiret'),
        ('Lot', 'Lot'),
        ('Lot-et-Garonne', 'Lot-et-Garonne'),
        ('Lozère', 'Lozère'),
        ('Maine-et-Loire', 'Maine-et-Loire'),
        ('Manche', 'Manche'),
        ('Marne', 'Marne'),
        ('Haute-Marne', 'Haute-Marne'),
        ('Mayenne', 'Mayenne'),
        ('Meurthe-et-Moselle', 'Meurthe-et-Moselle'),
        ('Meuse', 'Meuse'),
        ('Morbihan', 'Morbihan'),
        ('Moselle', 'Moselle'),
        ('Nièvre', 'Nièvre'),
        ('Nord', 'Nord'),
        ('Oise', 'Oise'),
        ('Orne', 'Orne'),
        ('Pas-de-Calais', 'Pas-de-Calais'),
        ('Puy-de-Dôme', 'Puy-de-Dôme'),
        ('Pyrénées-Atlantiques', 'Pyrénées-Atlantiques'),
        ('Hautes-Pyrénées', 'Hautes-Pyrénées'),
        ('Pyrénées-Orientales', 'Pyrénées-Orientales'),
        ('Bas-Rhin', 'Bas-Rhin'),
        ('Haut-Rhin', 'Haut-Rhin'),
        ('Rhône', 'Rhône'),
        ('Haute-Saône', 'Haute-Saône'),
        ('Saône-et-Loire', 'Saône-et-Loire'),
        ('Sarthe', 'Sarthe'),
        ('Savoie', 'Savoie'),
        ('Haute-Savoie', 'Haute-Savoie'),
        ('Paris', 'Paris'),
        ('Seine-Maritime', 'Seine-Maritime'),
        ('Seine-et-Marne', 'Seine-et-Marne'),
        ('Yvelines', 'Yvelines'),
        ('Deux-Sèvres', 'Deux-Sèvres'),
        ('Somme', 'Somme'),
        ('Tarn', 'Tarn'),
        ('Tarn-et-Garonne', 'Tarn-et-Garonne'),
        ('Var', 'Var'),
        ('Vaucluse', 'Vaucluse'),
        ('Vendée', 'Vendée'),
        ('Vienne', 'Vienne'),
        ('Haute-Vienne', 'Haute-Vienne'),
        ('Vosges', 'Vosges'),
        ('Yonne', 'Yonne'),
        ('Territoire de Belfort', 'Territoire de Belfort'),
        ('Essonne', 'Essonne'),
        ('Hauts-de-Seine', 'Hauts-de-Seine'),
        ('Seine-Saint-Denis', 'Seine-Saint-Denis'),
        ('Val-de-Marne', 'Val-de-Marne'),
        ("Val-d'Oise", "Val-d'Oise"),
        ('Guadeloupe', 'Guadeloupe'),
        ('Martinique', 'Martinique'),
        ('Mayotte', 'Mayotte'),
        ('Guyane', 'Guyane'),
        ('La Réunion', 'La Réunion'),
        ('Nouvelle-Calédonie', 'Nouvelle-Calédonie'),
        ('Saint-Pierre-et-Miquelon', 'Saint-Pierre-et-Miquelon'),

    )

    CHOIX_CODE_DEPARTEMENT = (
        ('01', '01'),
        ('02', '02'),
        ('03', '03'),
        ('04', '04'),
        ('05', '05'),
        ('06', '06'),
        ('07', '07'),
        ('08', '08'),
        ('09', '09'),
        ('10', '10'),
        ('11', '11'),
        ('12', '12'),
        ('13', '13'),
        ('14', '14'),
        ('15', '15'),
        ('16', '16'),
        ('17', '17'),
        ('18', '18'),
        ('19', '19'),
        ('21', '21'),
        ('22', '22'),
        ('23', '23'),
        ('24', '24'),
        ('25', '25'),
        ('26', '26'),
        ('27', '27'),
        ('28', '28'),
        ('29', '29'),
        ('2A', '2A'),
        ('2B', '2B'),
        ('30', '30'),
        ('31', '31'),
        ('32', '32'),
        ('33', '33'),
        ('34', '34'),
        ('35', '35'),
        ('36', '36'),
        ('37', '37'),
        ('38', '38'),
        ('39', '39'),
        ('40', '40'),
        ('41', '41'),
        ('42', '42'),
        ('43', '43'),
        ('44', '44'),
        ('45', '45'),
        ('46', '46'),
        ('47', '47'),
        ('48', '48'),
        ('49', '49'),
        ('50', '50'),
        ('51', '51'),
        ('52', '52'),
        ('53', '53'),
        ('54', '54'),
        ('55', '55'),
        ('56', '56'),
        ('57', '57'),
        ('58', '58'),
        ('59', '59'),
        ('60', '60'),
        ('61', '61'),
        ('62', '62'),
        ('63', '63'),
        ('64', '64'),
        ('65', '65'),
        ('66', '66'),
        ('67', '67'),
        ('68', '68'),
        ('69', '69'),
        ('70', '70'),
        ('71', '71'),
        ('72', '72'),
        ('73', '73'),
        ('74', '74'),
        ('75', '75'),
        ('76', '76'),
        ('77', '77'),
        ('78', '78'),
        ('79', '79'),
        ('80', '80'),
        ('81', '81'),
        ('82', '82'),
        ('83', '83'),
        ('84', '84'),
        ('85', '85'),
        ('86', '86'),
        ('87', '87'),
        ('88', '88'),
        ('89', '89'),
        ('90', '90'),
        ('91', '91'),
        ('92', '92'),
        ('93', '93'),
        ('94', '94'),
        ('95', '95'),
        ('971', '971'),
        ('972', '972'),
        ('973', '973'),
        ('974', '974'),
        ('976', '976'),

    )

    # Informations générales
    designation = models.CharField(max_length=300, null=True, verbose_name="Désignation", default="orgue", blank=True)
    is_polyphone = models.BooleanField(default=False, verbose_name="Orgue polyphone de la manufacture Debierre ?")
    codification = models.CharField(max_length=24, unique=True, db_index=True)
    references_palissy = models.CharField(max_length=60, null=True, verbose_name="Référence(s) Palissy", blank=True,
                                          help_text="Séparer les codes par des virgules")
    resume = models.TextField(max_length=500, null=True, verbose_name="Résumé", blank=True,
                              help_text="Présentation en quelques lignes de l'instrument \
                              et son originalité (max 500 caractères)")
    proprietaire = models.CharField(max_length=40, null=True, choices=CHOIX_PROPRIETAIRE, default="commune",
                                    verbose_name="Propriétaire")
    organisme = models.CharField(verbose_name="Organisme auquel s'adresser", max_length=100, null=True, blank=True)
    lien_reference = models.URLField(verbose_name="Lien de référence", max_length=300, null=True, blank=True)

    entretien = models.ManyToManyField(Facteur, blank=True, verbose_name="Facteur en charge de l'entretien")

    etat = models.CharField(max_length=20, choices=CHOIX_ETAT, null=True, blank=True,
                            help_text="Se rapporte au fait que l'orgue est jouable ou non.")
    emplacement = models.CharField(max_length=50, null=True, blank=True, verbose_name="Emplacement",
                                   help_text="Ex: sol, tribune ...")
    buffet = models.TextField(verbose_name="Description du buffet", null=True, blank=True,
                              help_text="Description du buffet et de son état.")
    console = models.TextField(verbose_name="Description de la console", null=True, blank=True,
                               help_text="Description de la console (ex: en fenêtre, \
                               séparée organiste tourné vers l'orgue ...).")

    commentaire_admin = models.TextField(verbose_name="Commentaire rédacteurs", null=True, blank=True,
                                         help_text="Commentaire uniquement visible par les rédacteurs")

    # Localisation
    code_dep_validator = RegexValidator(regex='^(97[12346]|0[1-9]|[1-8][0-9]|9[0-5]|2[AB])$',
                                        message="Renseigner un code de département valide")

    edifice = models.CharField(max_length=300)
    adresse = models.CharField(max_length=300, null=True, blank=True)
    commune = models.CharField(max_length=100)
    code_insee = models.CharField(max_length=5)
    ancienne_commune = models.CharField(max_length=100, null=True, blank=True)
    departement = models.CharField(verbose_name="Département", choices=CHOIX_DEPARTEMENT, max_length=50)
    code_departement = models.CharField(choices=CHOIX_CODE_DEPARTEMENT, verbose_name="Code département", max_length=3)
    region = models.CharField(verbose_name="Région", choices=CHOIX_REGION, max_length=50)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    osm_type = models.CharField(choices=CHOIX_TYPE_OSM, verbose_name="Type open street map", max_length=20, null=True,
                                blank=True)
    osm_id = models.CharField(verbose_name="Id open street map", max_length=20, null=True, blank=True)

    # Partie instrumentale
    diapason = models.CharField(max_length=20, null=True, blank=True,
                                help_text="Hauteur en Hertz du A2 joué par le prestant 4, à une température donnée")
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
    transmission_commentaire = models.CharField(max_length=100, null=True, blank=True, help_text="Max 100 caractères")
    tirage_jeux = models.CharField(verbose_name="Tirage des jeux", max_length=30, choices=CHOIX_TIRAGE, null=True,
                                   blank=True)
    tirage_commentaire = models.CharField(max_length=100, null=True, blank=True, help_text="Max 100 caractères")
    commentaire_tuyauterie = models.TextField(verbose_name="Description de la tuyauterie", blank=True, null=True)
    accessoires = models.ManyToManyField('Accessoire', blank=True)

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
        Récupère l'image principale de l'instrument
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
        return self.claviers.filter(type__nom__in=['Pédale', 'Pédalier']).exists()

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
        :return:
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
    if not re.match("^([A-G]|CD)#?[1-7]-([A-G]|CD)#?[1-7]$", value):
        raise ValidationError("L'étendue doit être de la forme F1-G5, C1-F#5 ...")


class Clavier(models.Model):
    """
    Un orgue peut avoir plusieurs claviers et un pédalier.
    """

    type = models.ForeignKey(TypeClavier, verbose_name="Nom", null=True, on_delete=models.CASCADE, db_index=True)
    is_expressif = models.BooleanField(verbose_name="Cocher si expressif", default=False)
    etendue = models.CharField(validators=[validate_etendue], max_length=10, null=True, blank=True,
                               help_text="De la forme F1-G5, C1-F#5 ... ")
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
        ("relevage", "Relevage"),
        ("modifications", "Modifications"),
        ("disparition", "Disparition"),
        ("degats", "Dégâts"),
        ("classement_mh", "Classement au titre des monuments historiques"),
        ("inscription_mh", "Inscription au titre des monuments historiques"),
    )

    annee = models.IntegerField(verbose_name="Année de début de l'évènement")
    annee_fin = models.IntegerField(verbose_name="Année de fin de l'évènement", null=True, blank=True, help_text="Optionnelle")
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

    def __str__(self):
        return "{} ({})".format(self.type, self.dates)

    class Meta:
        ordering = ["annee"]


class TypeJeu(models.Model):
    """
    Lorsque l'on définit les jeux d'un clavier, on pioche parmi les types de jeu existants
    """
    nom = models.CharField(max_length=50)
    hauteur = models.CharField(max_length=20,
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
    CHOIX_CONFIGURATION = (
        ('basse', 'Basse'),
        ('dessus', 'Dessus'),
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


def chemin_image(instance, filename):
    return os.path.join(str(instance.orgue.code_departement), instance.orgue.codification, "images", filename)


class Image(models.Model):
    """
    Images liées à un instrument
    """
    image = models.ImageField(upload_to=chemin_image,
                              help_text="Taille maximale : 2 Mo. Les images doivent être libres de droits.")
    is_principale = models.BooleanField(default=False, editable=False)
    legende = models.CharField(verbose_name="Légende", max_length=400, null=True, blank=True)
    credit = models.CharField(verbose_name="Crédit", max_length=200)

    # Champs automatiques
    thumbnail_principale = ProcessedImageField(upload_to=chemin_image,
                                               processors=[Transpose(),ResizeToFill(600, 450)],
                                               format='JPEG',
                                               options={'quality': 100})

    thumbnail = ImageSpecField(source='image',
                               processors=[Transpose(),ResizeToFill(600, 450)],
                               format='JPEG',
                               options={'quality': 100})
    vignette = ImageSpecField(source='image',
                              processors=[Transpose(), ResizeToFit(150, 100)],
                              format='JPEG',
                              options={'quality': 100})

    orgue = models.ForeignKey(Orgue, null=True, on_delete=models.CASCADE, related_name="images")
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


class Accessoire(models.Model):
    """
    Ex : Tremblant, Trémolo, Accouplement Pos./G.O.
    """
    nom = models.CharField(max_length=100)

    def __str__(self):
        return self.nom


@receiver([post_save, post_delete], sender=Evenement)
def save_evenement_calcul_facteurs(sender, instance, **kwargs):
    orgue = instance.orgue
    orgue.save()


@receiver(post_save, sender=Orgue)
def update_orgue_in_index(sender, instance, **kwargs):
    if hasattr(settings, 'MEILISEARCH_URL'):
        from orgues.api.serializers import OrgueResumeSerializer
        client = meilisearch.Client(settings.MEILISEARCH_URL, settings.MEILISEARCH_KEY)
        orgue = OrgueResumeSerializer(instance).data
        index = client.get_index(uid='orgues')
        index.add_documents([orgue])


@receiver(post_save, sender=Image)
def update_image_in_index(sender, instance, **kwargs):
    if hasattr(settings, 'MEILISEARCH_URL') and instance.is_principale:
        from orgues.api.serializers import OrgueResumeSerializer
        client = meilisearch.Client(settings.MEILISEARCH_URL, settings.MEILISEARCH_KEY)
        orgue = OrgueResumeSerializer(instance.orgue).data
        index = client.get_index(uid='orgues')
        index.add_documents([orgue])
