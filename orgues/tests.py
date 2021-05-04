import json
import os
import shutil

from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.template import Template, Context
from django.test import TestCase
from django.urls import reverse

from django.conf import settings
from accounts.models import User
from orgues.models import Jeu, validate_etendue, Orgue, Clavier, Image, TypeClavier


class OrgueTestCase(TestCase):

    def setUp(self):
        call_command("init_groups")
        self.admin_user = User.objects.create(email="admin_user@fabdev.fr", username="admin_user")
        self.admin_user.set_password('123456TEST')
        self.admin_user.groups.add(Group.objects.get(name=settings.GROUP_ADMIN_USER))
        self.admin_user.save()

    def test_OrgueUpdate(self):
        self.client.login(username='admin_user@fabdev.fr', password='123456TEST')
        orgue = Orgue.objects.create(edifice="sanctuaire Sainte-Marie-Mere-de-Dieu")
        url = reverse('orgues:orgue-update', args=(orgue.uuid,))

        data = {
            "edifice": "",
            "designation": "grand orgue",
            "emplacement": "en tribune, en diagonale à droite du chœur",
            "etat": "tres_bon",
            "proprietaire": "congregation",
            "references_palissy": "",
            "organisme": "Foyer de Charité de Chateauneuf-de-Galaure",
            "lien_reference": "",
            "resume": "Orgue neuf d'André Thomas, de construction contemporaine avec le sanctuaire (1979)",
            "commentaire_admin": "test"
        }
        self.client.post(url, data)
        self.assertTrue(Orgue.objects.filter(edifice="sanctuaire Sainte-Marie-Mere-de-Dieu",
                                             designation="grand orgue",
                                             emplacement="en tribune, en diagonale à droite du chœur",
                                             proprietaire="congregation",
                                             organisme="Foyer de Charité de Chateauneuf-de-Galaure",
                                             commentaire_admin="test"
                                             ).exists())

    def test_validate_etendue(self):
        self.assertRaises(ValidationError, validate_etendue, "H1-F3")
        self.assertRaises(ValidationError, validate_etendue, "C1#-F3")
        self.assertRaises(ValidationError, validate_etendue, "C1-F3#")
        self.assertRaises(ValidationError, validate_etendue, "C1-F8")
        self.assertIsNone(validate_etendue("C1-F3"))
        self.assertIsNone(validate_etendue("C#1-F3"))
        self.assertIsNone(validate_etendue("G#1-F6"))
        self.assertIsNone(validate_etendue("G#7-A1"))

    def test_has_pedalier(self):
        orgue = Orgue.objects.create()
        clavierGO = Clavier.objects.create(type=TypeClavier.objects.create(nom='GO'), orgue=orgue)
        self.assertFalse(orgue.has_pedalier)
        clavierPed = Clavier.objects.create(type=TypeClavier.objects.create(nom='Pédalier'), orgue=orgue)
        self.assertTrue(orgue.has_pedalier)
        clavierPed.delete()
        clavierPed = Clavier.objects.create(type=TypeClavier.objects.create(nom='Pedalwerk'), orgue=orgue)
        self.assertTrue(orgue.has_pedalier)

