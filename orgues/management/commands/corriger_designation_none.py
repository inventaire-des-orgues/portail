import os
from django.core.files import File
from django.core.management.base import BaseCommand
from orgues.models import Orgue, Accessoire, Evenement, Facteur, TypeClavier, Clavier, Jeu, TypeJeu, Image, Source, Fichier


class Command(BaseCommand):
    help = "Correction d'un attribut en base de données"

    def add_arguments(self, parser):
        parser.add_argument('--replace', nargs=1, type=str,
                            help='<nouvelle valeur>')

    def handle(self, *args, **options):
        if options.get('replace'):
            new_value = options['replace'][0]
            Orgue.objects.filter(designation__isnull=True).update(**{"designation": new_value})
