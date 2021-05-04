from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer

from orgues.api.serializers import OrgueSerializer
from orgues.models import Orgue, Facteur, Accessoire, TypeClavier, TypeJeu


class OrgueViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Orgue.objects.all()
    serializer_class = OrgueSerializer


    def get_queryset(self):
        queryset = Orgue.objects.all()
        code_departement = self.request.query_params.get('code_departement', None)
        if code_departement is not None:
            queryset = queryset.filter(code_departement=code_departement)
        return queryset.order_by('designation')


class ConfigView(APIView):
    renderer_classes = [JSONRenderer]

    def get(self, request, format=None):
        facteurs = Facteur.objects.all()
        accessoires = Accessoire.objects.all()
        typesClavier = TypeClavier.objects.all()
        typesJeux = TypeJeu.objects.all()
        return Response({
            "facteurs": [facteur.nom for facteur in facteurs],
            "types_claviers": [type.nom for type in typesClavier],
            "types_jeux": [{"nom": type.nom, "hauteur": type.hauteur} for type in typesJeux],
            "type_accessoire": [accessoire.nom for accessoire in accessoires]
        })