import os

from django.core.management.base import BaseCommand

from orgues.models import Image


class Command(BaseCommand):
    help = 'Remove empty and broken images'

    def handle(self, *args, **options):
        for image in Image.objects.all():
            if not image.image:
                image.delete()
                print('Delete non existing image: ', image)
            elif not os.path.exists(image.image.path):
                print('File does not exist: ', image.image.path)
            elif image.image.size <= 1:
                image.image.delete()
                image.delete()
                print('Delete empty image : ', image)
