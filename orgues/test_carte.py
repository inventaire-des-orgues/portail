import json
import tempfile
from types import SimpleNamespace
from unittest import mock

from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from meilisearch.errors import MeilisearchCommunicationError
from requests.exceptions import MissingSchema

from accounts.models import User
from orgues.services.carte import DELAI_MEILISEARCH_SECONDES, RechercheCarteIndisponible, construire_filtre_carte, \
    rechercher_orgues_carte

MEILISEARCH_FICTIF = "http://meilisearch.test"


@override_settings(MEILISEARCH_URL=False, FULL_SITE_URL="https://portail.test")
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


@override_settings(MEILISEARCH_URL=False, FULL_SITE_URL="https://portail.test")
class OrgueCarteDepartementsTestCase(TestCase):
    """
    Une carte intégrée en iframe peut se limiter à quelques départements (issue #653).
    """

    url = reverse('orgues:orgue-carte')
    resultats_vides = {"hits": [], "facetDistribution": {"region": {}, "departement": {}}}

    def rechercher(self, departements):
        with override_settings(MEILISEARCH_URL=MEILISEARCH_FICTIF), \
                mock.patch("orgues.services.carte.meilisearch.Client") as client:
            index = client.return_value.index.return_value
            index.search.return_value = self.resultats_vides
            response = self.client.post(self.url, {"departements": departements})
        return response, index.search

    def test_departements_filtrent_les_orgues_dans_meilisearch(self):
        response, recherche = self.rechercher(["29", "56"])
        self.assertEqual(response.status_code, 200)
        options = recherche.call_args.args[1]
        self.assertEqual(options["filter"], '(departement = "Finistère" OR departement = "Morbihan")')

    def test_recherche_filtree_renvoie_le_geojson_des_orgues_et_les_totaux(self):
        resultats = {
            "hits": [{"id": 7, "longitude": -4.1, "latitude": 48.2, "edifice": "Église fictive",
                      "commune": "Commune fictive", "monument_historique": True}],
            "facetDistribution": {"region": {"Bretagne": 1}, "departement": {"Finistère": 1}},
        }
        with override_settings(MEILISEARCH_URL=MEILISEARCH_FICTIF), \
                mock.patch("orgues.services.carte.meilisearch.Client") as client:
            client.return_value.index.return_value.search.return_value = resultats
            response = self.client.post(self.url, {"departements": ["29"]})
        self.assertEqual(response.status_code, 200)
        donnees = response.json()
        self.assertEqual(donnees["totaux_regions"], {"Bretagne": 1})
        self.assertEqual(donnees["totaux_departements"], {"Finistère": 1})
        orgue = donnees["orgues_geojson"]["features"][0]
        self.assertEqual(orgue["id"], 7)
        self.assertEqual(orgue["geometry"]["coordinates"], [-4.1, 48.2])
        self.assertEqual(orgue["properties"]["nom"], "Église fictive - Commune fictive")

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


@override_settings(MEILISEARCH_URL=False, FULL_SITE_URL="https://portail.test")
class OrgueCarteIntegrationTestCase(TestCase):
    """
    Le code d'intégration (iframe) est proposé à tout visiteur du portail, anonyme compris.
    Il n'est pas proposé dans la carte intégrée elle-même : il se génère depuis le portail.
    """

    url = reverse('orgues:orgue-carte')

    def connecter_un_contributeur(self):
        utilisateur = User.objects.create(email="contributeur@exemple.test", username="contributeur")
        self.client.force_login(utilisateur)

    def assert_code_d_integration_propose(self, response):
        self.assertContains(response, 'href="#sharemodal"')
        self.assertContains(response, 'id="sharemodal"')
        self.assertContains(response, 'title="Carte des orgues - Inventaire des orgues de France"')
        self.assertContains(response, 'id="integration_departements"')

    def test_anonyme_obtient_un_code_d_integration_titre_et_cadre(self):
        response = self.client.get(self.url)
        self.assert_code_d_integration_propose(response)

    def test_utilisateur_connecte_obtient_un_code_d_integration_titre_et_cadre(self):
        self.connecter_un_contributeur()
        response = self.client.get(self.url)
        self.assert_code_d_integration_propose(response)

    def test_iframe_ne_propose_pas_d_integrer_la_carte(self):
        response = self.client.get(self.url, {"iframe": "true"})
        self.assertNotContains(response, 'href="#sharemodal"')
        self.assertNotContains(response, 'id="sharemodal"')
        self.assertNotContains(response, 'id="integration_departements"')
        self.assertNotContains(response, "update_iframe_code")

    def test_iframe_ne_propose_pas_d_integrer_la_carte_meme_connecte(self):
        self.connecter_un_contributeur()
        response = self.client.get(self.url, {"iframe": "true"})
        self.assertNotContains(response, 'href="#sharemodal"')
        self.assertNotContains(response, 'id="sharemodal"')
        self.assertNotContains(response, 'id="integration_departements"')
        self.assertNotContains(response, "update_iframe_code")


@override_settings(MEILISEARCH_URL=False, FULL_SITE_URL="https://portail.test")
class OrgueCarteIframeTestCase(TestCase):
    """
    La carte intégrée ouvre la fiche résumée d'un orgue dans une fenêtre modale Bootstrap.
    """

    url = reverse('orgues:orgue-carte')

    def test_iframe_charge_le_javascript_des_fenetres_modales(self):
        response = self.client.get(self.url, {"iframe": "true"})
        self.assertContains(response, "polo/js/plugins.js")


@override_settings(MEILISEARCH_URL=False, FULL_SITE_URL="https://portail.test")
class OrgueCarteFondDeCarteTestCase(TestCase):
    """
    La carte, y compris intégrée sur un site tiers, ne transmet pas l'adresse IP des visiteurs à Mapbox :
    MapLibre est servi par le portail et le fond de carte vient de la Géoplateforme de l'IGN.
    """

    url = reverse('orgues:orgue-carte')

    def test_carte_s_affiche_sans_jeton_mapbox(self):
        for parametres in ({}, {"iframe": "true"}):
            with self.subTest(parametres=parametres):
                response = self.client.get(self.url, parametres)
                self.assertEqual(response.status_code, 200)
                self.assertNotContains(response, "mapbox")
                self.assertContains(response, "plugins/maplibre-gl/maplibre-gl.js")
                self.assertContains(response, "https://data.geopf.fr/")

    def test_page_propose_la_liste_des_orgues_si_la_carte_ne_peut_pas_s_afficher(self):
        for parametres in ({}, {"iframe": "true"}):
            with self.subTest(parametres=parametres):
                response = self.client.get(self.url, parametres)
                self.assertContains(response, 'id="carte_indisponible"')
                self.assertContains(response, "La carte ne peut pas s'afficher dans ce navigateur")


class ConstruireFiltreCarteTestCase(SimpleTestCase):
    """
    Le filtre Meilisearch de la carte est construit à partir des données validées par OrgueCarteForm.
    """

    def donnees(self, **filtres):
        donnees = {"etats": [], "facteurs": [], "manufactures": [], "jeux": None, "monument": False,
                   "departements": []}
        donnees.update(filtres)
        return donnees

    def test_sans_filtre_renvoie_none(self):
        self.assertIsNone(construire_filtre_carte(self.donnees()))

    def test_chaque_filtre_seul(self):
        cas = [
            ({"etats": ["Disparu", "Bon : jouable, défauts mineurs"]},
             '(etat = "Disparu" OR etat = "Bon : jouable, défauts mineurs")'),
            ({"facteurs": [SimpleNamespace(nom=" Cavaillé-Coll "), SimpleNamespace(nom="Merklin")]},
             '(facet_facteurs = "Cavaillé-Coll" OR facet_facteurs = "Merklin")'),
            ({"manufactures": [SimpleNamespace(nom="Manufacture fictive ")]},
             '(facet_manufactures = "Manufacture fictive")'),
            ({"jeux": [10, 40]}, '(jeux_count 10 TO 40)'),
            ({"monument": True}, '(monument_historique = "true")'),
            ({"departements": ["Finistère", "Morbihan"]},
             '(departement = "Finistère" OR departement = "Morbihan")'),
        ]
        for filtres, attendu in cas:
            with self.subTest(filtres=filtres):
                self.assertEqual(construire_filtre_carte(self.donnees(**filtres)), attendu)

    def test_curseur_de_jeux_a_trois_valeurs_utilise_les_deux_premieres(self):
        self.assertEqual(construire_filtre_carte(self.donnees(jeux=[10, 40, 60])), '(jeux_count 10 TO 40)')

    def test_filtres_combines_par_and(self):
        donnees = self.donnees(etats=["Disparu"], facteurs=[SimpleNamespace(nom="Merklin")],
                               manufactures=[SimpleNamespace(nom="Manufacture fictive")], jeux=[0, 20],
                               monument=True, departements=["Sarthe"])
        self.assertEqual(
            construire_filtre_carte(donnees),
            '(etat = "Disparu") AND (facet_facteurs = "Merklin") AND (facet_manufactures = "Manufacture fictive")'
            ' AND (jeux_count 0 TO 20) AND (monument_historique = "true") AND (departement = "Sarthe")'
        )


class RechercherOrguesCarteTestCase(SimpleTestCase):
    """
    Point d'accès de la vue carte à Meilisearch : un échec devient RechercheCarteIndisponible.
    """

    filtre = '(departement = "Sarthe")'
    resultats = {"hits": [], "facetDistribution": {"region": {}, "departement": {}}}

    @override_settings(MEILISEARCH_URL=MEILISEARCH_FICTIF)
    def test_renvoie_les_resultats_bruts_de_l_index_des_orgues(self):
        with mock.patch("orgues.services.carte.meilisearch.Client") as client:
            index = client.return_value.index.return_value
            index.search.return_value = self.resultats
            resultats = rechercher_orgues_carte(self.filtre)
        self.assertEqual(resultats, self.resultats)
        self.assertEqual(client.call_args.kwargs["timeout"], DELAI_MEILISEARCH_SECONDES)
        client.return_value.index.assert_called_once_with(uid="orgues")
        index.search.assert_called_once_with(
            None, {"facets": ["region", "departement"], "limit": 100000, "filter": self.filtre})

    @override_settings(MEILISEARCH_URL=MEILISEARCH_FICTIF)
    def test_echec_de_meilisearch_leve_recherche_indisponible_et_est_journalise(self):
        with mock.patch("orgues.services.carte.meilisearch.Client") as client:
            client.return_value.index.return_value.search.side_effect = MeilisearchCommunicationError("injoignable")
            with self.assertLogs("orgues.services.carte", level="ERROR"):
                with self.assertRaises(RechercheCarteIndisponible):
                    rechercher_orgues_carte(self.filtre)

    @override_settings(MEILISEARCH_URL=MEILISEARCH_FICTIF)
    def test_reponse_ou_url_inexploitable_leve_recherche_indisponible_et_est_journalise(self):
        erreurs = [json.JSONDecodeError("corps non JSON", "<html>", 0), MissingSchema("URL sans schéma")]
        for erreur in erreurs:
            with self.subTest(erreur=type(erreur).__name__):
                with mock.patch("orgues.services.carte.meilisearch.Client") as client:
                    client.return_value.index.return_value.search.side_effect = erreur
                    with self.assertLogs("orgues.services.carte", level="ERROR"):
                        with self.assertRaises(RechercheCarteIndisponible):
                            rechercher_orgues_carte(self.filtre)

    @override_settings(MEILISEARCH_URL=False)
    def test_meilisearch_non_configure_leve_recherche_indisponible_sans_creer_de_client(self):
        with mock.patch("orgues.services.carte.meilisearch.Client") as client:
            with self.assertLogs("orgues.services.carte", level="WARNING"):
                with self.assertRaises(RechercheCarteIndisponible):
                    rechercher_orgues_carte(self.filtre)
        client.assert_not_called()


@override_settings(FULL_SITE_URL="https://portail.test")
class OrgueCarteRechercheIndisponibleTestCase(TestCase):
    """
    Quand la recherche des orgues échoue, la carte répond une erreur JSON gérée (503) sans détail technique,
    et la page prévoit un message qui oriente vers la liste des orgues.
    """

    url = reverse('orgues:orgue-carte')
    message = {"message": "La recherche des orgues est momentanément indisponible."}

    @override_settings(MEILISEARCH_URL=MEILISEARCH_FICTIF)
    def test_meilisearch_injoignable_renvoie_503(self):
        with mock.patch("orgues.services.carte.meilisearch.Client") as client:
            client.return_value.index.return_value.search.side_effect = MeilisearchCommunicationError("injoignable")
            with self.assertLogs("orgues.services.carte", level="ERROR"):
                response = self.client.post(self.url, {"departements": ["72"]})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), self.message)

    @override_settings(MEILISEARCH_URL=False)
    def test_meilisearch_non_configure_renvoie_503_sans_creer_de_client(self):
        with mock.patch("orgues.services.carte.meilisearch.Client") as client:
            with self.assertLogs("orgues.services.carte", level="WARNING"):
                response = self.client.post(self.url, {"departements": ["72"]})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), self.message)
        client.assert_not_called()

    @override_settings(MEILISEARCH_URL=False)
    def test_sans_filtre_la_carte_lit_le_cache_sans_interroger_meilisearch(self):
        cache = {"totaux_regions": {}, "totaux_departements": {}, "orgues_geojson": {"type": "FeatureCollection",
                                                                                     "features": []}}
        with tempfile.NamedTemporaryFile("w", suffix=".json") as fichier:
            json.dump(cache, fichier)
            fichier.flush()
            with override_settings(CACHE_CARTE=fichier.name), \
                    mock.patch("orgues.services.carte.meilisearch.Client") as client:
                response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), cache)
        client.assert_not_called()

    @override_settings(MEILISEARCH_URL=False)
    def test_page_prevoit_un_message_annonce_vers_la_liste(self):
        url_liste = "https://portail.test" + reverse('orgues:orgue-list')
        response = self.client.get(self.url)
        self.assertContains(response, '<div id="recherche_indisponible" role="alert" hidden>')
        self.assertContains(response, f'<a href="{url_liste}">Consulter la liste des orgues</a>', html=True)

    @override_settings(MEILISEARCH_URL=False)
    def test_iframe_prevoit_un_message_annonce_vers_la_liste_en_nouvelle_fenetre(self):
        url_liste = "https://portail.test" + reverse('orgues:orgue-list')
        response = self.client.get(self.url, {"iframe": "true"})
        self.assertContains(response, f'''
            <div id="recherche_indisponible" role="alert" hidden>
              <p>La recherche des orgues est momentanément indisponible : la carte ne peut pas afficher les orgues.</p>
              <a href="{url_liste}" target="_blank" rel="noopener">
                Consulter la liste des orgues<span class="sr-only"> (nouvelle fenêtre)</span>
              </a>
            </div>''', html=True)
