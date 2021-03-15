from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from accounts.models import User
from django.contrib.auth.models import Group
from django.conf import settings


class UserTestCase(TestCase):

    def setUp(self):
        call_command("init_groups")
        self.admin_group = Group.objects.get(name=settings.GROUP_ADMIN_USER)
        self.admin_user = User.objects.create(email="admin_user@fabdev.fr", username="admin_user")
        self.admin_user.set_password('123456TEST')
        self.admin_user.groups.add(self.admin_group)
        self.admin_user.save()
