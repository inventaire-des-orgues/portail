from django import forms
from django.core.mail import send_mail, BadHeaderError
from project.settings.base import ADMIN_EMAILS


class ContactForm(forms.Form):
    nom = forms.CharField(max_length=100)
    prenom = forms.CharField(max_length=100, label="Prénom")
    email = forms.EmailField()
    sujet = forms.CharField(max_length=100)
    message = forms.CharField(widget=forms.Textarea)

    def send_email(self):
        nom = self.cleaned_data['nom']
        prenom = self.cleaned_data['prenom']
        email = self.cleaned_data['email']
        sujet = self.cleaned_data['sujet']
        message = self.cleaned_data['message']
        email_message = f"message de {prenom} {nom} : \n{message}"
        try:
            send_mail(subject=sujet,
                      message=email_message,
                      from_email=email,
                      recipient_list=ADMIN_EMAILS,
                      fail_silently=False)
        except BadHeaderError:
            pass






