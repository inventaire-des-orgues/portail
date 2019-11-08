from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = 'Populate groups and permissions.'

    def handle(self, *args, **options):
        standard_group, created = Group.objects.get_or_create(name=settings.GROUP_STANDARD_USER)
        admin_group, created = Group.objects.get_or_create(name=settings.GROUP_ADMIN_USER)

        standard_user_permissions = [

            'orgues.view_orgue'
        ]

        admin_user_permissions = standard_user_permissions + [
            'view_user',
            'add_user',
            'change_user',
            'delete_user',

            'view_orgue',
            'add_orgue',
            'change_orgue',
            'delete_orgue',
        ]

        standard_group.permissions.clear()
        standard_permission_queryset = Permission.objects.filter(codename__in=standard_user_permissions)
        for permission in standard_permission_queryset:
            standard_group.permissions.add(permission)

        admin_group.permissions.clear()
        admin_permission_queryset = Permission.objects.filter(codename__in=admin_user_permissions)
        for permission in admin_permission_queryset:
            admin_group.permissions.add(permission)
