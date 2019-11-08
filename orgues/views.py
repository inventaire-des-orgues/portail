from django.contrib import messages
from django.db.models import Count
from django.forms import modelformset_factory
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, TemplateView
from django.views.generic.base import View

from fabutils.mixins import FabCreateView, FabListView, FabDeleteView, FabUpdateView, FabView, FabCreateViewJS
from .forms import OrgueCreateForm, EvenementForm, ClavierForm, OrgueGeneralInfoForm, OrgueTuyauterieForm, JeuForm, \
    FichierForm, ImageForm, OrgueGeographieForm
from .models import Orgue, Clavier, Jeu, Evenement, Facteur, TypeClavier, TypeJeu, Fichier, Image


class OrgueList(ListView):
    """
    Listing des orgues
    """
    model = Orgue
    paginate_by = 30

    def get_queryset(self):
        queryset = super().get_queryset()
        commune = self.request.GET.get("commune")
        edifice = self.request.GET.get("edifice")
        if commune:
            queryset = queryset.filter(commune__icontains=commune)
        if edifice:
            queryset = queryset.filter(edifice__icontains=edifice)

        return queryset.order_by('-modified_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        return context


class OrgueCarte(TemplateView):
    """
    Cartographie des orgues (gérée par Leaflet)
    """
    template_name = "orgues/carte.html"


class OrgueListJS(View):
    """
    Cette vue est requêtée par Leaflet lors de l'affichage de la carte de France
    """
    def get(self, request, *args, **kwargs):
        data = Orgue.objects.filter(latitude__isnull=False).values("pk", "slug", "edifice", "latitude", "longitude")
        return JsonResponse(list(data), safe=False)


class OrgueDetail(DetailView):
    """
    Vue de détail (lecture seule) d'un orgue
    """
    model = Orgue
    slug_field = 'slug'
    slug_url_kwarg = 'slug'


class OrgueDetailExemple(View):
    """
    Redirige vers la fiche la mieux renseignée du site
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
    form_class = OrgueCreateForm
    success_url = reverse_lazy('orgues:orgue-list')
    success_message = 'Nouvel orgue créé'

    def form_valid(self, form):
        form.instance.updated_by_user = self.request.user
        return super().form_valid(form)


class OrgueUpdate(FabUpdateView):
    """
    Mise à jour des informations générales d'un orgue
    """
    model = Orgue
    slug_field = 'uuid'
    slug_url_kwarg = 'orgue_uuid'
    permission_required = 'orgues.change_orgue'
    form_class = OrgueGeneralInfoForm
    success_message = 'Informations générales mises à jour !'

    def form_valid(self, form):
        form.instance.updated_by_user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return self.object.get_update_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["orgue"] = self.object
        return context


class OrgueUpdateTuyauterie(OrgueUpdate):
    form_class = OrgueTuyauterieForm
    success_message = 'Tuyauterie mise à jour, merci !'
    template_name = "orgues/orgue_form_tuyauterie.html"

    def get_success_url(self):
        success_url = reverse('orgues:orgue-update-tuyauterie', args=(self.object.uuid,))
        return self.request.POST.get("next", success_url)


class OrgueUpdateGeographie(OrgueUpdate):
    form_class = OrgueGeographieForm
    success_message = 'Géographie mise à jour, merci !'
    template_name = "orgues/orgue_form_geographie.html"

    def get_success_url(self):
        success_url = reverse('orgues:orgue-update-geographie', args=(self.object.uuid,))
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
    Voir et éditer la liste des évenements d'un orgue
    """
    model = Evenement
    permission_required = "orgues.add_evenement"

    def get_queryset(self):
        self.orgue = get_object_or_404(Orgue, uuid=self.kwargs["orgue_uuid"])
        queryset = super().get_queryset()
        queryset = queryset.filter(orgue=self.orgue)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["orgue"] = self.orgue
        return context


class TypeJeuCreateJS(FabCreateViewJS):
    model = TypeJeu
    permission_required = "orgues.add_typejeu"
    fields = ["nom"]
    success_message = "Nouveau type de jeu créé, merci !"

    def post(self, request, *args, **kwargs):
        nom = request.POST.get("nom")
        hauteur = request.POST.get("hauteur")
        typejeu, created = TypeJeu.objects.get_or_create(nom=nom, hauteur=hauteur)
        return JsonResponse(
            {'message': self.success_message, 'facteur': {'id': typejeu.id, 'nom': str(typejeu)}})


class TypeJeuUpdate(FabUpdateView):
    model = TypeJeu
    permission_required = "orgues.change_typejeu"
    fields = ["nom"]
    success_message = "Type de jeu mis à jour, merci !"

    def get_success_url(self):
        return reverse('orgues:typejeu-update', args=(self.object.pk,))


class TypeJeuListJS(FabListView):
    """
    Liste dynamique utilisée pour filtrer les jeux d'orgues dans les menus déroulants select2.
    Les jeux sont triés par nombre d'apparitions dans les claviers (jeux les plus populaires apparaissent en premier)
    documentation : https://select2.org/data-sources/ajax
    """
    model = TypeJeu
    permission_required = 'orgues.add_orgue'
    paginate_by = 30

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.annotate(claviers_count=Count('jeux'))
        query = self.request.GET.get("q")
        if query:
            queryset = queryset.filter(nom__icontains=query)
        return queryset.order_by('-claviers_count')

    def render_to_response(self, context, **response_kwargs):
        results = []
        more = context["page_obj"].number < context["paginator"].num_pages
        if context["object_list"]:
            results = [{"id": t.id, "text": str(t)} for t in context["object_list"]]
        return JsonResponse({"results": results, "pagination": {"more": more}})


class FacteurListJS(FabListView):
    """
    Liste dynamique utilisée pour filtrer les facteurs d'orgue dans les menus déroulants select2.

    documentation : https://select2.org/data-sources/ajax
    """
    model = Facteur
    permission_required = 'orgues.add_orgue'
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


class EvenementCreate(FabCreateView):
    model = Evenement
    permission_required = "orgues.add_evenement"
    form_class = EvenementForm
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
    model = Evenement
    permission_required = "orgues.change_evenement"
    form_class = EvenementForm
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
    model = Clavier
    permission_required = "orgues.add_clavier"
    form_class = ClavierForm

    def get(self, request, *args, **kwargs):
        JeuFormset = modelformset_factory(Jeu, JeuForm, extra=10)
        orgue = get_object_or_404(Orgue, uuid=self.kwargs.get('orgue_uuid'))
        context = {
            "jeux_formset": JeuFormset(queryset=Jeu.objects.none()),
            "clavier_form": ClavierForm(),
            "orgue": orgue
        }
        return render(request, "orgues/clavier_form.html", context)

    def post(self, request, *args, **kwargs):
        orgue = get_object_or_404(Orgue, uuid=self.kwargs.get('orgue_uuid'))
        JeuFormset = modelformset_factory(Jeu, JeuForm)

        jeux_formset = JeuFormset(self.request.POST)
        clavier_form = ClavierForm(self.request.POST)
        if jeux_formset.is_valid() and clavier_form.is_valid():
            clavier_form.instance.orgue = orgue
            clavier = clavier_form.save()
            jeux = jeux_formset.save()
            for jeu in jeux:
                jeu.clavier = clavier
                jeu.save()

            messages.success(self.request, "Nouveau clavier ajouté, merci !")
            return redirect('orgues:orgue-update-tuyauterie', orgue_uuid=orgue.uuid)
        else:
            context = {
                "jeux_formset": jeux_formset,
                "clavier_form": clavier_form,
                "orgue": orgue
            }
            return render(request, "orgues/clavier_form.html", context)


class ClavierUpdate(FabUpdateView):
    model = Clavier
    permission_required = "orgues.change_clavier"
    form_class = ClavierForm

    def get(self, request, *args, **kwargs):
        clavier = get_object_or_404(Clavier, pk=kwargs["pk"])
        JeuFormset = modelformset_factory(Jeu, JeuForm, extra=3, can_delete=True)
        context = {
            "jeux_formset": JeuFormset(queryset=clavier.jeux.all()),
            "clavier_form": ClavierForm(instance=clavier),
            "orgue": clavier.orgue,
            "clavier": clavier
        }
        return render(request, "orgues/clavier_form.html", context)

    def post(self, request, *args, **kwargs):
        clavier = get_object_or_404(Clavier, pk=kwargs["pk"])
        JeuFormset = modelformset_factory(Jeu, JeuForm, extra=3, can_delete=True)
        jeux_formset = JeuFormset(self.request.POST, queryset=clavier.jeux.all())
        clavier_form = ClavierForm(self.request.POST, instance=clavier)
        if jeux_formset.is_valid() and clavier_form.is_valid():
            clavier = clavier_form.save()
            jeux = jeux_formset.save()
            for jeu in jeux:
                jeu.clavier = clavier
                jeu.save()
            messages.success(self.request, "Nouveau clavier ajouté, merci !")
            return redirect('orgues:orgue-update-tuyauterie', orgue_uuid=clavier.orgue.uuid)
        else:
            context = {
                "jeux_formset": jeux_formset,
                "clavier_form": clavier_form,
                "orgue": clavier.orgue
            }
            return render(request, "orgues/clavier_form.html", context)


class ClavierDelete(FabDeleteView):
    model = Clavier
    permission_required = "orgues.delete_clavier"
    success_message = "Clavier supprimé, merci !"

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["orgue"] = self.object.orgue
        return context

    def get_success_url(self):
        return reverse('orgues:orgue-update-tuyauterie', args=(self.object.orgue.uuid,))


class FacteurCreateJS(FabCreateViewJS):
    model = Facteur
    permission_required = "orgues.add_facteur"
    fields = "__all__"

    def post(self, request, *args, **kwargs):
        nom = request.POST.get("nom")
        facteur, created = Facteur.objects.get_or_create(nom=nom)
        return JsonResponse(
            {'message': self.success_message, 'facteur': {'id': facteur.id, 'nom': facteur.nom}})


class FichierList(FabListView):
    model = Fichier
    permission_required = "orgues.add_fichier"
    paginate_by = 50

    def get_queryset(self):
        self.orgue = get_object_or_404(Orgue, uuid=self.kwargs["orgue_uuid"])
        return Fichier.objects.filter(orgue=self.orgue)

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["orgue"] = self.orgue
        context["form"] = FichierForm()
        return context


class FichierCreate(FabCreateView):
    model = Fichier
    permission_required = "orgues.add_fichier"
    form_class = FichierForm
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
    model = Fichier
    permission_required = "orgues.delete_fichier"
    success_message = "Fichier supprimé, merci !"

    def get_success_url(self):
        return reverse('orgues:fichier-list', args=(self.object.orgue.uuid,))


class ImageList(FabListView):
    model = Image
    permission_required = "orgues.add_image"
    paginate_by = 50

    def get_queryset(self):
        self.orgue = get_object_or_404(Orgue, uuid=self.kwargs["orgue_uuid"])
        return Image.objects.filter(orgue=self.orgue)

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["orgue"] = self.orgue
        context["form"] = ImageForm()
        return context


class ImageCreate(FabCreateView):
    model = Image
    permission_required = "orgues.add_image"
    form_class = ImageForm
    template_name = "orgues/image_list.html"

    def form_valid(self, form):
        orgue = get_object_or_404(Orgue, uuid=self.kwargs["orgue_uuid"])
        image = form.save(commit=False)
        if not orgue.images.exists():
            image.is_principale = True
        image.orgue = orgue
        image.save()
        messages.success(self.request, "Image créée, merci !")
        return redirect('orgues:image-list', orgue_uuid=orgue.uuid)

    def get_context_data(self, **kwargs):
        orgue = get_object_or_404(Orgue, uuid=self.kwargs["orgue_uuid"])
        context = super().get_context_data()
        context["orgue"] = orgue
        context["object_list"] = Image.objects.filter(orgue=orgue)
        return context


class ImageDelete(FabDeleteView):
    model = Image
    permission_required = "orgues.delete_image"
    success_message = "Image supprimée, merci !"

    def get_success_url(self):
        return reverse('orgues:image-list', args=(self.object.orgue.uuid,))


class ImagePrincipale(FabView):
    permission_required = "orgues.change_image"

    def get(self, request, *args, **kwargs):
        image = get_object_or_404(Image, pk=kwargs["pk"])
        image.orgue.images.update(is_principale=False)
        image.is_principale = True
        image.save()
        messages.success(request, "Nouvelle image principale, merci !")
        return redirect('orgues:image-list', orgue_uuid=image.orgue.uuid)
