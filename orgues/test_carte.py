from unittest import mock

from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import User


@override_settings(MEILISEARCH_URL=False, MAPBOX_ACCESS_TOKEN="jeton-de-test",
                   FULL_SITE_URL="https://portail.test")
class OrgueCartePositionTestCase(TestCase):
    """
    Les paramètres d'URL zoom, lat et lng positionnent la carte (y compris en iframe sur un site tiers).
    Ils sont injectés dans du JavaScript : ils ne doivent jamais y arriver sans validation.
    """

    url = reverse('orgues:orgue-carte')

    def test_anonyme_accede_a_la_carte(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_parametre_zoom_malveillant_n_est_pas_injecte_dans_la_page(self):
        response = self.client.get(self.url, {"zoom": "alert(document.cookie)"})
        self.assertNotContains(response, "alert(document.cookie)")

    def test_parametres_malveillants_ne_sont_pas_injectes_dans_l_iframe(self):
        response = self.client.get(self.url, {"iframe": "true", "lat": "1;alert(1)", "lng": "fetch('//x')"})
        self.assertNotContains(response, "alert(1)")
        self.assertNotContains(response, "fetch(")

    def test_parametres_valides_positionnent_la_carte(self):
        response = self.client.get(self.url, {"zoom": "10.5", "lat": "48.39", "lng": "-4.48"})
        self.assertEqual(response.context["carte_position"], {"zoom": 10.5, "lat": 48.39, "lng": -4.48, "bbox": None})

    def test_sans_parametre_la_carte_est_centree_sur_la_france(self):
        response = self.client.get(self.url)
        self.assertEqual(response.context["carte_position"], {"zoom": 4.8, "lat": 46.2, "lng": 2.2, "bbox": None})

    def test_parametre_invalide_ou_hors_bornes_est_remplace_par_la_valeur_par_defaut(self):
        response = self.client.get(self.url, {"zoom": "10", "lat": "200", "lng": "nan"})
        self.assertEqual(response.context["carte_position"], {"zoom": 10.0, "lat": 46.2, "lng": 2.2, "bbox": None})

    def test_bbox_valide_cadre_la_carte(self):
        response = self.client.get(self.url, {"bbox": "-5.2,47.6,-3,48.9"})
        self.assertEqual(response.context["carte_position"]["bbox"], [-5.2, 47.6, -3.0, 48.9])

    def test_bbox_invalide_est_ignoree(self):
        bbox_invalides = [
            "-5.2,47.6,-3",  # trois valeurs
            "-3,47.6,-5.2,48.9",  # longitude min > longitude max
            "-5.2,47.6,-3,95",  # latitude hors bornes
            "-5.2,47.6,-3,alert(1)",
        ]
        for bbox in bbox_invalides:
            with self.subTest(bbox=bbox):
                response = self.client.get(self.url, {"bbox": bbox})
                self.assertIsNone(response.context["carte_position"]["bbox"])


@override_settings(MEILISEARCH_URL=False, MAPBOX_ACCESS_TOKEN="jeton-de-test",
                   FULL_SITE_URL="https://portail.test")
class OrgueCarteDepartementsTestCase(TestCase):
    """
    Une carte intégrée en iframe peut se limiter à quelques départements (issue #653).
    """

    url = reverse('orgues:orgue-carte')
    resultats_vides = {"hits": [], "facetDistribution": {"region": {}, "departement": {}}}

    def rechercher(self, departements):
        with mock.patch("orgues.views.meilisearch.Client") as client:
            index = client.return_value.index.return_value
            index.search.return_value = self.resultats_vides
            response = self.client.post(self.url, {"departements": departements})
        return response, index.search

    def test_departements_filtrent_les_orgues_dans_meilisearch(self):
        response, recherche = self.rechercher(["29", "56"])
        self.assertEqual(response.status_code, 200)
        options = recherche.call_args.args[1]
        self.assertEqual(options["filter"], '(departement = "Finistère" OR departement = "Morbihan")')

    def test_code_departement_inconnu_est_refuse_sans_interroger_meilisearch(self):
        response, recherche = self.rechercher(['29" OR etat = "x'])
        self.assertEqual(response.status_code, 400)
        recherche.assert_not_called()

    def test_departements_de_l_url_sont_transmis_au_formulaire_de_la_carte(self):
        response = self.client.get(self.url, {"iframe": "true", "departements": ["29", "inconnu"]})
        self.assertContains(response, '<input type="hidden" name="departements" value="29" id="id_departements_0">',
                            html=True)
        self.assertNotContains(response, "inconnu")

    def test_iframe_propose_la_liste_textuelle_des_orgues_des_departements(self):
        response = self.client.get(self.url, {"iframe": "true", "departements": ["29"]})
        url_liste = reverse('orgues:orgue-list') + "?departement=Finist%C3%A8re"
        self.assertContains(response, f'href="https://portail.test{url_liste}"')


@override_settings(MEILISEARCH_URL=False, MAPBOX_ACCESS_TOKEN="jeton-de-test",
                   FULL_SITE_URL="https://portail.test")
class OrgueCarteIntegrationTestCase(TestCase):
    """
    Le code d'intégration (iframe) est proposé aux contributeurs connectés.
    """

    url = reverse('orgues:orgue-carte')

    def test_anonyme_ne_voit_pas_le_bouton_integrer(self):
        response = self.client.get(self.url)
        self.assertNotContains(response, 'id="sharemodal"')

    def test_utilisateur_connecte_obtient_un_code_d_integration_titre_et_cadre(self):
        utilisateur = User.objects.create(email="contributeur@exemple.test", username="contributeur")
        self.client.force_login(utilisateur)
        response = self.client.get(self.url)
        self.assertContains(response, 'id="sharemodal"')
        self.assertContains(response, 'title="Carte des orgues - Inventaire des orgues de France"')
        self.assertContains(response, 'id="integration_departements"')


@override_settings(MEILISEARCH_URL=False, MAPBOX_ACCESS_TOKEN="jeton-de-test",
                   FULL_SITE_URL="https://portail.test")
class OrgueCarteIframeTestCase(TestCase):
    """
    La carte intégrée ouvre la fiche résumée d'un orgue dans une fenêtre modale Bootstrap.
    """

    url = reverse('orgues:orgue-carte')

    def test_iframe_charge_le_javascript_des_fenetres_modales(self):
        response = self.client.get(self.url, {"iframe": "true"})
        self.assertContains(response, "polo/js/plugins.js")
