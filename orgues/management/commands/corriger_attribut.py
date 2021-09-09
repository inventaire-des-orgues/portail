import os
from django.core.files import File
from django.core.management.base import BaseCommand
from orgues.models import Orgue, Accessoire, Evenement, Facteur, TypeClavier, Clavier, Jeu, TypeJeu, Image, Source, Fichier


class Command(BaseCommand):
    help = "Correction d'un attribut en base de données"

    def add_arguments(self, parser):
        parser.add_argument('--replace', nargs=3, type=str,
                            help='<attribut> <valeur recherchée> <nouvelle valeur>')

    def handle(self, *args, **options):
        if options.get('replace'):
            field = options['replace'][0]
            old_value = options['replace'][1]
            new_value = options['replace'][2]
            Orgue.objects.filter(**{field: old_value}).update(**{field: new_value})
