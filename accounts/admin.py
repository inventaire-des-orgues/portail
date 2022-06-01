from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Permission
from django.db.models import Max
from django.utils import formats
from django.utils.html import format_html

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
    list_display = ('first_name', 'last_name', 'email', 'last_login','derniere_contribution')
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

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(derniere_contribution=Max('contributions__date'))

    def derniere_contribution(self, obj):
        if not obj.derniere_contribution:
            return

        return format_html("<a href='/admin/orgues/contribution/?q={}'>{}</a>".format(obj.get_full_name(),
                                                                                      formats.date_format(obj.derniere_contribution, "j F Y H:i")))

    derniere_contribution.admin_order_field = 'derniere_contribution'


admin.site.register(User, FabUserAdmin)

admin.site.site_header = 'inventaire_des_orgues Admin'
