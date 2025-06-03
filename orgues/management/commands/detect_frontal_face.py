from django.core.management.base import BaseCommand
from orgues.models import Image
from tqdm import tqdm
import json
import face_recognition


class Command(BaseCommand):
    help = "Recherche les visages sur les images"

    def handle(self, *args, **options):
        images = Image.objects.all()
        images_to_delete = []
        for image in tqdm(images):
            try:
                path = image.thumbnail.path
            except:
                path = None
            if path is None:
                continue

            image_fr = face_recognition.load_image_file(image.thumbnail.path)
            face_locations = face_recognition.face_locations(image_fr)
            if len(face_locations) > 0:
                images_to_delete.append({"pk":image.pk, "orgue":image.orgue.__str__()})
                print(f"Visage trouvé : {image.orgue}, {image.pk}")
        with open("orgues/temp/images_with_frontal_face.json", 'w') as f:
            json.dump(images_to_delete, f)
