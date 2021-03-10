from orgues.models import Orgue
from django.core.management.base import BaseCommand
import requests




class Command(BaseCommand):
    help = 'Calcul barycenters of osm object'

    def add_arguments(self, parser):
        parser.add_argument('replaceall', nargs=1, type=str,
                            help='Remplace la longitude/latitude pour tous les orgues, y compris pour ceux déjà renseignés.')

    def handle(self, *args, **options):
        compte_changer=0
        for orgue in Orgue.objects.all():
            if options['replaceall'][0] or orgue.latitude==None or orgue.longitude==None:
                if (orgue.osm_type and orgue.osm_id):
                    overpass_url = "http://overpass-api.de/api/interpreter"
                    overpass_query = """[out:json];{}({});(._;>;);out;""".format(orgue.osm_type, orgue.osm_id)
                    response = requests.get(overpass_url,params={'data': overpass_query})
                    if response.status_code==200:
                        data=response.json()
                        if len(data['elements'])>0:
                            orgue.latitude, orgue.longitude, coef=orgue.calcul_barycentre(data['elements'], orgue.osm_type)
                            compte_changer+=1
                    else:
                        print("Erreur avec l'orgue : ", orgue)
                        print("Status code : ", response.status_code)
                        print("")
        print("{} orgues ont été mis à jour".format(compte_changer))
