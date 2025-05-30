from django.contrib import admin
from django.db.models import Count

from .models import Orgue, Clavier, TypeClavier, TypeJeu, Fichier, Image, Evenement, Facteur, Accessoire, Jeu, Contribution, Manufacture, FacteurManufacture, Provenance
from django.utils.html import format_html
from django.urls import reverse


class ClavierInline(admin.StackedInline):
    model = Clavier
    extra = 0


@admin.register(Fichier)
class FichierAdmin(admin.ModelAdmin):
    list_display = ('pk', 'file', 'description', 'orgue')
    search_fields = ('orgue__commune', 'orgue__edifice', 'orgue__designation', 'orgue__codification', 'orgue__emplacement', 'orgue__departement',)


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ('pk', 'orgue', 'credit', 'is_principale','user')
    list_editable = ('credit',)
    search_fields = ('user__first_name','user__last_name','user__email','orgue__codification')


@admin.register(Facteur)
class FacteurAdmin(admin.ModelAdmin):
    list_display = ('nom', 'latitude_atelier', 'longitude_atelier', 'updated_by_user')
    list_editable = ('latitude_atelier', 'longitude_atelier',)
    search_fields = ('nom',)


@admin.register(FacteurManufacture)
class FacteurManufactureAdmin(admin.ModelAdmin):
    list_display = ('pk', 'annee_debut', 'annee_fin')
    list_editable = ('annee_debut', 'annee_fin')
    search_fields = ('facteur',)


@admin.register(Manufacture)
class ManufactureAdmin(admin.ModelAdmin):
    list_display = ('nom',)
    search_fields = ('nom',)


@admin.register(TypeJeu)
class TypeJeuAdmin(admin.ModelAdmin):
    list_display = ('nom_hauteur', 'nom', 'hauteur', 'created_date', 'updated_by_user')
    search_fields = ('nom', 'updated_by_user__first_name', 'updated_by_user__last_name')

    def nom_hauteur(self, _typejeu):
        return _typejeu


@admin.register(Jeu)
class JeuAdmin(admin.ModelAdmin):
    list_display = ('type', 'nom_du_jeu', 'hauteur_du_jeu', 'dans_orgue')
    search_fields = ('type__nom',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('type', 'clavier', 'clavier__orgue')

    def nom_du_jeu(self, _jeu):
        return _jeu.type.nom

    def hauteur_du_jeu(self, _jeu):
        return _jeu.type.hauteur

    def dans_orgue(self, _jeu):
        orgue = _jeu.clavier.orgue
        return format_html(
            '<a href="{}" target="_blank">{}</a>'.format(reverse('orgues:orgue-update', args=(orgue.uuid,)), orgue))


@admin.register(TypeClavier)
class TypeClavierAdmin(admin.ModelAdmin):
    list_display = ('nom',)


@admin.register(Evenement)
class EvenementAdmin(admin.ModelAdmin):
    list_display = (
        'annee',
        'type',
        'resume',
    )
    list_editable = ['resume']


@admin.register(Accessoire)
class AccessoireAdmin(admin.ModelAdmin):
    list_display = ('nom',)


@admin.register(Orgue)
class OrgueAdmin(admin.ModelAdmin):
    fields = ['codification', 'code_insee', 'commune', 'edifice', 'region', 'departement', 'code_departement',
              'designation', 'emplacement', 'references_palissy', 'references_inventaire_regions', 'commentaire_admin']
    list_display = ('codification', 'designation', 'commune', 'edifice','updated_by_user','modified_date','contributions_compte','images_compte', 'departement', 'commentaire_admin', 'created_date')
    ordering = ('-modified_date',)
    inlines = [ClavierInline]
    list_per_page = 20
    search_fields = ('commune', 'edifice', 'designation', 'codification', 'emplacement', 'departement',
                     'updated_by_user__first_name', 'updated_by_user__last_name', 'updated_by_user__email')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(contributions_compte=Count('contributions', distinct=True),images_compte=Count('images', distinct=True))

    def contributions_compte(self, obj):
        return format_html("<a href='/admin/orgues/contribution/?q={}'>{}</a>".format(obj.codification,obj.contributions_compte))

    def images_compte(self, obj):
        return format_html("<a href='/admin/orgues/image/?q={}'>{}</a>".format(obj.codification,obj.images_compte))

    images_compte.admin_order_field = 'images_compte'
    contributions_compte.admin_order_field = 'contributions_compte'


@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    list_display = ('date','user','orgue','description')
    search_fields = ('orgue__commune', 'orgue__edifice', 'orgue__designation', 'orgue__codification', 'orgue__emplacement', 'orgue__departement',
                     'user__first_name', 'user__last_name', 'user__email')
    list_filter = ('date',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user','orgue')
