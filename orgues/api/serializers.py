from rest_framework import serializers
from orgues.models import Orgue, Jeu, Clavier, TypeJeu, Image, Fichier, Evenement, Source, Facteur


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


class OrgueSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="orgues:orgue-detail", lookup_field="slug")
    updated_by_user = serializers.StringRelatedField()
    accessoires = serializers.StringRelatedField(many=True)
    claviers = ClavierSerializer(many=True)
    images = ImageSerializer(many=True)
    fichiers = FichierSerializer(many=True)
    evenements = EvenementSerializer(many=True)
    sources = SourceSerializer(many=True)

    class Meta:
        model = Orgue
        exclude = ["uuid", "id", "slug", "created_date"]


class OrgueResumeSerializer(serializers.ModelSerializer):
    """
    Serializers utilisé pour constuire l'index de recherche
    """
    facteurs = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

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
            "url"
        ]

    def get_url(self, obj):
        return obj.get_absolute_url()

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
