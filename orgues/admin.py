from django.contrib import admin

from .models import Orgue, Clavier, TypeClavier, TypeJeu, Fichier, Image, Evenement, Facteur, Accessoire, Jeu
from django.utils.html import format_html
from django.urls import reverse


class ClavierInline(admin.StackedInline):
    model = Clavier
    extra = 0


@admin.register(Fichier)
class FichierAdmin(admin.ModelAdmin):
    list_display = ('pk', 'file', 'description', 'orgue')


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ('pk', 'orgue', 'credit', 'is_principale')
    list_editable = ('credit',)


@admin.register(Facteur)
class FacteurAdmin(admin.ModelAdmin):
    list_display = ('nom', 'latitude_atelier', 'longitude_atelier',)
    list_editable = ('latitude_atelier', 'longitude_atelier',)
    search_fields = ('nom',)


@admin.register(TypeJeu)
class TypeJeuAdmin(admin.ModelAdmin):
    list_display = ('nom_hauteur', 'nom', 'hauteur', 'created_date', 'updated_by_user')
    list_filter = ('nom', 'nom', 'hauteur', 'created_date', 'updated_by_user')
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
              'designation', 'references_palissy']
    list_display = ('codification', 'designation', 'commune', 'edifice',
                    'departement', 'commentaire_admin', 'updated_by_user', 'modified_date')
    inlines = [ClavierInline]
    list_filter = ('updated_by_user',)
    search_fields = ('commune', 'edifice', 'codification', 'departement')
