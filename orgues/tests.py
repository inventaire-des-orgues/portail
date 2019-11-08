import os
import shutil

from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from django.conf import settings
from accounts.models import User
from orgues.models import Jeu


class OrgueTestCase(TestCase):

    def setUp(self):
        call_command("init_groups")
        self.admin_user = User.objects.create(email="admin_user@fabdev.fr", username="admin_user")
        self.admin_user.set_password('123456TEST')
        self.admin_user.groups.add(Group.objects.get(name=settings.GROUP_ADMIN_USER))
        self.admin_user.save()

    def test_OrgueCreate(self):
        self.client.login(username='admin_user@fabdev.fr', password='123456TEST')
        url = reverse('orgues:orgue-create')
        response = self.client.post(url, {
            "nom": "Orgue de Vraux",
            "edifice": "Eglise de Vraux",
            "adresse": "Rue de l'Eglise",
            "latitude": 49.028079,
            "longitude": 4.23734,
            "historique": "Lorem ipsum",
            "evenements": [],
            "clavier-Grand-Orgue Test": ["A", "B", "C", "D"],
            "clavier-Récit Test": ["A", "B", "C", "E"]
        })

        self.assertEqual(list(Jeu.objects.values_list("nom", flat=True)), ["A", "B", "C", "D", "E"])
