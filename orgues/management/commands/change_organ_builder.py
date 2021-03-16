from orgues.models import Orgue
from orgues.models import Facteur
from orgues.models import Evenement
from django.core.management.base import BaseCommand
import requests

class Command(BaseCommand):
    """
    Remplace dans tous les événements un facteur d'orgue par un autre.
    La fonction prend trois arguments obligatoires:
    - Le nom du facteur à retirer;
    - Le nom du facteur par lequel il faut remplacer;
    - Un booléen qui, si a la valeur True, efface le facteur d'orgue de la base de données.
    La fonction renvoie un message d'erreur si l'un des facteurs passé en argument n'existe pas dans la base de données ou s'il existe plusieurs fois.
    """
    help = "Change le facteur d'orgue"

    def add_arguments(self, parser):
        parser.add_argument('name_delete', nargs=1, type=str,
                            help='Nom du facteur à retirer de la base de données.')
        parser.add_argument('name_replace', nargs=1, type=str,
                            help='Nom du facteur qui doit remplacer.')
        parser.add_argument('delete', nargs=1, type=str,
                            help="Si True, efface le facteur d'orgue de la base de données")

    def handle(self, *args, **options):
        facteur_delete=Facteur.objects.filter(nom=options['name_delete'][0])
        facteur_replace=Facteur.objects.filter(nom=options['name_replace'][0])
        if facteur_delete.count()==0:
            print("Le nom du facteur à effacer n'existe pas.")
        elif facteur_replace.count()==0:
            print("Le nom du facteur qui doit remplacer n'existe pas.")
        elif facteur_delete.count()>1:
            print("Deux facteurs à effacer portent le même nom.")
        elif facteur_replace.count()>1:
            print("Deux facteurs à mettre portent le même nom.")
        else:
            evenements=Evenement.objects.filter(facteurs=facteur_delete[0])
            for evenement in evenements:
                evenement.facteurs.remove(facteur_delete[0])
                evenement.facteurs.add(facteur_replace[0])
                print("Changement effectué pour l'orgue de {} pour l'événement {}.".format(evenement.orgue, evenement))
                evenement.save()
            if options['delete'][0]=='True':
                facteur_delete[0].delete()
                print("Le facteur {} a été retiré de la liste.".format(options['name_delete'][0]))