from rest_framework import serializers
from orgues.models import Orgue, Jeu, Clavier, TypeJeu, Image, Fichier, Evenement, Source, Facteur, Contribution


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ["image", "is_principale", "credit"]


class FichierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fichier
        fields = ["file", "description"]


class TypeJeuSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeJeu
        exclude = ["id"]


class EvenementSerializer(serializers.ModelSerializer):
    facteurs = serializers.StringRelatedField(many=True)

    class Meta:
        model = Evenement
        exclude = ["id", "orgue"]


class JeuSerializer(serializers.ModelSerializer):
    type = TypeJeuSerializer()

    class Meta:
        model = Jeu
        exclude = ["clavier", "id"]


class ClavierSerializer(serializers.ModelSerializer):
    jeux = JeuSerializer(many=True)
    type = serializers.StringRelatedField()

    class Meta:
        model = Clavier
        exclude = ["id", "created_date", "modified_date", "orgue"]


class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Source
        exclude = ["id", "orgue"]


class FacteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Facteur
        exclude = ["id"]


class ContributionSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()

    class Meta:
        model = Contribution
        exclude = ["id", "orgue"]


class OrgueSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="orgues:orgue-detail", lookup_field="slug")
    updated_by_user = serializers.StringRelatedField()
    accessoires = serializers.StringRelatedField(many=True)
    claviers = ClavierSerializer(many=True)
    images = ImageSerializer(many=True)
    fichiers = FichierSerializer(many=True)
    evenements = EvenementSerializer(many=True)
    sources = SourceSerializer(many=True)
    contributions = ContributionSerializer(many=True)

    class Meta:
        model = Orgue
        exclude = ["uuid", "id", "slug", "created_date"]


class OrgueResumeSerializer(serializers.ModelSerializer):
    """
    Serializers utilisé pour construire l'index de recherche
    """
    facteurs = serializers.SerializerMethodField()
    facet_facteurs = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    jeux = serializers.SerializerMethodField()
    construction = serializers.SerializerMethodField()

    class Meta:
        model = Orgue
        fields = [
            "id",
            "designation",
            "edifice",
            "commune",
            "ancienne_commune",
            "departement",
            "region",
            "completion",
            "vignette",
            "emplacement",
            "resume_composition",
            "facteurs",
            "facet_facteurs",
            "url",
            "latitude",
            "longitude", 
            "jeux",
            "claviers_count",
            "jeux_count",
            "construction",
            "resume_composition_clavier",
        ]

    def get_url(self, obj):
        return obj.get_absolute_url()

    def get_jeux(self, obj):
        jeux = obj.jeux_count // 10
        return "{0}-{1}".format(jeux * 10, (jeux+1) * 10)

    def get_facteurs(self, obj):
        facteurs = []
        seen_facteurs = set()
        evenements = Evenement.objects.filter(orgue=obj, facteurs__isnull=False).prefetch_related('facteurs').order_by('annee')
        for evenement in evenements:
            nouveau_facteur = " & ".join(evenement.facteurs.values_list('nom', flat=True))
            if nouveau_facteur not in seen_facteurs:
                seen_facteurs.add(nouveau_facteur)
                facteurs.append(nouveau_facteur)
        return ", ".join(facteurs)
    
    def get_facet_facteurs(self, obj):
        facteurs = set()
        evenements = Evenement.objects.filter(orgue=obj, facteurs__isnull=False).prefetch_related('facteurs').order_by('annee')
        for evenement in evenements:
            if evenement.type in ['construction', 'reconstruction']:
                facteurs.update(evenement.facteurs.values_list('nom', flat=True))
        return list(facteurs)

    def get_construction(self, obj):
        evenements = Evenement.objects.filter(orgue=obj).order_by('-annee')
        for evenement in evenements:
            if evenement.type in ['construction', 'reconstruction']:
                return evenement.annee
        return ''


class OrgueCarteSerializer(serializers.ModelSerializer):
    """
    Serializers utilisé pour afficher les orgues sur la carte
    """
    facteurs = serializers.SerializerMethodField()
    nombre_jeux = serializers.SerializerMethodField()

    class Meta:
        model = Orgue
        fields = [
            "slug",
            "latitude",
            "longitude",
            "commune",
            "emplacement",
            "edifice",
            "references_palissy",
            "nombre_jeux",
            "resume_composition",
            "etat",
            "facteurs",
        ]

    def get_nombre_jeux(self, obj):
        return obj.jeux_count

    def get_facteurs(self, obj):
        facteurs = []
        evenements = Evenement.objects.filter(orgue=obj, facteurs__isnull=False).prefetch_related('facteurs')
        for evenement in evenements:
            nouveaux_facteurs = evenement.facteurs.values_list('pk', flat=True)
            for nouveau_facteur in nouveaux_facteurs:
                facteurs.append([nouveau_facteur, evenement.type])
        return facteurs
