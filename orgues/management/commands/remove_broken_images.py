from django.core.management.base import BaseCommand

from orgues.models import Image


class Command(BaseCommand):
    help = 'Remove empty and broken images'

    def handle(self, *args, **options):
        for image in Image.objects.all():
            if (not image.image) or (image.image.size <= 1):
                image.delete()
                print('Deleting image : ',image)
