import csv
from collections import deque

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, authenticate, login
from django.contrib.auth.forms import AdminPasswordChangeForm
from django.contrib.auth.models import Group
from django.shortcuts import redirect, render
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView

from accounts.forms import InscriptionForm
from fabutils.mixins import FabUpdateView, FabView
from project.views import verify_captcha

User = get_user_model()



class Inscription(CreateView):
    """
    Les utilisateurs peuvent s'inscrire eux-mêmes ici.
    Ils sont ajoutés par défaut dans le groupe des utilisateurs standards.
    """
    model = User
    success_message = "Votre compte a bien été créé, vous êtes connecté(e) !"
    success_url = reverse_lazy("orgues:orgue-list")
    form_class = InscriptionForm
    template_name = "accounts/inscription.html"

    def form_valid(self, form):
        if not verify_captcha(self.request):
            messages.error(self.request,"La vérification de sécurité anti-robot a échoué")
            return redirect('accounts:inscription')
        user = form.save()
        user.save()
        user.groups.add(Group.objects.get(name=settings.GROUP_STANDARD_USER))
        messages.success(self.request, self.success_message)
        next = self.request.GET.get("next", self.success_url)
        user = authenticate(username=user.email, password=form.cleaned_data["password1"])
        login(self.request, user)
        return redirect(next)


class UserUpdatePassword(FabUpdateView):
    """
    Admin only
    """
    model = User
    permission_required = "accounts.change_user"
    slug_field = "uuid"
    slug_url_kwarg = "user_uuid"
    success_message = "User password updated"
    form_class = AdminPasswordChangeForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = kwargs.pop('instance')
        return kwargs

    def get_success_url(self):
        return reverse('accounts:user-update', args=(self.object.uuid,))


class AccessLogs(FabView):
    permission_required = "accounts.add_user"

    def get(self, request, *args, **kwargs):
        rows = int(request.GET.get("rows",300))
        with open(settings.FABACCESSLOG_FILE) as f:
            reader = csv.reader(deque(f, maxlen=rows), delimiter=";")
            access_logs = reversed(list(reader))
        return render(request, "accounts/access_logs.html", {"access_logs": access_logs})
