from django.core.management.base import BaseCommand
from orgues.models import TypeJeu, Jeu
from django.db.models import Count, F
from django.db.models.functions import Concat


class Command(BaseCommand):
    help = "Supprime les doublons de typeJeu."

    def handle(self, *args, **options):
        doublons = TypeJeu.objects.values('nom').annotate(nom_complet=Concat(F('nom'), F('hauteur'))).annotate(nom_complet_count=Count('nom_complet')).filter(nom_complet_count__gt=1)
        for doublon in doublons:
            typeJeu = TypeJeu.objects.annotate(nom_complet=Concat(F('nom'), F('hauteur'))).filter(nom_complet=doublon['nom_complet'])
            typeJeu_quon_garde = typeJeu[0]
            typeJeux_qui_disparaissent = typeJeu[1:]

            for typeJeu_qui_disparait in typeJeux_qui_disparaissent:
                for jeu in Jeu.objects.filter(type=typeJeu_qui_disparait):
                    jeu.type = typeJeu_quon_garde
                    jeu.save()
                print("Le doublon du typejeu {} a disparu".format(typeJeu_qui_disparait))
                typeJeu_qui_disparait.delete()