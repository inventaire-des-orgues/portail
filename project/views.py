from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import reverse_lazy, reverse
from django.views.generic import FormView

import project.forms as project_forms
from django.contrib import messages


@login_required
def accueil(request):
    """
    Page d'accueil
    """
    context = {}
    return render(request, "accueil.html", context)


class ContactView(FormView):
    template_name = "contact.html"
    form_class = project_forms.ContactForm
    success_url = reverse_lazy('orgues:orgue-list')

    def form_valid(self, form):
        form.send_email()
        messages.success(self.request, 'Votre message a été envoyé')
        return super().form_valid(form)
