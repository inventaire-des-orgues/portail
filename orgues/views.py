import csv
import json
import logging
import os
from collections import deque
from datetime import datetime, timedelta, date
import pandas as pd

import meilisearch

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core import serializers
from django.core.paginator import Paginator
from django.db import connection, transaction
from django.db.models import Q, Count
from django.forms import modelformset_factory
from django.http import JsonResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView, TemplateView, ListView
from django.views.generic.base import View

import orgues.forms as orgue_forms
from accounts.models import User
from fabutils.fablog import load_fabaccess_logs
from fabutils.mixins import FabCreateView, FabListView, FabDeleteView, FabUpdateView, FabView, FabCreateViewJS, \
    FabDetailView
from orgues.api.serializers import OrgueSerializer, OrgueResumeSerializer

from project import settings

from .models import Orgue, Clavier, Jeu, Evenement, Facteur, TypeJeu, Fichier, Image, Source, Contribution, Provenance
import orgues.utilsorgues.correcteurorgues as co
import orgues.utilsorgues.codification as codif
import orgues.utilsorgues.code_geographique as codegeo

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
        context["region"] = self.request.GET.get("region")
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
        region = request.POST.get('region', '')
        query = request.POST.get('query')
        if settings.MEILISEARCH_URL:
            results = self.search_meilisearch(page, departement, region, query, request)
        else:
            results = self.search_sql(page, departement, region, query)
        return JsonResponse(results)

    @staticmethod
    def search_sql(page, departement, region, query):
        """
        Moteur de recherche dégradé.
        Imite un résultat au format meilisearch pour être compatible avec la template de rendu
        """
        queryset = Orgue.objects.all()
        if departement:
            queryset = queryset.filter(departement=departement)
        if region:
            queryset = queryset.filter(region=region)
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
            'totalPages': paginator.num_pages,
            'totalHits': paginator.count
        }

    @staticmethod
    def search_meilisearch(page, departement, region, query, request):
        """
        Moteur de recherche avancé
        """
        try:
            client = meilisearch.Client(settings.MEILISEARCH_URL, settings.MEILISEARCH_KEY)
            index = client.index(uid='orgues')
        except:
            return JsonResponse({'message': 'Le moteur de recherche est mal configuré'}, status=500)

        facets = ['departement', 'region', 'resume_composition_clavier', 'facet_facteurs', 'jeux', 'proprietaire', 'etat']
        options = {'attributesToHighlight': ['*'], 'hitsPerPage': OrgueSearch.paginate_by, 'page': int(page)}

        # Première requête qui permet de récupérer toutes les possibilités dans chaque facet
        options["facets"] = facets
        filter_init = []
        if departement:
            filter_init.append('departement="{}"'.format(departement))
        if region:
            filter_init.append('region="{}"'.format(region))
        if len(filter_init) > 0:
            options['filter'] = filter_init
        results_init = index.search(query, options)

        # Deuxième requête pour récupérer les orgues correspondant aux filtres
        filter = []
        filterResult = {}
        for facet in facets:
            arg = request.POST.get('filter_' + facet)
            if arg:
                values = arg.split(';;')
                filter.append(['{}="{}"'.format(facet, value) for value in values])
                filterResult[facet] = values
        init = request.POST.get('init')
        
        # Si c'est l'initialisation de la page ou d'un département, alors par défaut, on n'affiche pas les orgues disparus
        if init=="true":
            filter.append(['etat="{}"'.format(value[1]) for value in Orgue.CHOIX_ETAT if value[1] != "Disparu"])
        if departement:
            filter.append('departement="{}"'.format(departement))
        if region:
            filter.append('region="{}"'.format(region))
        if len(filter) > 0:
            options['filter'] = filter
        if not query:
            query = None
        sort = request.POST.get('sort')
        if sort and sort != 'pertinence':
            options['sort'] = [sort]
        results = index.search(query, options)
        if 'facetDistribution' in results:
            results['facets'] = OrgueSearch.convertFacets(results_init['facetDistribution'])
            del results['facetDistribution']
        
        # Si c'est l'initialisation de la page ou d'un département, 
        # alors par défaut, on ne surligne pas "Disparu" dans la colonne des filtres 
        if init=="true":
            filterResult['etat'] = ['Très bon, tout à fait jouable', 'Bon : jouable, défauts mineurs', 'Altéré : difficilement jouable', 'Dégradé ou en ruine : injouable', 'En restauration (ou projet initié)']
        results['filter'] = filterResult
        return results

    @staticmethod
    def convertFacets(facetDistribution):
        labels = {'departement': 'Département', 'region': 'Régions', 'resume_composition_clavier': 'Nombres de claviers', 'facet_facteurs': 'Facteurs', 'jeux': 'Jeux', 'proprietaire': 'Propriétaire', 'etat':'Etat'}
        return [{'label': labels[name], 'field': name,
                 'items': sorted([{'name': item, 'count': count} for item, count in values.items()], key=lambda k: k['name'])} for name, values in
                facetDistribution.items()]


class OrgueCarteOld(TemplateView):
    """
    Cartographie des orgues (gérée par Leaflet).
    La page est vide initialement et les orgues sont récupérés après coup en javascript via la vue OrgueListJS
    """
    template_name = "orgues/carte_old.html"


class OrgueCarte(TemplateView):
    """
    Cartographie des orgues (Mapbox).
    La page est vide initialement et les orgues sont récupérés après coup en javascript via une requête POST.
    Cette vue peut être appelée en iframe (avec le paramètre iframe=true) pour être intégrée dans un autre site.
    """
    template_name = "orgues/carte.html"

    @method_decorator(csrf_exempt)
    @method_decorator(xframe_options_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["form"] = orgue_forms.OrgueCarteForm()
        context["MAPBOX_ACCESS_TOKEN"] = settings.MAPBOX_ACCESS_TOKEN
        context["FULL_SITE_URL"] = settings.FULL_SITE_URL
        if self.request.GET.get("iframe") == "true":
            context["iframe"] = True
            context["extends_template"] = "orgues/carte_iframe.html"
        else:
            context["extends_template"] = "base.html"
        return context

    @staticmethod
    def meilisearch_results_to_map_json(results):
        features = []
        for orgue in results['hits']:
            features.append(
                {
                    "type": "Feature",
                    "id": orgue['id'],
                    "geometry": {
                        "type": "Point",
                        "coordinates": [orgue['longitude'], orgue['latitude']]
                    },
                    "properties": {
                        "nom": f"{orgue['edifice']} - {orgue['commune']}",
                        "monument_historique": orgue['monument_historique'],
                    },
                }
            )
        orgues_geojson = {
            "type": "FeatureCollection",
            "features": features
        }

        return {
            "totaux_regions": results['facetDistribution']['region'],
            "totaux_departements": results['facetDistribution']['departement'],
            "orgues_geojson": orgues_geojson
        }

    def post(self, request, *args, **kwargs):
        """
        On génère le geojson des orgues en fonction des filtres
        """
        form = orgue_forms.OrgueCarteForm(request.POST)
        if form.is_valid():
            try:
                client = meilisearch.Client(settings.MEILISEARCH_URL, settings.MEILISEARCH_KEY)
                index = client.index(uid='orgues')
            except:
                return JsonResponse({'message': 'Le moteur de recherche est mal configuré'}, status=500)

            options = {'facets': ['region', 'departement'], 'limit': 100000}
            filters = []
            if form.cleaned_data['etats']:
                etat_filter = " OR ".join([f'etat = "{etat}"' for etat in form.cleaned_data['etats']])
                filters.append(f'({etat_filter})')
            if form.cleaned_data['facteurs']:
                facteur_filter = " OR ".join([f'facet_facteurs = "{facteur.nom.strip()}"' for facteur in form.cleaned_data['facteurs']])
                filters.append(f'({facteur_filter})')
            if form.cleaned_data['jeux']:
                jeux_filter = f"jeux_count {form.cleaned_data['jeux'][0]} TO {form.cleaned_data['jeux'][1]}"
                filters.append(f'({jeux_filter})')
            if form.cleaned_data['monument']:
                filters.append(f'(monument_historique = "true")')
            if filters:
                options['filter'] = " AND ".join(filters)
                results = index.search(None, options)
                results = self.meilisearch_results_to_map_json(results)
            else:
                with open(settings.CACHE_CARTE, "r") as f:
                    results = json.load(f)
            return JsonResponse(results)
        else:
            return JsonResponse({'message': 'Le formulaire est invalide'}, status=400)


class OrgueCartePopup(View):
    """
    Génère des popups à la demande pour la carte des orgues
    """

    def get(self, request, *args, **kwargs):
        id = request.GET.get("orgue_id")
        orgue = Orgue.objects.get(id=id)
        orgues = Orgue.objects.filter(latitude=orgue.latitude, longitude=orgue.longitude).prefetch_related("evenements")
        message = render_to_string("orgues/carte_popup.html", context={"orgues": orgues,"edifice":orgue.edifice,"FULL_SITE_URL": settings.FULL_SITE_URL})
        return JsonResponse({"message": message}, safe=False)


class FacteurListJSLeaflet(View):
    """
    Cette vue est requêtée par Leaflet lors de l'affichage de la carte de France
    """

    def get(self, request, *args, **kwargs):
        data = Facteur.objects.filter(latitude_atelier__isnull=False).values("nom", "latitude_atelier", "longitude_atelier")
        return JsonResponse(list(data), safe=False)


class FacteurLonLatLeaflet(View):
    """
    Cette vue est requêtée par Leaflet lors de l'affichage de la carte de France
    """

    def get(self, request, *args, **kwargs):
        facteur_id = self.request.GET.get("facteur")
        data = Facteur.objects.filter(pk=facteur_id).values("nom", "latitude_atelier", "longitude_atelier")
        return JsonResponse(list(data), safe=False)


class FacteurListJSlonlat(ListView):
    """
    Liste dynamique utilisée pour filtrer les facteurs d'orgue dans les menus déroulants select2. Utilisée pour le filtre de la carte.
    documentation : https://select2.org/data-sources/ajax
    """
    model = Facteur
    paginate_by = 30

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get("search")
        queryset = queryset.filter(Q(latitude_atelier__isnull=False) & Q(longitude_atelier__isnull=False)).distinct()
        if query:
            queryset = queryset.filter(nom__icontains=query).distinct()
        return queryset

    def render_to_response(self, context, **response_kwargs):
        results = []
        more = context["page_obj"].number < context["paginator"].num_pages
        if context["object_list"]:
            results = [{"id": u.id, "text": u.nom} for u in context["object_list"]]
        return JsonResponse({"results": results, "pagination": {"more": more}})


class FacteursList(TemplateView):
    """
    Liste des orgues par facteurs.
    Cette page est vide au démarrage, la récupération des orgues se fait après coup en javascript via
    la vue EvenementfacteurJS.
    """
    template_name = "orgues/facteurs_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        queryset = Facteur.objects.all().order_by("nom")
        facteurs = []
        for facteur in queryset:
            facteurs.append({"nom":facteur.nom_dates(), "pk":facteur.pk})
        context["facteurs"] = facteurs
        return context


class OrgueDetail(DetailView):
    """
    Vue de détail (lecture seule) d'un orgue
    """
    model = Orgue
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_object(self, queryset=None):

        logger.info("{user};{method};detail/{get_full_path};200".format(user=self.request.user,
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
        context["contributions"] = self.get_contributions()
        context["orgue_url"] = self.request.build_absolute_uri(self.object.get_absolute_url())
        context["buffet_vide"] = self.object.buffet_vide
        return context

    def get_contributions(self):
        last = self.object.contributions.order_by("-date").first()
        return {
            "count": self.object.contributions.count(),
            "contributeurs": self.object.contributions.values_list("user").distinct().count(),
            "updated_by_user": last.user if last else "",
            "modified_date": last.date if last else "",
        }


class OrgueDetailExemple(View):
    """
    Redirige vers la fiche la mieux complétée du site
    """

    def get(self, request, *args, **kwargs):
        orgue = Orgue.objects.order_by('-completion').first()
        return redirect(orgue.get_absolute_url())


class OrgueQrcode(DetailView):
    """
    Affiche une page avec un QrCode
    """
    model = Orgue
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    template_name_suffix = '_qrcode'

    def get_object(self, queryset=None):
        orgue = Orgue.objects.filter(Q(slug=self.kwargs['slug']) | Q(codification=self.kwargs['slug'])).first()
        if not orgue:
            raise Http404
        return orgue

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["orgue_url"] = self.request.build_absolute_uri(self.object.get_short_url())
        return context


class ContributionOrgueMixin:
    """
    Ajout d'une contribution lors de la modification d'un orgue
    """
    contribution_description = 'Mise à jour'

    def save_contribution(self, orgue, description=None):
        detail = self.contribution_description if not description else description
        contribution = Contribution.objects.filter(orgue=orgue, date__date=date.today()).order_by('-date').first()
        if not contribution or contribution.user != self.request.user:
            contribution = Contribution(user=self.request.user, orgue=orgue, description=detail)
        if contribution.description.find(detail) < 0:
            contribution.description += ', ' + detail
        orgue.updated_by_user = self.request.user
        orgue.save()
        contribution.save()


class OrgueCreate(FabCreateView, ContributionOrgueMixin):
    """
    Création d'un nouvel orgue
    """
    model = Orgue
    permission_required = 'orgues.add_orgue'
    form_class = orgue_forms.OrgueCreateForm
    template_name = "orgues/orgue_create.html"

    def form_valid(self, form):
        print("designation : ", form.instance.designation)
        form.instance.updated_by_user = self.request.user
        commune, departement, code_departement, region, code_insee = co.geographie_administrative(form.instance.commune)
        edifice, type_edifice = co.reduire_edifice(form.instance.edifice, commune)
        codification = codif.codifier_instrument(code_insee, commune, edifice, type_edifice, form.instance.designation)
        form.instance.commune = commune
        form.instance.departement = departement
        form.instance.code_departement = code_departement
        form.instance.region = region
        form.instance.code_insee = code_insee
        form.instance.codification = codification
        if len(Orgue.objects.filter(codification=codification)) == 1:
            messages.error(self.request, 'Cette codification existe déjà !')
            return super().form_invalid(form)
        else:
            messages.success(self.request, "Nouvel orgue créé : {}".format(form.instance.codification))
            return super().form_valid(form)

    def get_success_url(self):
        success_url = reverse('orgues:orgue-detail', args=(self.object.slug,))
        return self.request.POST.get("next", success_url)


class OrgueUpdateMixin(FabUpdateView, ContributionOrgueMixin):
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
        self.save_contribution(form.instance)
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
        self.object.completion = self.object.calcul_completion()  # on recalcule l'avancement pour être sûr
        self.object.save(update_fields=['completion'])
        context["orgue"] = self.object
        return context


class OrgueDetailContributions(FabDetailView):
    """
    Vue de détail des contributeurs d'un orgue.
    """
    model = Orgue
    slug_field = 'uuid'
    slug_url_kwarg = 'orgue_uuid'
    permission_required = 'orgues.change_orgue'
    template_name = "orgues/orgue_detail_contributions.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["orgue"] = self.object
        return context


class OrgueUpdate(OrgueUpdateMixin, FabUpdateView):
    """
    Mise à jour des informations générales d'un orgue
    """
    form_class = orgue_forms.OrgueGeneralInfoForm
    success_message = 'Informations générales mises à jour !'
    contribution_description = 'Informations générales'

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
    contribution_description = 'Partie instrumentale'
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
    contribution_description = 'Composition'

    def get_object(self, queryset=None):
        object = super().get_object()
        object.resume_composition = object.calcul_resume_composition()
        object.save(update_fields=['resume_composition'])
        return object

    def get_success_url(self):
        success_url = reverse('orgues:orgue-update-composition', args=(self.object.uuid,))
        return self.request.POST.get("next", success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["claviers"] = self.object.claviers.all().prefetch_related("jeux")
        context["buffet_vide"] = self.object.buffet_vide
        return context


class OrgueUpdateBuffet(OrgueUpdateMixin):
    """
    Mise à jour du buffet d'un orgue
    """
    model = Orgue
    form_class = orgue_forms.OrgueBuffetForm
    template_name = "orgues/orgue_form_buffet.html"
    contribution_description = 'Buffet'
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
    contribution_description = 'Localisation'
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
            "pagination": {"more": results['estimatedTotalHits'] > TypeJeuListJS.paginate_by}
        }


class FacteurListJS(ListView):
    """
    Liste dynamique utilisée pour filtrer les facteurs d'orgue dans les menus déroulants select2.
    documentation : https://select2.org/data-sources/ajax
    """
    model = Facteur
    paginate_by = 30

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get("search")
        if query:
            queryset = queryset.filter(nom__icontains=query)
        return queryset

    def render_to_response(self, context, **response_kwargs):
        if self.request.GET.get("tous_facteurs") == "true":
            results = [{"id": -1, "text": "Tous les facteurs"}]
        else:
            results = []
        more = context["page_obj"].number < context["paginator"].num_pages
        if context["object_list"]:
            for u in context["object_list"]:
                results.append({"id": u.id, "text": u.nom_dates()})
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
        communes_francaises = codegeo.Communes()
        results = []
        for commune in communes_francaises:
            if commune.typecom == "COM" or commune.typecom == "ARM":
                intitule = commune.nom + ", " + commune.nomdepartement + ", " + commune.code_insee
                dictionnaire = {"id": commune.code_insee, "nom": commune.nom + ", " + commune.nomdepartement + ", " + commune.code_insee}
                if query:
                    if query in commune.nom.lower() or query in commune.nom:
                        results.append(dictionnaire)
                else:
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
        liste_designation = codif.DENOMINATION_ORGUE
        results = []
        results.append({"id": "", "nom": ""})
        for denomination in liste_designation:
            if query:
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


class EvenementCreate(FabCreateView, ContributionOrgueMixin):
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
        self.save_contribution(orgue, "Nouvel événement")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["orgue"] = Orgue.objects.get(uuid=self.kwargs["orgue_uuid"])
        return context

    def get_success_url(self):
        return reverse('orgues:evenement-list', args=(self.kwargs["orgue_uuid"],))


class EvenementUpdate(FabUpdateView, ContributionOrgueMixin):
    """
    Mise à jour d'un évenement
    """
    model = Evenement
    permission_required = "orgues.change_evenement"
    form_class = orgue_forms.EvenementForm
    success_message = "Evénement mis à jour, merci !"

    def form_valid(self, form):
        self.save_contribution(self.object.orgue, "Mise à jour d'un événement")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["orgue"] = self.object.orgue
        return context

    def get_success_url(self):
        return reverse('orgues:evenement-list', args=(self.object.orgue.uuid,))


class EvenementDelete(FabDeleteView, ContributionOrgueMixin):
    """
    Suppression d'un événement
    """
    model = Evenement
    permission_required = "orgues.delete_evenement"
    success_message = "Evenement supprimé, merci !"

    def delete(self, request, *args, **kwargs):
        self.save_contribution(self.get_object().orgue, "Suppression d'un événement")
        return super().delete(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["orgue"] = self.object.orgue
        return context

    def get_success_url(self):
        return reverse('orgues:evenement-list', args=(self.object.orgue.uuid,))


class EvenementfacteurJS(View):
    """
    Récupère tous les événements relatifs à un facteur d'orgue
    """

    def get(self, request, *args, **kwargs):
        facteur_id = int(self.request.GET.get("facteur"))
        facteur = get_object_or_404(Facteur, pk=facteur_id)
        evenements = Evenement.objects.filter(facteurs=facteur)
        results = {}
        for evenement in evenements:
            data = {"type":evenement.type, "date":evenement.dates, "orgue":OrgueResumeSerializer(evenement.orgue).data}
            date = evenement.annee
            if date in results.keys():
                results[date].append(data)
            else:
                results[date] = [data]
        return JsonResponse(results, safe=False)


class ClavierCreate(FabView, ContributionOrgueMixin):
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
            "orgue": orgue,
            "notes": None,
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
            self.save_contribution(orgue, "Ajout d'un clavier")
            return redirect('orgues:orgue-update-composition', orgue_uuid=orgue.uuid)
        else:
            context = {
                "jeux_formset": jeux_formset,
                "clavier_form": clavier_form,
                "orgue": orgue,
                "notes": None,
            }
            return render(request, "orgues/clavier_form.html", context)


class ClavierUpdate(FabUpdateView, ContributionOrgueMixin):
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
            "clavier": clavier,
            "notes": clavier.notes,
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
            self.save_contribution(clavier.orgue, "Mise à jour d'un clavier")
            messages.success(self.request, "Clavier mis à jour, merci !")
            return redirect('orgues:orgue-update-composition', orgue_uuid=clavier.orgue.uuid)
        else:
            context = {
                "jeux_formset": jeux_formset,
                "clavier_form": clavier_form,
                "orgue": clavier.orgue
            }
            return render(request, "orgues/clavier_form.html", context)


class ClavierDelete(FabDeleteView, ContributionOrgueMixin):
    """
    Suppression d'un clavier
    """
    model = Clavier
    permission_required = "orgues.delete_clavier"
    success_message = "Clavier supprimé, merci !"

    def delete(self, request, *args, **kwargs):
        self.save_contribution(self.get_object().orgue, "Suppression d'un Clavier")
        return super().delete(request, *args, **kwargs)

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
        if " " in nom:
            facteur, created = Facteur.objects.get_or_create(nom=nom)
            if created:
                facteur.updated_by_user = self.request.user
                facteur.save()
            return JsonResponse(
                {'success': "true", 'facteur': {'id': facteur.id, 'nom': facteur.nom}})
        else:
            return JsonResponse({'success': "false"})


class ProvenanceCreateJS(FabCreateViewJS):
    """
    Création d'une nouvelle Provenance.
    Vue appelée par du code javascript
    """
    model = Provenance
    permission_required = "orgues.add_evenement"
    fields = "__all__"

    def post(self, request, *args, **kwargs):
        edifice = request.POST.get("edifice")
        commune = request.POST.get("commune")
        osm_type = request.POST.get("type_osm")
        osm_id = request.POST.get("id_osm")
        commune, departement, code_departement, region, code_insee = co.geographie_administrative(commune)
        provenance, created = Provenance.objects.get_or_create(edifice=edifice, commune=commune, departement=departement, region=region, osm_type=osm_type, osm_id=osm_id)

        return JsonResponse(
            {'success': "true", 'provenance': {'id': provenance.id, 'nom': provenance.__str__()}})


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


class FichierCreate(FabCreateView, ContributionOrgueMixin):
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
        self.save_contribution(orgue, "Ajout d'un fichier")
        messages.success(self.request, "Fichier créé, merci !")
        return redirect('orgues:fichier-list', orgue_uuid=orgue.uuid)

    def get_context_data(self, **kwargs):
        orgue = get_object_or_404(Orgue, uuid=self.kwargs["orgue_uuid"])

        context = super().get_context_data()
        context["orgue"] = orgue
        context["object_list"] = Fichier.objects.filter(orgue=orgue)
        return context


class FichierDelete(FabDeleteView, ContributionOrgueMixin):
    """
    Suppression d'un fichier associé à un orgue
    """
    model = Fichier
    permission_required = "orgues.delete_fichier"
    success_message = "Fichier supprimé, merci !"

    def delete(self, request, *args, **kwargs):
        self.save_contribution(self.get_object().orgue, "Suppression d'un fichier")
        return super().delete(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('orgues:fichier-list', args=(self.object.orgue.uuid,))

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["orgue"] = self.object.orgue
        return context


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


class ImageCreate(FabView, ContributionOrgueMixin):
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
        self.save_contribution(orgue, "Ajout d'une image")
        return JsonResponse({'ok': True})


class ImageDelete(FabDeleteView, ContributionOrgueMixin):
    """
    Suppression d'une image
    """
    model = Image
    permission_required = "orgues.delete_image"
    success_message = "Image supprimée, merci !"

    def delete(self, request, *args, **kwargs):
        self.save_contribution(self.get_object().orgue, "Suppression d'une image")
        return super().delete(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('orgues:image-list', args=(self.object.orgue.uuid,))

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["orgue"] = self.object.orgue
        return context


class ImagePrincipaleUpdate(FabUpdateView, ContributionOrgueMixin):
    """
    Sélection et rognage de l'image principale d'un orgue dans le but de créer une vignette (utilise ajax et cropper.js)
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
            messages.warning(request, "Les images en noir & blanc ne peuvent pas devenir des vignettes")
            return redirect("orgues:image-list", orgue_uuid=image.orgue.uuid)
        return super().dispatch(request, *args, **kwargs)

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
        self.save_contribution(image.orgue, "Mise à jour de la vignette")

        # remove old thumbnail
        if old_path:
            os.remove(old_path)

        messages.success(self.request, self.success_message)
        return JsonResponse({})

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["orgue"] = self.object.orgue
        return context


class ImageUpdate(FabUpdateView, ContributionOrgueMixin):
    """
    Modification de la légende ou du crédit d'une image
    """
    model = Image
    fields = ['credit', 'legende']
    permission_required = "orgues.change_image"
    success_message = "Informations mises à jour, merci"

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.save_contribution(self.object.orgue, "Mise à jour d'une image")
        return super().post(request, *args, **kwargs)

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


class SourceCreate(FabCreateView, ContributionOrgueMixin):
    model = Source
    permission_required = "orgues.add_source"
    form_class = orgue_forms.SourceForm
    success_message = "Nouvelle source ajoutée, merci!"

    def form_valid(self, form):
        orgue = get_object_or_404(Orgue, uuid=self.kwargs['orgue_uuid'])
        form.instance.orgue = orgue
        self.save_contribution(orgue, "Ajout d'une source")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["orgue"] = Orgue.objects.get(uuid=self.kwargs["orgue_uuid"])
        return context

    def get_success_url(self):
        return reverse('orgues:source-list', args=(self.kwargs["orgue_uuid"],))


class SourceUpdate(FabUpdateView, ContributionOrgueMixin):
    model = Source
    permission_required = "orgues.change_source"
    form_class = orgue_forms.SourceForm
    success_message = "Source mise à jour, merci !"

    def form_valid(self, form):
        form.instance.updated_by_user = self.request.user
        self.save_contribution(self.object.orgue, "Mise à jour d'une source")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["orgue"] = self.object.orgue
        return context

    def get_success_url(self):
        return reverse('orgues:source-list', args=(self.object.orgue.uuid,))


class SourceDelete(FabDeleteView, ContributionOrgueMixin):
    model = Source
    permission_required = "orgues.delete_source"
    success_message = "Source supprimée, merci !"

    def delete(self, request, *args, **kwargs):
        self.save_contribution(self.get_object().orgue, "Suppression d'une source")
        return super().delete(request, *args, **kwargs)

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
            "references_inventaire_regions",
            "etat",
            "emplacement",
            "completion",
            "resume_composition",
            "diapason",
            "proprietaire",
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


class Stats(View):

    def get(self, request, *args, **kwargs):
        context = {}
        columns = ['departement', 'region', 'completion', 'etat', 'references_palissy']
        df = pd.DataFrame(Orgue.objects.values(*columns), columns=columns)

        # departements
        context["departement"] = self.calc(df, 'departement')
        # regions
        context["region"] = self.calc(df, 'region')

        # France
        completion = df.agg({'completion': ['count', 'mean'], 'references_palissy': ['count']}).round()
        etats = df.value_counts(subset='etat')
        context["France"] = self.normalize({**etats.to_dict(), 'count': completion.loc['count', 'completion'], 'avancement': completion.loc['mean', 'completion'],
                                            'mh': completion.loc['count', 'references_palissy']})

        return JsonResponse(context)

    def calc(self, df, type):
        completion = df.groupby(type, as_index=True).agg({'completion': ['count', 'mean'], 'references_palissy': ['count']}).round()
        completion.columns = ['count', 'avancement', 'mh']
        etats = df.groupby(by=[type, 'etat'], as_index=True).size().unstack(fill_value=0)
        res = pd.merge(completion, etats, left_index=True, right_index=True).to_dict(orient='index')
        return dict((k, self.normalize(v)) for k, v in res.items())

    def normalize(self, data):
        total = data['count'] - data['disparu'] or 0
        return {
            'total': total,
            'mh': data['mh'] or 0,
            'avancement': data['avancement'] or 0,
            'bons': round(100 * ((data['bon'] or 0) + (data['tres_bon'] or 0)) / total, 0),
            'altere': round(100 * (data['altere'] or 0) / total, 0),
            'degrade': round(100 * ((data['degrade'] or 0) + (data['restauration'] or 0)) / total, 0),
            'inconnu': round(
                100 * (total - (data['altere'] or 0) - (data['bon'] or 0) - (data['tres_bon'] or 0) - (data['degrade'] or 0) - (data['restauration'] or 0)) / total, 0),
            'disparu' : data['disparu'],
        }
