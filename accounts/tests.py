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

    def test_UserList(self):
        self.client.login(username='admin_user@fabdev.fr', password='123456TEST')
        response = self.client.get(reverse('accounts:user-list'))
        self.assertEqual(response.status_code, 200)

    def test_UserCreate(self):
        self.client.login(username='admin_user@fabdev.fr', password='123456TEST')
        url = reverse('accounts:user-create')
        self.client.post(url, data={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@fabdev.fr",
            "password": "54321TEST",
            "groups": self.admin_group.pk
        })
        self.client.login(username='john.doe@fabdev.fr', password='54321TEST')
        response = self.client.get(reverse('accounts:user-list'))
        self.assertEqual(response.status_code, 200)

    def test_UserUpdatePassword(self):
        self.client.login(username='admin_user@fabdev.fr', password='123456TEST')
        user = User.objects.create(first_name="John", last_name="Doe", email="john.doe@fabdev.fr", password="coucou")
        user.groups.add(self.admin_group)
        url = reverse('accounts:user-update-password', args=(user.uuid,))
        self.client.post(url, data={
            "password1": "coucouleschatons",
            "password2": "coucouleschatons",
        })
        self.client.login(username='john.doe@fabdev.fr', password='coucouleschatons')
        response = self.client.get(reverse('accounts:user-list'))
        self.assertEqual(response.status_code, 200)
