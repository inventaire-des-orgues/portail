from django.contrib import admin

from .models import Orgue, Clavier, TypeClavier, TypeJeu, Fichier, Image, Evenement, Facteur, Accessoire, Jeu


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
    list_display = ('nom',)


@admin.register(TypeJeu)
class TypeJeuAdmin(admin.ModelAdmin):
    list_display = ('nom', 'hauteur')
    search_fields = ('nom',)


@admin.register(Jeu)
class JeuAdmin(admin.ModelAdmin):
    list_display = ('type', 'type_hauteur', 'clavier_orgue')
    search_fields = ('type',)

    def type_hauteur(self, _jeu):
        return _jeu.type.hauteur

    def clavier_orgue(self, _jeu):
        return _jeu.clavier.orgue


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
    fields = ['codification', 'code_insee', 'commune', 'edifice', 'region', 'departement', 'code_departement']
    list_display = ('codification', 'designation', 'commune', 'edifice',
                    'departement', 'commentaire_admin', 'updated_by_user', 'modified_date')
    inlines = [ClavierInline]
    list_filter = ('updated_by_user',)
    search_fields = ('commune', 'edifice', 'codification', 'departement')
