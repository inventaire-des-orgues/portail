from django.core.management.base import BaseCommand
from orgues.models import Orgue
import orgues.utilsorgues.codification as codif
import orgues.utilsorgues.correcteurorgues as co


class Command(BaseCommand):
    help = "Récupération de la nouvelle codification d'un orgue lorsque les information de localisation ont été changées mais pas la codification"

    def add_arguments(self, parser):
        parser.add_argument('codification', nargs=1, type=str,
                            help="Codification actuelle de l'orgue")

    def handle(self, *args, **options):
        codification = options['codification'][0]
        orgue = Orgue.objects.get(codification__exact=codification)
        edifice, type_edifice = co.reduire_edifice(orgue.edifice, orgue.commune)
        nouvelle_codification = codif.codifier_instrument(orgue.code_insee, orgue.commune, edifice, type_edifice, orgue.designation)
        print("Nouvelle codification : ", nouvelle_codification)
        
