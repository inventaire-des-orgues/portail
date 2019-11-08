from django.contrib import admin

from .models import Orgue, Clavier, TypeClavier, TypeJeu, Jeu, Fichier


class ClavierInline(admin.StackedInline):
    model = Clavier
    extra = 0


from .models import Orgue, Clavier, TypeClavier, TypeJeu, Facteur



@admin.register(Fichier)
class FichierAdmin(admin.ModelAdmin):
    list_display = ('pk','file','description','orgue')

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


@admin.register(Orgue)
class OrgueAdmin(admin.ModelAdmin):
    list_display = ('designation',)
    inlines = [ClavierInline]
