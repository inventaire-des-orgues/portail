from django.contrib import admin

from .models import Orgue, Clavier, TypeClavier, TypeJeu, Jeu, Fichier, Image, Evenement


class ClavierInline(admin.StackedInline):
    model = Clavier
    extra = 0


from .models import Orgue, Clavier, TypeClavier, TypeJeu, Facteur



@admin.register(Fichier)
class FichierAdmin(admin.ModelAdmin):
    list_display = ('pk','file','description','orgue')


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ('pk','orgue','credit','is_principale')
    list_editable = ('credit',)

@admin.register(Jeu)
class JeuAdmin(admin.ModelAdmin):
    list_display = ('type','clavier','commentaire')

@admin.register(Facteur)
class FacteurAdmin(admin.ModelAdmin):
    list_display = ('nom',)


@admin.register(TypeJeu)
class TypeJeuAdmin(admin.ModelAdmin):
    list_display = ('nom',)


@admin.register(Clavier)
class ClavierAdmin(admin.ModelAdmin):
    list_display = ('orgue',)


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

@admin.register(Orgue)
class OrgueAdmin(admin.ModelAdmin):
    list_display = ('codification','designation','commune','edifice','departement','commentaire_admin','updated_by_user','modified_date')
    inlines = [ClavierInline]
    list_filter = ('updated_by_user',)
    search_fields = ('commune','edifice','codification', 'departement')
