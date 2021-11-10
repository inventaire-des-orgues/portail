import os
from django.core.files import File
from django.core.management.base import BaseCommand
from orgues.models import Orgue, Accessoire, Evenement, Facteur, TypeClavier, Clavier, Jeu, TypeJeu, Image, Source, \
    Fichier


class Command(BaseCommand):
    help = "Correction de l'attribut designation en base de données"

    def add_arguments(self, parser):
        parser.add_argument('--casse', nargs=0, type=str,
                            help="Met la première lettre de la désignation en minuscule")
        parser.add_argument('--liste', nargs=1, type=str,
                            help="Remplace toutes les désignations à l'aide d'un fichier CSV")

    def handle(self, *args, **options):
        if options.get('casse'):
            def lower_first(s): return s[:1].lower() + s[1:] if s else ''
            for orgue in Orgue.objects.all():
                new_value = lower_first(orgue.designation)
                orgue.designation = new_value
                orgue.save()

        if options.get('liste'):
            with open(options['liste'][0], 'r', encoding='utf-8') as fic_csv:
                for avant_apres in fic_csv.readlines():
                    avant, apres = avant_apres.split(";")
                    print("Remplacement de l'attribut designation %s par %s.".format(avant, apres))
                    Orgue.objects.filer(**{"designation": avant}).update(**{"designation": apres})

