import csv
import logging
import os
from collections import Counter, deque
from datetime import datetime, timedelta

import meilisearch
import pandas as pd
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.forms import modelformset_factory
from django.http import JsonResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy, reverse
from django.views.generic import DetailView, TemplateView
from django.views.generic.base import View

import orgues.forms as orgue_forms
from accounts.models import User
from fabutils.fablog import load_fabaccess_logs
from fabutils.mixins import FabCreateView, FabListView, FabDeleteView, FabUpdateView, FabView, FabCreateViewJS, \
    FabDetailView
from orgues.api.serializers import OrgueSerializer, OrgueResumeSerializer
from project import settings
from .models import Orgue, Clavier, Jeu, Evenement, Facteur, TypeJeu, Fichier, Image, Source
from .codification import Codification

logger = logging.getLogger("fabaccess")


class OrgueList(TemplateView):
    """
    Liste des orgues.
    Cette page est vide au démarrage, la récupération des orgues se fait après coup en javascript via
    la vue OrgueSearch.
    """
    template_name = "orgues/orgue_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["departements"] = Orgue.CHOIX_DEPARTEMENT
        context["departement"] = self.request.GET.get("departement")
        context["query"] = self.request.GET.get("query")
        context["limit"] = self.request.GET.get("limit")
        context["page"] = self.request.GET.get("page")
        return context


class OrgueSearch(View):
    """
    Vue de recherche d'orgue.
    Principalement appelée par du code javascript dans orgues/orgue_list.html
    Cette vue utilise le moteur de recherche "meilisearch" ou un moteur de recherche SQL dégradé quand meilisearch
    n'est pas disponible (settings.MEILISEARCH_URL=False)
    """
    paginate_by = 20

    def post(self, request, *args, **kwargs):
        request.session['orgues_url'] = "{}{}".format(reverse('orgues:orgue-list'), request.POST.get('pageUrl'))
        page = request.POST.get('page', 1)
        departement = request.POST.get('departement', '')
        query = request.POST.get('query')
        if settings.MEILISEARCH_URL:
            results = self.search_meilisearch(page, departement, query)
        else:
            results = self.search_sql(page, departement, query)
        return JsonResponse(results)

    @staticmethod
    def search_sql(page, departement, query):
        """
        Moteur de recherche dégradé.
        Imite un résultat au format meilisearch pour être compatible avec la template de rendu
        """
        queryset = Orgue.objects.all()
        if departement:
            queryset = queryset.filter(departement=departement)
        if query:
            terms = [term.lower() for term in query.split(" ") if term]
            query = Q()
            for term in terms:
                query = query & (Q(region__icontains=term) | Q(commune__icontains=term) | Q(edifice__icontains=term))
            queryset = queryset.filter(query)
        paginator = Paginator(queryset, OrgueSearch.paginate_by)
        object_list = paginator.page(page).object_list
        hits = []
        for result in OrgueResumeSerializer(object_list, many=True).data:
            hit = result.copy()
            hit['_formatted'] = result
            hits.append(hit)
        return {
            'hits': hits,
            'pages': paginator.num_pages,
            'nbHits': paginator.count
        }

    @staticmethod
    def search_meilisearch(page, departement, query):
        """
        Moteur de recherche avancé
        """
        try:
            client = meilisearch.Client(settings.MEILISEARCH_URL, settings.MEILISEARCH_KEY)
            index = client.get_index(uid='orgues')
        except:
            return JsonResponse({'message': 'Le moteur de recherche est mal configuré'}, status=500)

        try:
            offset = (int(page) - 1) * OrgueSearch.paginate_by
        except:
            offset = 0
        options = {'attributesToHighlight': ['*'], 'offset': offset, 'limit': OrgueSearch.paginate_by}
        if departement:
            options['facetFilters'] = ['departement:{}'.format(departement)]
        if not query:
            query = None
        results = index.search(query, options)
        results['pages'] = 1 + results['nbHits'] // OrgueSearch.paginate_by
        return results


class OrgueCarte(TemplateView):
    """
    Cartographie des orgues (gérée par Leaflet).
    La page est vide initialement et les orgues sont récupérés après coup en javascript via la vue OrgueListJS
    """
    template_name = "orgues/carte.html"


class OrgueListJS(View):
    """
    Cette vue est requêtée par Leaflet lors de l'affichage de la carte de France dans "orgues/carte.html"
    """

    def get(self, request, *args, **kwargs):
        data = Orgue.objects.filter(latitude__isnull=False).values("slug", "commune", "edifice", "latitude",
                                                                   "longitude", 'emplacement', "references_palissy")
        return JsonResponse(list(data), safe=False)


class FacteurListJSLeaflet(View):
    """
    Cette vue est requêtée par Leaflet lors de l'affichage de la carte de France
    """

    def get(self, request, *args, **kwargs):
        data = Facteur.objects.filter(latitude_atelier__isnull=False).values("nom", "latitude_atelier", "longitude_atelier")
        return JsonResponse(list(data), safe=False)

class FacteurListJSFiltre(FabListView):
    """
    Liste dynamique utilisée pour filtrer les facteurs d'orgue dans les menus déroulants select2. Utilisée pour le filtre de la carte.
    documentation : https://select2.org/data-sources/ajax
    """
    model = Facteur
    permission_required = 'orgues.view_facteur'

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get("search")
        if query:
            queryset = queryset.filter(nom__icontains=query)
        return queryset

    def render_to_response(self, context, **response_kwargs):
        results = []
        if context["object_list"]:
            results = [{"id": u.id, "text": u.nom} for u in context["object_list"]]
        return JsonResponse({"results": results, "pagination": {"more": False}})

class FacteurListJSlonlat(FabListView):
    """
    Liste dynamique utilisée pour filtrer les facteurs d'orgue dans les menus déroulants select2. Utilisée pour le filtre de la carte.
    documentation : https://select2.org/data-sources/ajax
    """
    model = Facteur
    permission_required = 'orgues.view_facteur'
    paginate_by = 100000

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get("search")
        if query:
            queryset = queryset.filter(nom__icontains=query)
        return queryset

    def render_to_response(self, context, **response_kwargs):
        results = []
        if context["object_list"]:
            for u in context["object_list"]:
                if u.latitude_atelier != None and u.longitude_atelier != None:
                    results.append({"id": u.id, "text": u.nom, "latitude": u.latitude_atelier, "longitude": u.longitude_atelier})
        return JsonResponse({"results": results, "pagination": {"more": False}})



class OrgueFiltreJS(View):
    """
    JSON renvoyant la liste des orgues auxquels le facteur a participé.
    """

    def get(self, request, *args, **kwargs):
        facteur = request.GET.get("facteur")
        type_requete = request.GET.get("type")
        if facteur:
            requete = Orgue.objects.filter(evenements__facteurs__nom=facteur).distinct()
            if type_requete == "construction":
                requete = Orgue.objects.filter(Q(evenements__facteurs__nom=facteur) & (Q(evenements__type="construction")|Q(evenements__type="reconstruction"))).distinct()
            else:
                requete = Orgue.objects.filter(evenements__facteurs__nom=facteur).distinct()
        else:
            requete =  Orgue.objects.all()
        data =requete.values("slug", "commune", "edifice", "latitude", "longitude", 'emplacement', "references_palissy")
        return JsonResponse(list(data), safe=False)

class OrgueEtatsJS(View):
    """
    JSON décrivant les états des orgues pour une région
    Si pas de région alors envoie les infos aggrégées pour toutes les régions
    """

    def get(self, request, *args, **kwargs):
        region = request.GET.get("region")
        queryset = Orgue.objects.all()
        if region:
            queryset = queryset.filter(region=region)
        valeurs = queryset.values_list("etat", flat=True)
        etats = dict(Counter(valeurs))
        etats["total"] = sum(list(etats.values()))
        if None in etats.keys():
            etats["inconnu"] = etats.get(None, 0)
            del etats[None]
        return JsonResponse(etats, safe=False)

class OrgueHistJS(View):
    """
    JSON décrivant les orgues classés ou inscrits au monument historique pour un département
    """
    def get(self, request, *args, **kwargs):
        region = request.GET.get("region")
        queryset = Orgue.objects.all()
        if region:
            queryset = queryset.filter(region=region)
        valeurs = queryset.values_list("references_palissy", flat=True)
        references_palissy = dict(Counter(valeurs))
        references_palissy["total"] = sum(list(references_palissy.values()))
        if None in references_palissy.keys():
            references_palissy["PasCla"] = references_palissy.get(None, 0)
            del references_palissy[None]
        #if evenementstot["type"]
        return JsonResponse(references_palissy, safe=False)

class OrgueEtatsJSDep(View):
    """
    JSON décrivant les états des orgues pour un département
    Si pas de région alors envoie les infos aggrégées pour toutes les régions
    """
    def get(self, request, *args, **kwargs):
        """Un if ou deux fonctions"""
        departement = request.GET.get("departement")
        queryset = Orgue.objects.all()
        if departement:
            queryset = queryset.filter(departement=departement)
        valeurs = queryset.values_list("etat", flat=True)
        etats = dict(Counter(valeurs))
        etats["total"] = sum(list(etats.values()))
        if None in etats.keys():
            etats["inconnu"] = etats.get(None, 0)
            del etats[None]
        return JsonResponse(etats, safe=False)

class OrgueHistJSDep(View):
    """
    JSON décrivant les orgues classés ou inscrits au monument historique pour un département
    """
    def get(self, request, *args, **kwargs):
        departement = request.GET.get("departement")
        queryset = Orgue.objects.all()
        if departement:
            queryset = queryset.filter(departement=departement)
        valeurs = queryset.values_list("references_palissy", flat=True)
        references_palissy = dict(Counter(valeurs))
        references_palissy["total"] = sum(list(references_palissy.values()))
        if None in references_palissy.keys():
            references_palissy["PasCla"] = references_palissy.get(None, 0)
            del references_palissy[None]
        return JsonResponse(references_palissy, safe=False)


class OrgueDetail(DetailView):
    """
    Vue de détail (lecture seule) d'un orgue
    """
    model = Orgue
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_object(self, queryset=None):

        logger.info("{user};{method};{get_full_path};200".format(user=self.request.user,
                                                                 method=self.request.method,
                                                                 get_full_path=self.request.META.get('HTTP_REFERER')))
        orgue = Orgue.objects.filter(Q(slug=self.kwargs['slug']) | Q(codification=self.kwargs['slug'])).first()
        if not orgue:
            raise Http404
        return orgue

    def render_to_response(self, context, **response_kwargs):
        if self.request.GET.get("format") == "json":
            return JsonResponse(OrgueSerializer(self.object, context={
                "request": self.request,
            }).data, safe=False)
        return super().render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["claviers"] = self.object.claviers.all().prefetch_related('type', 'jeux', 'jeux__type')
        context["evenements"] = self.object.evenements.all().prefetch_related('facteurs')
        context["facteurs_evenements"] = self.object.evenements.filter(facteurs__isnull=False).prefetch_related(
            'facteurs').distinct()
        return context


class OrgueDetailExemple(View):
    """
    Redirige vers la fiche la mieux complétée du site
    """

    def get(self, request, *args, **kwargs):
        orgue = Orgue.objects.order_by('-completion').first()
        return redirect(orgue.get_absolute_url())


class OrgueCreate(FabCreateView):
    """
    Création d'un nouvel orgue
    """
    model = Orgue
    permission_required = 'orgues.add_orgue'
    form_class = orgue_forms.OrgueCreateForm
    success_url = reverse_lazy('orgues:orgue-list')
    success_message = 'Nouvel orgue créé'
    template_name = "orgues/orgue_create.html"

    def form_valid(self, form):
        form.instance.updated_by_user = self.request.user
        c = Codification(form.instance.commune, form.instance.edifice, form.instance.designation)
        form.instance.commune = c.commune
        form.instance.departement = c.departement
        form.instance.code_departement = c.code_departement
        form.instance.region = c.region
        form.instance.code_insee = c.code_insee
        form.instance.edifice = c.edifice
        form.instance.codification = c.codification
        return super().form_valid(form)


class OrgueUpdateMixin(FabUpdateView):
    """
    Mixin de modification d'un orgue qui permet de systématiquement:
     - vérifier la permission
     - enregistrer l'utilisateur qui a fait la modification
     - inclure l'instance 'orgue' dans la template html
    """
    model = Orgue
    slug_field = 'uuid'
    slug_url_kwarg = 'orgue_uuid'
    permission_required = 'orgues.change_orgue'

    def form_valid(self, form):
        form.instance.updated_by_user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return self.object.get_update_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["orgue"] = self.object
        return context


class OrgueDetailAvancement(FabDetailView):
    """
    Vue de détail du score d'avancement d'un orgue.
    Toutes les règles de calcul sont définies dans la méthode Orgue.infos_completions
    """
    model = Orgue
    slug_field = 'uuid'
    slug_url_kwarg = 'orgue_uuid'
    permission_required = 'orgues.change_orgue'
    template_name = "orgues/orgue_detail_avancement.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        self.object.save()  # on recalcule l'avancement pour être sûr
        context["orgue"] = self.object
        return context


class OrgueUpdate(OrgueUpdateMixin, FabUpdateView):
    """
    Mise à jour des informations générales d'un orgue
    """
    form_class = orgue_forms.OrgueGeneralInfoForm
    success_message = 'Informations générales mises à jour !'


    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


class OrgueUpdateInstrumentale(OrgueUpdateMixin):
    """
    Mise à jour de la partie instrumentale d'un orgue
    """
    form_class = orgue_forms.OrgueInstrumentaleForm
    success_message = 'Tuyauterie mise à jour, merci !'
    template_name = "orgues/orgue_form_instrumentale.html"

    def get_success_url(self):
        success_url = reverse('orgues:orgue-update-instrumentale', args=(self.object.uuid,))
        return self.request.POST.get("next", success_url)


class OrgueUpdateComposition(OrgueUpdateMixin):
    """
    Mise à jour de la composition d'un orgue
    """
    model = Orgue
    form_class = orgue_forms.OrgueCompositionForm
    template_name = "orgues/orgue_form_composition.html"
    success_message = 'Composition mise à jour, merci !'

    def get_object(self, queryset=None):
        object = super().get_object()
        object.resume_composition = object.calcul_resume_composition()
        object.save()
        return object

    def get_success_url(self):
        success_url = reverse('orgues:orgue-update-composition', args=(self.object.uuid,))
        return self.request.POST.get("next", success_url)


class OrgueUpdateBuffet(OrgueUpdateMixin):
    """
    Mise à jour du buffet d'un orgue
    """
    model = Orgue
    form_class = orgue_forms.OrgueBuffetForm
    template_name = "orgues/orgue_form_buffet.html"
    success_message = 'Buffet mis à jour, merci !'

    def get_success_url(self):
        success_url = reverse('orgues:orgue-update-buffet', args=(self.object.uuid,))
        return self.request.POST.get("next", success_url)


class OrgueUpdateLocalisation(OrgueUpdateMixin):
    """
    Mise à jour de la localisation d'un orgue
    """
    form_class = orgue_forms.OrgueLocalisationForm
    permission_required = "orgues.change_localisation"
    success_message = 'Localisation mise à jour, merci !'
    template_name = "orgues/orgue_form_localisation.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        """
        Enregistrement automatique du code du département
        """
        departement = form.cleaned_data['departement']
        for code_departement, nom_departement in Orgue.CHOIX_DEPARTEMENT:
            if departement == nom_departement:
                form.instance.code_departement = code_departement
                break
        return super().form_valid(form)

    def get_success_url(self):
        success_url = reverse('orgues:orgue-update-localisation', args=(self.object.uuid,))
        return self.request.POST.get("next", success_url)


class OrgueDelete(FabDeleteView):
    """
    Suppression d'un orgue
    """
    model = Orgue
    slug_field = 'uuid'
    slug_url_kwarg = 'orgue_uuid'
    permission_required = 'orgues.delete_orgue'
    success_url = reverse_lazy('orgues:orgue-list')
    success_message = 'Orgue supprimé'


class EvenementList(FabListView):
    """
    Liste des évenements associés à un orgue
    """
    model = Evenement
    permission_required = "orgues.add_evenement"

    def get_queryset(self):
        self.orgue = get_object_or_404(Orgue, uuid=self.kwargs["orgue_uuid"])
        return self.orgue.evenements.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["orgue"] = self.orgue
        return context


class TypeJeuCreateJS(FabCreateViewJS):
    """
    Création d'un nouveau type de jeu.
    Cette vue est appelée par du code javascript.
    """
    model = TypeJeu
    permission_required = "orgues.add_typejeu"
    fields = ["nom"]
    success_message = "Nouveau type de jeu créé, merci !"

    def post(self, request, *args, **kwargs):
        nom = request.POST.get("nom")
        hauteur = request.POST.get("hauteur")
        typejeu, created = TypeJeu.objects.get_or_create(nom=nom, hauteur=hauteur)
        if created:
            typejeu.updated_by_user = self.request.user
            typejeu.save()
        return JsonResponse(
            {'message': self.success_message, 'facteur': {'id': typejeu.id, 'nom': str(typejeu)}})


class TypeJeuUpdate(FabUpdateView):
    """
    Mise à jour d'un type de jeu
    """
    model = TypeJeu
    permission_required = "orgues.change_typejeu"
    fields = ["nom"]
    success_message = "Type de jeu mis à jour, merci !"

    def get_success_url(self):
        return reverse('orgues:typejeu-update', args=(self.object.pk,))


class TypeJeuListJS(FabView):
    """
    Liste dynamique utilisée pour filtrer les jeux d'orgues dans les menus déroulants select2.

    Cette vue utilise le moteur de recherche "meilisearch" ou un moteur de recherche SQL dégradé quand meilisearch
    n'est pas disponible (settings.MEILISEARCH_URL=False)

    documentation : https://select2.org/data-sources/ajax
    """
    permission_required = "orgues.view_jeu"
    paginate_by = 20

    def get(self, request, *args, **kwargs):
        page = request.GET.get('page', 1)
        query = request.GET.get('q', '')
        if settings.MEILISEARCH_URL:
            results = self.search_meilisearch(page, query)
        else:
            results = self.search_sql(page, query)
        return JsonResponse(results)

    @staticmethod
    def search_sql(page, query):
        """
        Moteur de recherche dégradé.
        Imite un résultat au format meilisearch pour être compatible avec la template de rendu
        """
        queryset = TypeJeu.objects.all()
        if query:
            terms = [term.lower() for term in query.split(" ") if term]
            query = Q()
            for term in terms:
                query = query & (Q(nom__icontains=term) | Q(hauteur__icontains=term))
            queryset = queryset.filter(query)
        paginator = Paginator(queryset, TypeJeuListJS.paginate_by)
        object_list = paginator.page(page).object_list
        return {
            "results": [{'id': jeu.id, 'text': str(jeu)} for jeu in object_list],
            "pagination": {"more": int(page) < paginator.num_pages}
        }

    @staticmethod
    def search_meilisearch(page, query):
        """
        Moteur de recherche avancé
        """
        try:
            client = meilisearch.Client(settings.MEILISEARCH_URL, settings.MEILISEARCH_KEY)
            index = client.get_index(uid='types_jeux')
        except:
            return JsonResponse({'message': 'Le moteur de recherche est mal configuré'}, status=500)

        try:
            offset = (int(page) - 1) * TypeJeuListJS.paginate_by
        except:
            offset = 0
        options = {'offset': offset, 'limit': TypeJeuListJS.paginate_by}
        results = index.search(query, options)

        return {
            "results": [{'id': r['id'], 'text': r['nom']} for r in results['hits']],
            "pagination": {"more": results['nbHits'] > TypeJeuListJS.paginate_by}
        }


class FacteurListJS(FabListView):
    """
    Liste dynamique utilisée pour filtrer les facteurs d'orgue dans les menus déroulants select2.
    documentation : https://select2.org/data-sources/ajax
    """
    model = Facteur
    permission_required = 'orgues.view_facteur'
    paginate_by = 30

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get("search")
        if query:
            queryset = queryset.filter(nom__icontains=query)
        return queryset

    def render_to_response(self, context, **response_kwargs):
        results = []
        more = context["page_obj"].number < context["paginator"].num_pages
        if context["object_list"]:
            results = [{"id": u.id, "text": u.nom} for u in context["object_list"]]
        return JsonResponse({"results": results, "pagination": {"more": more}})

class CommuneListJS(FabListView):
    """
    Liste dynamique utilisée pour filtrer les communes dans le menu déroulant select2 pour créer un nouvel orgue.
    documentation : https://select2.org/data-sources/ajax
    """
    model = Facteur
    permission_required = 'orgues.add_orgue'
    paginate_by = 30

    def get_queryset(self):
        query = self.request.GET.get("search")
        with open('code_INSEE.csv', 'r', encoding='utf-8') as read_obj:
            csv_reader = csv.reader(read_obj, delimiter=';')
            results = []
            for row in csv_reader:
                ligne=row[0].split(",")  
                if query :
                    if query in ligne[3].lower():    
                        dictionnaire = {"id": ligne[3]+", "+ligne[4], "nom": ligne[3]+", "+ligne[4]}
                        results.append(dictionnaire)
                else:
                    dictionnaire = {"id": ligne[3]+", "+ligne[4], "nom": ligne[3]+", "+ligne[4]}
                    results.append(dictionnaire)
        return results

    def render_to_response(self, context, **response_kwargs):
        results = []
        more = context["page_obj"].number < context["paginator"].num_pages
        if context["object_list"]:
            results = [{"id": u["id"], "text": u["nom"]} for u in context["object_list"]]
        return JsonResponse({"results": results, "pagination": {"more": more}})

class DesignationListJS(FabListView):
    """
    Liste dynamique utilisée pour filtrer les désignations dans le menu déroulant select2 pour créer un nouvel orgue.
    Si une désignation est manquante, l'ajouter dans la liste liste_designation.
    documentation : https://select2.org/data-sources/ajax
    """
    model = Facteur
    permission_required = 'orgues.add_orgue'
    paginate_by = 30

    def get_queryset(self):
        query = self.request.GET.get("search")
        liste_designation = ['G.O.', 'orgue', 'Grand Orgue', 'orgue de tribune', 'orgue de transept', 'orgue positif','orgue régale',
"orgue d'accompagnement",'petit orgue', "orgue d'étude", 'positif', 'grand positif', 'chapelle', 'oratoire',
"chapelle d'hiver", 'chapelle de la Vierge', 'sacristie', 'O.C.', 'O.C.1', 'O.C.2', 'crypte', 'Orgue coffre','auditorium',
'orgue 1', 'orgue 2','ancien','nouveau','1', '2', '3', '4', '5', '6', '7', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII',
"Orgue d'étude", 'Orgue espagnol', 'Orgue majorquin', 'Orgue napolitain', "orgue d'étude (1982)", "orgue d'étude (1968)",
'polyphone', 'buffet', 'orgue à rouleau', 'orgue à cylindre', '']
        results = []
        for denomination in liste_designation:
            if query :
                if query in denomination.lower():    
                    dictionnaire = {"id": denomination, "nom": denomination}
                    results.append(dictionnaire)
            else:
                dictionnaire = {"id": denomination, "nom": denomination}
                results.append(dictionnaire)
        return results

    def render_to_response(self, context, **response_kwargs):
        results = []
        more = context["page_obj"].number < context["paginator"].num_pages
        if context["object_list"]:
            results = [{"id": u["id"], "text": u["nom"]} for u in context["object_list"]]
        return JsonResponse({"results": results, "pagination": {"more": more}})


class EvenementCreate(FabCreateView):
    """
    Création d'un nouvel évenement associé à un orgue
    """
    model = Evenement
    permission_required = "orgues.add_evenement"
    form_class = orgue_forms.EvenementForm
    success_message = "Nouvel événement ajouté à la frise, merci!"

    def form_valid(self, form):
        orgue = get_object_or_404(Orgue, uuid=self.kwargs['orgue_uuid'])
        form.instance.orgue = orgue
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["orgue"] = Orgue.objects.get(uuid=self.kwargs["orgue_uuid"])
        return context

    def get_success_url(self):
        return reverse('orgues:evenement-list', args=(self.kwargs["orgue_uuid"],))


class EvenementUpdate(FabUpdateView):
    """
    Mise à jour d'un évenement
    """
    model = Evenement
    permission_required = "orgues.change_evenement"
    form_class = orgue_forms.EvenementForm
    success_message = "Evénement mis à jour, merci !"

    def form_valid(self, form):
        form.instance.updated_by_user = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["orgue"] = self.object.orgue
        return context

    def get_success_url(self):
        return reverse('orgues:evenement-list', args=(self.object.orgue.uuid,))


class EvenementDelete(FabDeleteView):
    """
    Suppression d'un événement
    """
    model = Evenement
    permission_required = "orgues.delete_evenement"
    success_message = "Evenement supprimé, merci !"

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["orgue"] = self.object.orgue
        return context

    def get_success_url(self):
        return reverse('orgues:evenement-list', args=(self.object.orgue.uuid,))


class ClavierCreate(FabView):
    """
    Ajout d'un clavier
    """
    model = Clavier
    permission_required = "orgues.add_clavier"
    form_class = orgue_forms.ClavierForm

    def get(self, request, *args, **kwargs):
        JeuFormset = modelformset_factory(Jeu, orgue_forms.JeuForm, extra=10)
        orgue = get_object_or_404(Orgue, uuid=self.kwargs.get('orgue_uuid'))
        context = {
            "jeux_formset": JeuFormset(queryset=Jeu.objects.none()),
            "clavier_form": orgue_forms.ClavierForm(),
            "orgue": orgue
        }
        return render(request, "orgues/clavier_form.html", context)

    def post(self, request, *args, **kwargs):
        orgue = get_object_or_404(Orgue, uuid=self.kwargs.get('orgue_uuid'))
        JeuFormset = modelformset_factory(Jeu, orgue_forms.JeuForm)

        jeux_formset = JeuFormset(self.request.POST)
        clavier_form = orgue_forms.ClavierForm(self.request.POST)
        if jeux_formset.is_valid() and clavier_form.is_valid():
            clavier_form.instance.orgue = orgue
            clavier = clavier_form.save()
            jeux = jeux_formset.save()
            for jeu in jeux:
                jeu.clavier = clavier
                jeu.save()
            if request.POST.get("continue") == "true":
                return redirect(reverse('orgues:clavier-update', args=(clavier.pk,)) + "#jeux")
            messages.success(self.request, "Nouveau clavier ajouté, merci !")
            return redirect('orgues:orgue-update-composition', orgue_uuid=orgue.uuid)
        else:
            context = {
                "jeux_formset": jeux_formset,
                "clavier_form": clavier_form,
                "orgue": orgue
            }
            return render(request, "orgues/clavier_form.html", context)


class ClavierUpdate(FabUpdateView):
    """
    Mise à jour d'un clavier
    """
    model = Clavier
    permission_required = "orgues.change_clavier"
    form_class = orgue_forms.ClavierForm

    def get(self, request, *args, **kwargs):
        clavier = get_object_or_404(Clavier, pk=kwargs["pk"])
        JeuFormset = modelformset_factory(Jeu, orgue_forms.JeuForm, extra=3, can_delete=True)
        context = {
            "jeux_formset": JeuFormset(queryset=clavier.jeux.all()),
            "clavier_form": orgue_forms.ClavierForm(instance=clavier),
            "orgue": clavier.orgue,
            "clavier": clavier
        }
        return render(request, "orgues/clavier_form.html", context)

    def post(self, request, *args, **kwargs):
        clavier = get_object_or_404(Clavier, pk=kwargs["pk"])
        JeuFormset = modelformset_factory(Jeu, orgue_forms.JeuForm, extra=3, can_delete=True)
        jeux_formset = JeuFormset(self.request.POST, queryset=clavier.jeux.all())
        clavier_form = orgue_forms.ClavierForm(self.request.POST, instance=clavier)
        if jeux_formset.is_valid() and clavier_form.is_valid():
            clavier = clavier_form.save()
            jeux = jeux_formset.save()
            for jeu in jeux:
                jeu.clavier = clavier
                jeu.save()
            if request.POST.get("continue") == "true":
                return redirect(reverse('orgues:clavier-update', args=(clavier.pk,)) + "#jeux")
            messages.success(self.request, "Clavier mis à jour, merci !")
            return redirect('orgues:orgue-update-composition', orgue_uuid=clavier.orgue.uuid)
        else:
            context = {
                "jeux_formset": jeux_formset,
                "clavier_form": clavier_form,
                "orgue": clavier.orgue
            }
            return render(request, "orgues/clavier_form.html", context)


class ClavierDelete(FabDeleteView):
    """
    Suppression d'un clavier
    """
    model = Clavier
    permission_required = "orgues.delete_clavier"
    success_message = "Clavier supprimé, merci !"

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["orgue"] = self.object.orgue
        return context

    def get_success_url(self):
        return reverse('orgues:orgue-update-composition', args=(self.object.orgue.uuid,))


class FacteurCreateJS(FabCreateViewJS):
    """
    Création d'un nouveau facteur.
    Vue appelée par du code javascript
    """
    model = Facteur
    permission_required = "orgues.add_facteur"
    fields = "__all__"

    def post(self, request, *args, **kwargs):
        nom = request.POST.get("nom")
        facteur, created = Facteur.objects.get_or_create(nom=nom)
        return JsonResponse(
            {'message': self.success_message, 'facteur': {'id': facteur.id, 'nom': facteur.nom}})


class FichierList(FabListView):
    """
    Liste des facteurs
    """
    model = Fichier
    permission_required = "orgues.add_fichier"
    paginate_by = 50

    def get_queryset(self):
        self.orgue = get_object_or_404(Orgue, uuid=self.kwargs["orgue_uuid"])
        return Fichier.objects.filter(orgue=self.orgue)

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["orgue"] = self.orgue
        context["form"] = orgue_forms.FichierForm()
        return context


class FichierCreate(FabCreateView):
    """
    Création d'un fichier associé à un orgue
    """
    model = Fichier
    permission_required = "orgues.add_fichier"
    form_class = orgue_forms.FichierForm
    template_name = "orgues/fichier_list.html"

    def form_valid(self, form):
        orgue = get_object_or_404(Orgue, uuid=self.kwargs["orgue_uuid"])
        fichier = form.save(commit=False)
        fichier.orgue = orgue
        fichier.save()
        messages.success(self.request, "Fichier créé, merci !")
        return redirect('orgues:fichier-list', orgue_uuid=orgue.uuid)

    def get_context_data(self, **kwargs):
        orgue = get_object_or_404(Orgue, uuid=self.kwargs["orgue_uuid"])

        context = super().get_context_data()
        context["orgue"] = orgue
        context["object_list"] = Fichier.objects.filter(orgue=orgue)
        return context


class FichierDelete(FabDeleteView):
    """
    Suppression d'un fichier associé à un orgue
    """
    model = Fichier
    permission_required = "orgues.delete_fichier"
    success_message = "Fichier supprimé, merci !"

    def get_success_url(self):
        return reverse('orgues:fichier-list', args=(self.object.orgue.uuid,))


class ImageList(FabListView):
    """
    Liste des images de l'orgue.
    Un POST sur cette vue permet de réordonner les images
    """
    model = Image
    permission_required = "orgues.view_image"
    paginate_by = 50

    def post(self, request, *args, **kwargs):
        orgue = get_object_or_404(Orgue, uuid=self.kwargs["orgue_uuid"])
        image_pks = request.POST.getlist('image_pks[]')
        with transaction.atomic():
            for image in orgue.images.all():
                image.order = image_pks.index(str(image.pk))
                image.save()
        return JsonResponse({"message": "success"})

    def get_queryset(self):
        self.orgue = get_object_or_404(Orgue, uuid=self.kwargs["orgue_uuid"])
        return self.orgue.images.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["orgue"] = self.orgue
        return context


class ImageCreate(FabView):
    """
    Vue de chargement d'une image.
    Les images sont chargées et redimensionnée automatiquement en javascript côté client.
    """
    permission_required = "orgues.add_image"
    template_name = "orgues/image_create.html"

    def get(self, request, *args, **kwargs):
        orgue = get_object_or_404(Orgue, uuid=self.kwargs["orgue_uuid"])
        return render(request, self.template_name, {"orgue": orgue, "MAX_PIXEL_WIDTH": Image.MAX_PIXEL_WIDTH})

    def post(self, request, *args, **kwargs):
        """
        Vue appelée par filepond https://pqina.nl/filepond/docs/patterns/api/server/
        """
        image = self.request.FILES['filepond']
        credit = self.request.POST['credit']
        orgue = get_object_or_404(Orgue, uuid=self.kwargs["orgue_uuid"])
        image = Image.objects.create(orgue=orgue, image=image)
        if not (image.is_blackandwhite() or orgue.images.filter(is_principale=True).exists()):
            image.is_principale = True
        image.user = request.user
        image.credit = credit
        image.save()
        return JsonResponse({'ok': True})


class ImageDelete(FabDeleteView):
    """
    Suppression d'une image
    """
    model = Image
    permission_required = "orgues.delete_image"
    success_message = "Image supprimée, merci !"

    def get_success_url(self):
        return reverse('orgues:image-list', args=(self.object.orgue.uuid,))

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["orgue"] = self.object.orgue
        return context


class ImagePrincipaleUpdate(FabUpdateView):
    """
    Séléction et rognage de l'image principale d'un orgue dans le but de créer une vignette (utilise ajax et cropper.js)
    """
    model = Image
    fields = ['thumbnail_principale']
    permission_required = "orgues.change_image"
    success_message = "Vignette mise à jour, merci !"
    template_name = "orgues/image_principale_form.html"


    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        image = self.get_object()
        if image.is_blackandwhite():
            messages.warning(request,"Les images en noir & blanc ne peuvent pas devenir des vignettes")
            return redirect("orgues:image-list",orgue_uuid=image.orgue.uuid)
        return super().dispatch(request,*args,**kwargs)


    def form_valid(self, form):
        old_path = None
        try:
            old_path = Image.objects.get(pk=form.instance.pk).thumbnail_principale.path
        except:
            print('No old thumbnail')

        image = form.save(commit=False)
        image.orgue.images.update(is_principale=False)
        image.is_principale = True
        image.save()

        # remove old thumbnail
        if old_path:
            os.remove(old_path)

        messages.success(self.request, self.success_message)
        return JsonResponse({})

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["orgue"] = self.object.orgue
        return context


class ImageUpdate(FabUpdateView):
    """
    Modification de la légende ou du crédit d'une image
    """
    model = Image
    fields = ['credit', 'legende']
    permission_required = "orgues.change_image"
    success_message = "Informations mises à jour, merci"

    def get_success_url(self):
        return reverse('orgues:image-list', args=(self.object.orgue.uuid,))

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["orgue"] = self.object.orgue
        return context


class SourceList(FabListView):
    """
    Voir et éditer la liste des sources
    """
    model = Source
    permission_required = "orgues.view_source"

    def get_queryset(self):
        self.orgue = get_object_or_404(Orgue, uuid=self.kwargs["orgue_uuid"])
        queryset = super().get_queryset()
        queryset = queryset.filter(orgue=self.orgue)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["orgue"] = self.orgue
        return context


class SourceCreate(FabCreateView):
    model = Source
    permission_required = "orgues.add_source"
    form_class = orgue_forms.SourceForm
    success_message = "Nouvelle source ajoutée, merci!"

    def form_valid(self, form):
        orgue = get_object_or_404(Orgue, uuid=self.kwargs['orgue_uuid'])
        form.instance.orgue = orgue
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["orgue"] = Orgue.objects.get(uuid=self.kwargs["orgue_uuid"])
        return context

    def get_success_url(self):
        return reverse('orgues:source-list', args=(self.kwargs["orgue_uuid"],))


class SourceUpdate(FabUpdateView):
    model = Source
    permission_required = "orgues.change_source"
    form_class = orgue_forms.SourceForm
    success_message = "Source mise à jour, merci !"

    def form_valid(self, form):
        form.instance.updated_by_user = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["orgue"] = self.object.orgue
        return context

    def get_success_url(self):
        return reverse('orgues:source-list', args=(self.object.orgue.uuid,))


class SourceDelete(FabDeleteView):
    model = Source
    permission_required = "orgues.delete_source"
    success_message = "Source supprimée, merci !"

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["orgue"] = self.object.orgue
        return context

    def get_success_url(self):
        return reverse('orgues:source-list', args=(self.object.orgue.uuid,))


class SearchLogView(LoginRequiredMixin, TemplateView):
    template_name = 'orgues/search_log.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rows = int(self.request.GET.get("rows", 100))
        with open(settings.SEARCHLOG_FILE) as f:
            reader = csv.reader(deque(f, maxlen=rows), delimiter=";")
            search_logs = reversed(list(reader))
            context["search_logs"] = search_logs
        return context


class ConseilsFicheView(TemplateView):
    template_name = 'orgues/conseils_fiche.html'


class OrgueExport(FabView):
    permission_required = 'orgues.change_orgue'

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response.write(u'\ufeff'.encode('utf8'))
        response['Content-Disposition'] = 'attachment;filename=orgues-de-France_{}.csv'.format(
            datetime.today().strftime("%Y-%m-%d"))
        columns = [
            "codification",
            "code_departement",
            "departement",
            "code_insee",
            "commune",
            "ancienne_commune",
            "designation",
            "edifice",
            "references_palissy",
            "etat",
            "emplacement",
            "completion",
            "resume_composition",
        ]
        writer = csv.DictWriter(response, delimiter=';', fieldnames=columns)

        # header from verbose_names
        writer.writerow({column: Orgue._meta.get_field(column).verbose_name for column in columns})
        # data
        writer.writerows(Orgue.objects.values(*columns))

        return response


class Dashboard(FabView):
    """
    Dashboard d'avancement réservé aux admins
    """
    permission_required = 'orgues.add_orgue'

    def get(self, request, *args, **kwargs):
        context = {}
        pd.options.display.html.border = 0
        columns = ['departement', 'region', 'modified_date', 'updated_by_user__first_name',
                   'updated_by_user__last_name', 'completion']
        df = pd.DataFrame(Orgue.objects.values(*columns), columns=columns)
        df["user"] = df["updated_by_user__first_name"] + " " + df["updated_by_user__last_name"]

        # stats générales
        context["users_count"] = User.objects.count()
        context["image_count"] = Image.objects.count()
        context["jeu_count"] = Jeu.objects.count()

        # departements
        departements = df.groupby('departement').agg({'completion': ['count', 'mean']}).reset_index().round()
        departements.columns = ["Département", "Orgues", "Avancement (%)"]
        departements.sort_values("Avancement (%)", inplace=True)
        context["departments"] = departements.to_html(classes=['departments table table-sm'], index=False)

        # regions
        regions = df.groupby('region').agg({'completion': ['count', 'mean']}).reset_index().round()
        regions.columns = ["Region", "Orgues", "Avancement (%)"]
        regions.sort_values("Avancement (%)", inplace=True)
        context["regions"] = regions.to_html(classes=['regions table table-sm'], index=False)

        # utilisateurs
        utilisateurs = df.groupby('user').agg({'departement': 'count'}).reset_index().round()
        utilisateurs.columns = ["Utilisateur", "Orgues modifiés"]
        utilisateurs.sort_values("Orgues modifiés", inplace=True)
        context["users"] = utilisateurs.to_html(classes=['users table table-sm'], index=False)

        # Activité
        df = load_fabaccess_logs()
        df = df.loc[df["Date"] > datetime.now() - timedelta(days=30), :]
        df["strdate"] = df["Date"].dt.strftime("%Y-%m-%d")
        users_per_day = df.groupby("strdate").agg({"User": lambda x: x.nunique()})
        context["users_per_day"] = {
            "dates": list(users_per_day.index),
            "users": list(users_per_day["User"].values)
        }

        return render(request, 'orgues/dashboard.html', context=context)
