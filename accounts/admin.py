from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Permission


User = get_user_model()


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('name', 'codename')


class UserCreateForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name',)


class FabUserAdmin(UserAdmin):
    add_form = UserCreateForm
    list_display = ('first_name', 'last_name', 'email', 'last_login',)
    prepopulated_fields = {'username': ('first_name', 'last_name',)}

    fieldsets = (
        (None, {'fields': ('username', 'first_name', 'last_name', 'email', 'password')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('first_name', 'last_name', 'email', 'username', 'password1', 'password2',),
        }),
    )


admin.site.register(User, FabUserAdmin)

admin.site.site_header = 'inventaire_des_orgues Admin'
