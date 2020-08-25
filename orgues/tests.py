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
from orgues.models import Jeu, validate_etendue, Orgue, Clavier, Image


class OrgueTestCase(TestCase):

    def setUp(self):
        call_command("init_groups")
        self.admin_user = User.objects.create(email="admin_user@fabdev.fr", username="admin_user")
        self.admin_user.set_password('123456TEST')
        self.admin_user.groups.add(Group.objects.get(name=settings.GROUP_ADMIN_USER))
        self.admin_user.save()

    def test_Completion(self):
        orgue = Orgue.objects.create(commune='',
                                     region='Region',
                                     departement='Departement')
        orgue_id = orgue.id
        self.assertEqual(Orgue.objects.get(id=orgue_id).completion, 0)

        orgue.commune = 'Versailles'
        orgue.save()
        self.assertEqual(Orgue.objects.get(id=orgue_id).completion, 5)

        orgue.edifice = 'eglise'
        orgue.save()
        self.assertEqual(Orgue.objects.get(id=orgue_id).completion, 5)
        orgue.edifice = 'Cathédrale Saint-Louis'
        orgue.save()
        self.assertEqual(Orgue.objects.get(id=orgue_id).completion, 10)

        orgue.etat = 'bon'
        orgue.save()
        self.assertEqual(Orgue.objects.get(id=orgue_id).completion, 20)

        Clavier.objects.create(orgue=orgue)
        orgue.save()
        self.assertEqual(Orgue.objects.get(id=orgue_id).completion, 30)

        Image.objects.create(orgue=orgue, is_principale=True)
        orgue.save()
        self.assertEqual(Orgue.objects.get(id=orgue_id).completion, 60)

        orgue.buffet = 'Description du buffet'
        orgue.save()
        self.assertEqual(Orgue.objects.get(id=orgue_id).completion, 70)
        orgue.resume = 'Resumé'
        orgue.save()
        self.assertEqual(Orgue.objects.get(id=orgue_id).completion, 80)
        orgue.soufflerie = 'Description soufflerie'
        orgue.sommiers = 'Desciption sommier'
        orgue.save()
        self.assertEqual(Orgue.objects.get(id=orgue_id).completion, 100)

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

    def test_resume_composition(self):
        self.assertEqual(Template('{% load orgue_tags %}{% resume_composition 12 3 True %}').render(Context({})),
                         "12, II/P")
        self.assertEqual(Template('{% load orgue_tags %}{% resume_composition 12 2 True %}').render(Context({})), "12, I/P")
        self.assertEqual(Template('{% load orgue_tags %}{% resume_composition 9 1 True %}').render(Context({})), "9, P")

    def test_validate_etendue(self):
        self.assertRaises(ValidationError, validate_etendue, "H1-F3")
        self.assertRaises(ValidationError, validate_etendue, "C1#-F3")
        self.assertRaises(ValidationError, validate_etendue, "C1-F3#")
        self.assertRaises(ValidationError, validate_etendue, "C1-F8")
        self.assertIsNone(validate_etendue("C1-F3"))
        self.assertIsNone(validate_etendue("C#1-F3"))
        self.assertIsNone(validate_etendue("G#1-F6"))
        self.assertIsNone(validate_etendue("G#7-A1"))

    def test_search(self):
        elisabeth = Orgue.objects.create(edifice="église Sainte-Elisabeth")

        self.client.login(username='admin_user@fabdev.fr', password='123456TEST')
        url = reverse('orgues:orgue-list')

        for search_term in ['elisa',
                            'Eglise elisabeth',
                            'Eglise Sainte-Elisabeth',
                            'sainte-Elisabeth',
                            'élisabeth',
                            'Saint élisabeth',
                            'sainte-élisabeth']:
            response = self.client.get(url, {'edifice': search_term})
            self.assertIn(elisabeth, response.context['object_list'])

    def test_import_data(self):
        call_command('init_config')
        json_test = os.path.join(settings.BASE_DIR, 'exemple_orgue-v3.json')
        call_command('import_data', json_test)

        with open(json_test, "r", encoding="utf-8") as f:
            orgue_json = json.load(f)[0]

        orgue = Orgue.objects.first()

        self.assertEqual(orgue.designation, orgue_json["designation"])
        self.assertEqual(orgue.references_palissy, orgue_json["references_palissy"])
        self.assertEqual(orgue.resume, orgue_json["resume"])
        self.assertEqual(orgue.proprietaire, orgue_json["proprietaire"])
        self.assertEqual(orgue.organisme, orgue_json["organisme"])
        self.assertEqual(orgue.lien_reference, orgue_json["lien_reference"])
        self.assertEqual(orgue.is_polyphone, orgue_json["is_polyphone"])
        self.assertEqual(orgue.etat, orgue_json["etat"])
        self.assertEqual(orgue.emplacement, orgue_json["emplacement"])
        self.assertEqual(orgue.buffet, orgue_json["buffet"])
        self.assertEqual(orgue.console, orgue_json["console"])
        self.assertEqual(orgue.commentaire_admin, orgue_json["commentaire_admin"])
        self.assertEqual(orgue.edifice, orgue_json["edifice"])
        self.assertEqual(orgue.commune, orgue_json["commune"])
        self.assertEqual(orgue.code_insee, orgue_json["code_insee"])
        self.assertEqual(orgue.ancienne_commune, orgue_json["ancienne_commune"])
        self.assertEqual(orgue.departement, orgue_json["departement"])
        self.assertEqual(orgue.code_departement, orgue_json["code_departement"])
        self.assertEqual(orgue.region, orgue_json["region"])
        self.assertEqual(orgue.osm_type, orgue_json["osm_type"])
        self.assertEqual(orgue.osm_id, orgue_json["osm_id"])
        self.assertEqual(orgue.diapason, orgue_json["diapason"])
        self.assertEqual(orgue.sommiers, orgue_json["sommiers"])
        self.assertEqual(orgue.soufflerie, orgue_json["soufflerie"])
        self.assertEqual(orgue.transmission_notes, orgue_json["transmission_notes"])
        self.assertEqual(orgue.transmission_commentaire, orgue_json["transmission_commentaire"])
        self.assertEqual(orgue.tirage_jeux, orgue_json["tirage_jeux"])
        self.assertEqual(orgue.tirage_commentaire, orgue_json["tirage_commentaire"])
        self.assertEqual(orgue.commentaire_tuyauterie, orgue_json["commentaire_tuyauterie"])

        self.assertGreater(orgue.accessoires.count(), 3)
        self.assertGreater(orgue.claviers.count(), 1)
        self.assertGreater(orgue.images.count(), 0)
        self.assertGreater(orgue.claviers.filter(type__nom="Grand-Orgue").first().jeux.count(), 4)

        construction = orgue.evenements.filter(type="construction").first()
        self.assertEqual(construction.annee, 1885)
        self.assertEqual(construction.facteurs.first().nom, "Joseph Merklin & Cie")
