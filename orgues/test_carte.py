from django.test import TestCase, override_settings
from django.urls import reverse


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
        self.assertEqual(response.context["carte_position"], {"zoom": 10.5, "lat": 48.39, "lng": -4.48})

    def test_sans_parametre_la_carte_est_centree_sur_la_france(self):
        response = self.client.get(self.url)
        self.assertEqual(response.context["carte_position"], {"zoom": 4.8, "lat": 46.2, "lng": 2.2})

    def test_parametre_invalide_ou_hors_bornes_est_remplace_par_la_valeur_par_defaut(self):
        response = self.client.get(self.url, {"zoom": "10", "lat": "200", "lng": "nan"})
        self.assertEqual(response.context["carte_position"], {"zoom": 10.0, "lat": 46.2, "lng": 2.2})
