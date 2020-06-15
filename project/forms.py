from django import forms


class ContactForm(forms.Form):
    nom = forms.CharField(max_length=100)
    prenom = forms.CharField(max_length=100, label="Prénom")
    email = forms.EmailField()
    sujet = forms.CharField(max_length=100)
    message = forms.CharField(widget=forms.Textarea, max_length=1000)
    # password is a honeypot field to detect spam bots.
    password = forms.CharField(
        widget=forms.TextInput(attrs={'name': 'a_password',
                                      'style': 'display:none; !important',
                                      'tabindex': '-1',
                                      'autocomplete': 'off'}),
        required=False)
