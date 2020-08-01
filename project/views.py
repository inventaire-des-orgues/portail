import datetime
import logging
import time

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.views.generic import FormView

import project.forms as project_forms
from project.settings import ADMIN_EMAILS

logger = logging.getLogger("fabaccess")


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

    def form_valid(self, form):

        if not verify_captcha(self.request):
            messages.error(self.request,"La vérification de sécurité anti-robot a échoué")
            return redirect('contact')

        last_email_sent = self.request.session.get("last_email_sent")

        # user can send 1 message per 5 minutes max
        if last_email_sent and (time.time() - last_email_sent) < 60 * 5:
            messages.warning(self.request,
                             "Vous avez déjà envoyé un message il n'y a pas longtemps, revenez dans 5 minutes")
            return redirect('orgues:orgue-list')
        # password is a honeypot field to prevent spam bots
        elif form.cleaned_data['password']:
            logger.warning("{user};{method};{get_full_path};400".format(user=self.request.user,
                                                                        method=self.request.method,
                                                                        get_full_path=self.request.get_full_path()))
            return HttpResponseForbidden()
        else:
            context = {
                'nom': form.cleaned_data['nom'],
                'prenom': form.cleaned_data['prenom'],
                'email': form.cleaned_data['email'],
                'sujet': form.cleaned_data['sujet'],
                'message': form.cleaned_data['message']
            }

            html_message = render_to_string('emails/contact_email.html', context)
            text_message = strip_tags(html_message)
            send_mail(subject='Contact inventaire des orgues',
                      message=text_message,
                      from_email=form.cleaned_data['email'],
                      recipient_list=ADMIN_EMAILS,
                      html_message=html_message)
            messages.success(self.request, 'Votre message a été envoyé')
            self.request.session["last_email_sent"] = time.time()

        return redirect('orgues:orgue-list')


def get_client_ip(request):
    """
    Method to extract IP adress from request
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def verify_captcha(request):
    """
    Method to check google reCaptcha
    More info : https://developers.google.com/recaptcha/docs/invisible
    """
    import requests
    captcha = request.POST.get('g-recaptcha-response')
    response = requests.post("https://www.google.com/recaptcha/api/siteverify", data={
        "secret": settings.CAPTCHA_SECRET,
        "response": captcha,
        "remoteip": get_client_ip(request)
    }).json()
    return response.get("success", False)
