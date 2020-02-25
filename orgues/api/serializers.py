from rest_framework import serializers
from orgues.models import Orgue, Jeu, Clavier, TypeJeu, Image, Fichier, Evenement, Facteur


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ["image","is_principale","credit"]

class FichierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fichier
        fields = ["file","description"]

class TypeJeuSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeJeu
        exclude = ["id"]


class EvenementSerializer(serializers.ModelSerializer):
    facteurs = serializers.StringRelatedField(many=True)
    class Meta:
        model = Evenement
        exclude = ["id","orgue"]


class JeuSerializer(serializers.ModelSerializer):
    type = TypeJeuSerializer()
    class Meta:
        model = Jeu
        exclude = ["clavier","id"]

class ClavierSerializer(serializers.ModelSerializer):
    jeux = JeuSerializer(many=True)
    type = serializers.StringRelatedField()
    class Meta:
        model = Clavier
        exclude = ["id","created_date", "modified_date","orgue"]


class OrgueSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="orgues:orgue-detail", lookup_field="slug")
    updated_by_user = serializers.StringRelatedField()
    accessoires = serializers.StringRelatedField(many=True)
    claviers = ClavierSerializer(many=True)
    images = ImageSerializer(many=True)
    fichiers = FichierSerializer(many=True)
    evenements = EvenementSerializer(many=True)


    class Meta:
        model = Orgue
        exclude = ["uuid","slug","completion","created_date"]
