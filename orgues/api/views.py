from rest_framework import viewsets

from orgues.api.serializers import OrgueSerializer
from orgues.models import Orgue


class OrgueViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Orgue.objects.all()
    serializer_class = OrgueSerializer


    def get_queryset(self):
        queryset = Orgue.objects.all()
        code_departement = self.request.query_params.get('code_departement', None)
        if code_departement is not None:
            queryset = queryset.filter(code_departement=code_departement)
        return queryset.order_by('designation')
