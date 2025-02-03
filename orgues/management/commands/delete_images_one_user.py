from django.core.management.base import BaseCommand
from orgues.models import Image
from accounts.models import User
from tqdm import tqdm

class Command(BaseCommand):
    help = "Supprime toutes les images publiées par un utilisateur"

    def add_arguments(self, parser):
        parser.add_argument('--first_name', type=str, help="")
        parser.add_argument('--last_name', type=str, help="")

    def handle(self, *args, **options):
        first_name = options.get("first_name")
        last_name = options.get("last_name")
        users = User.objects.filter(first_name=first_name, last_name=last_name)
        if len(users)==0:
            print("L'utilisateur n'a pas été trouvé")
        elif len(users)>=2:
            print(f"{len(users)} utilisateurs ont été trouvés : {users}")
        else:
            user = users[0]
            print("Utilisateur trouvé : ", user)
            images = Image.objects.filter(user=user)
            print("Images à supprimer : ", len(images))
            for image in tqdm(images):
                image.delete()

        

        
