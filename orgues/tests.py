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
from orgues.models import Jeu, validate_etendue, note_to_hauteur, count_notes, Orgue, Clavier, Image, TypeClavier


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
        self.assertRaises(ValidationError, validate_etendue, "C1-F9")
        self.assertRaises(ValidationError, validate_etendue, "C1-CD8")
        self.assertRaises(ValidationError, validate_etendue, "G#7-A1")
        self.assertRaises(ValidationError, validate_etendue, "D♭1-D1")
        self.assertRaises(ValidationError, validate_etendue, "C0-B8")  # Plus de 88 notes (etendu du piano)
        self.assertIsNone(validate_etendue("C1-F3"))
        self.assertIsNone(validate_etendue("CD1-F3"))
        self.assertIsNone(validate_etendue("C#1-F3"))
        self.assertIsNone(validate_etendue("G#1-F6"))
        self.assertIsNone(validate_etendue("G#1-A#4"))
        self.assertIsNone(validate_etendue("CFDGEAA#BC1-C2"))  # Ocatave courte à l'italienne
        self.assertIsNone(validate_etendue("CFDGEAB♭BC1-C2"))  # Ocatave courte à l'italienne

    def test_nombre_notes(self):
        self.assertEqual(note_to_hauteur("F"), 5)
        self.assertEqual(note_to_hauteur("A#"), 10)
        self.assertEqual(note_to_hauteur("C♭"), 11)
        self.assertEqual(note_to_hauteur("D♭"), 1)
        self.assertEqual(note_to_hauteur("D"), 2)
        self.assertRaises(ValueError, note_to_hauteur, "H")

        self.assertNotes("", None)
        self.assertNotes("J3-F1", None)
        self.assertNotes("A-F1", None)
        self.assertNotes("D♭2-D1", None)
        self.assertNotes("D1-D♭1", None)
        self.assertNotes("D#1-D1", None)
        self.assertNotes("E1-E1", None)

        self.assertNotes("C1-G5", 56)

        # Validations nombres notes pédalier
        self.assertNotes("C1-F3", 30)
        self.assertNotes("C1-G3", 32)

        self.assertNotes("C1-C3", 25)
        self.assertNotes("C1-C#3", 26)
        self.assertNotes("C1-D♭3", 26)
        self.assertNotes("C1-D3", 27)
        self.assertNotes("C1-E3", 29)
        # Validation nombres notes claviers usuelles
        self.assertNotes("C1-B4", 48)
        self.assertNotes("C1-C#5", 50)
        self.assertNotes("C1-D5", 51)
        self.assertNotes("C1-E5", 53)
        self.assertNotes("C1-F#5", 55)
        self.assertNotes("C1-A5", 58)
        self.assertNotes("C1-C6", 61)
        # Validation nombres notes claviers courts
        self.assertNotes("C3-C5", 25)
        self.assertNotes("C2-C5", 37)
        self.assertNotes("A0-C8", 88)  # Etendu du piano
        # Validation ravalement
        self.assertNotes("CD1-F1", 5)  # Do Ré Ré# Mi Fa
        self.assertNotes("CDD#E1-F1", 5)  # Do Ré Ré# Mi Fa
        self.assertNotes("F0-C1", 8)  # Fa Fa# Sol Sol# La La# Si Do
        self.assertNotes("CFDGEAA#BC1-C1", 9)  # Octave courte italienne : Do Fa Ré Sol Mi La Sib Si Do
        self.assertNotes("CFDGEAB♭BC1-C1", 9)  # Octave courte italienne : Do Fa Ré Sol Mi La Sib Si Do

    def assertNotes(self, etendue, notes):
        if notes is not None:
            self.assertEqual(count_notes(etendue), notes, "etendue %s = %i notes" % (etendue, notes))
        else:
            self.assertRaises(ValidationError, count_notes, etendue)
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
        clavierGO.delete()
        clavierPed.delete()
