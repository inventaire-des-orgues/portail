from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = 'Populate groups and permissions.'

    @staticmethod
    def get_permission(codename):
        perm = None
        try:
            perm = Permission.objects.get(codename=codename)
        except Permission.DoesNotExist:
            print("Error on codename :", codename)
        except Permission.MultipleObjectsReturned:
            print("Multiple existing permissions :", codename)

        return perm

    def handle(self, *args, **options):
        standard_group, created = Group.objects.get_or_create(name=settings.GROUP_STANDARD_USER)
        admin_group, created = Group.objects.get_or_create(name=settings.GROUP_ADMIN_USER)

        standard_user_permissions = [
            'view_orgue',
            'change_orgue',

            'view_evenement',
            'add_evenement',
            'change_evenement',
            'delete_evenement',

            'view_clavier',
            'add_clavier',
            'change_clavier',
            'delete_clavier',

            'view_jeu',
            'add_jeu',
            'change_jeu',

            'view_fichier',
            'add_fichier',
            'change_fichier',
            'delete_fichier',

            'view_image',
            'add_image',
            'change_image',
            'delete_image',

            'view_source',
            'add_source',
            'change_source',
            'delete_source',

            'view_facteur',


        ]

        admin_user_permissions = standard_user_permissions + [
            'view_user',
            'add_user',
            'change_user',
            'delete_user',

            'add_orgue',
            'delete_orgue',
        ]

        standard_group.permissions.clear()
        for codename in standard_user_permissions:
            perm = self.get_permission(codename)
            standard_group.permissions.add(perm)

        admin_group.permissions.clear()
        for codename in admin_user_permissions:
            perm = self.get_permission(codename)
            admin_group.permissions.add(perm)
