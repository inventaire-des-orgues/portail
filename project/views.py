from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import BadHeaderError
from django.shortcuts import render
from django.urls import reverse_lazy, reverse
from django.views.generic import FormView
from django.contrib import messages

import project.forms as project_forms
from project.settings import ADMIN_EMAILS
from django.template.loader import render_to_string
from django.utils.html import strip_tags


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
        # password is a honeypot field to prevent spam bots
        if not form.cleaned_data['password']:
            context = {
                'nom': form.cleaned_data['nom'],
                'prenom': form.cleaned_data['prenom'],
                'email': form.cleaned_data['email'],
                'sujet': form.cleaned_data['sujet'],
                'message': form.cleaned_data['message']
            }

            html_message = render_to_string('emails/contact_email.html', context)
            text_message = strip_tags(html_message)
            try:
                send_mail(subject='Contact inventaire des orgues',
                          message=text_message,
                          from_email="info@love.engie.com",
                          recipient_list=[ADMIN_EMAILS],
                          html_message=html_message)
                messages.success(self.request, 'Votre message a été envoyé')
            except BadHeaderError:
                messages.error(self.request, "une erreur est survenue lors de l'envoi de votre message")
        else:
            print('spam bot detected')
        return super().form_valid(form)
