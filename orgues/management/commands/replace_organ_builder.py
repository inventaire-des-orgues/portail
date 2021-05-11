from orgues.models import Orgue
from orgues.models import Facteur
from orgues.models import Evenement
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """
    Remplace dans tous les événements un facteur d'orgue par un autre.
    La fonction prend deux arguments obligatoires et un optionnel:
    - Le nom du facteur à retirer;
    - Le nom du facteur par lequel il faut remplacer;
    - optionnel : --delete DELETE : efface de la base de données le facteur à retirer.
    La fonction renvoie un message d'erreur si l'un des facteurs passé en argument n'existe pas dans la base de données ou s'il existe plusieurs fois.

    Ex :
    manage.py replace_organ_builder --delete "Abbey John II" "Abbey John-Albert"
    """
    help = "Change le facteur d'orgue"

    def add_arguments(self, parser):
        parser.add_argument('name_delete', nargs=1, type=str,
                            help='Nom du facteur à retirer de la base de données.')
        parser.add_argument('name_replace', nargs=1, type=str,
                            help='Nom du facteur qui doit remplacer.')
        parser.add_argument('--delete', action='store_true',
                            help="Efface le facteur d'orgue de la base de données")

    def handle(self, *args, **options):
        facteur_delete = Facteur.objects.filter(nom=options['name_delete'][0])
        facteur_replace = Facteur.objects.filter(nom=options['name_replace'][0])
        if facteur_delete.count() == 0:
            print("ERROR : Le nom du facteur à remplacer n'existe pas.")
        elif facteur_replace.count() == 0:
            print("ERROR : Le nom du facteur qui doit prendre place n'existe pas.")
        elif facteur_delete.count() > 1:
            print("ERROR : Deux facteurs à effacer portent le même nom.")
        elif facteur_replace.count() > 1:
            print("ERROR : Deux facteurs à mettre portent le même nom.")
        else:
            print("INFO : Je cherche à remplacer {} par {}".format(facteur_delete, facteur_replace))
            evenements = Evenement.objects.filter(facteurs=facteur_delete[0])
            for evenement in evenements:
                evenement.facteurs.remove(facteur_delete[0])
                evenement.facteurs.add(facteur_replace[0])
                print("INFO : Changement effectué pour l'orgue de {} pour l'événement {}.".format(evenement.orgue, evenement))
                evenement.save()
            orgues = Orgue.objects.filter(entretien=facteur_delete[0])
            for orgue in orgues:
                orgue.entretien.remove(facteur_delete[0])
                orgue.entretien.add(facteur_replace[0])
                print("INFO : Changement effectué pour l'entretien de l'orgue de {}.".format(orgue))
                orgue.save()
            if options['delete']:
                facteur_delete[0].delete()
                print("INFO : Le facteur {} a été retiré de la liste.".format(options['name_delete'][0]))
