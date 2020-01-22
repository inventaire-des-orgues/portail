from django import forms

from .models import Orgue, Evenement, Clavier, Facteur, Jeu, Fichier, Image


class OrgueGeneralInfoForm(forms.ModelForm):
    class Meta:
        model = Orgue
        fields = [
            "designation",
            "edifice",
            "etat",
            "elevation",
            "is_polyphone",
            "association",
            "association_lien",
            "description",
            "console",
            "buffet",
            "commentaire_admin",

        ]

        widgets = {
            'buffet': forms.Textarea(attrs={'rows': 5, 'cols': 15}),
            'console': forms.Textarea(attrs={'rows': 5, 'cols': 15}),
            'description': forms.Textarea(attrs={'rows': 5, 'cols': 15}),
            'commentaire_admin': forms.Textarea(attrs={'rows': 2, 'cols': 15}),
        }


TUYAUTERIE_COLUMNS = {
    "transmission_notes": 4,
    "diapason": 4,
    "tirage_jeux": 4,
    "boite_expressive": 12,
    "sommiers": 12,
    "soufflerie": 12,
    "commentaire_tuyauterie": 12,
}


class OrgueGeographieForm(forms.ModelForm):
    class Meta:
        model = Orgue
        fields = [
            "commune",
            "code_insee",
            "ancienne_commune",
            "departement",
            "region",
            "latitude",
            "longitude"
        ]


class OrgueTuyauterieForm(forms.ModelForm):
    class Meta:
        model = Orgue

        fields = TUYAUTERIE_COLUMNS.keys()

        widgets = {
            'sommiers': forms.Textarea(attrs={'rows': 3, 'cols': 15}),
            'soufflerie': forms.Textarea(attrs={'rows': 3, 'cols': 15}),
            'commentaire_tuyauterie': forms.Textarea(attrs={'rows': 6, 'cols': 15}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['columns'] = TUYAUTERIE_COLUMNS[field]


class OrgueCreateForm(forms.ModelForm):
    class Meta:
        model = Orgue
        fields = [
            "designation",
            "edifice",
        ]


class ChoiceFieldNoValidation(forms.ChoiceField):
    def validate(self, value):
        pass


class EvenementForm(forms.ModelForm):
    class Meta:
        model = Evenement
        fields = [
            "annee",
            "type",
            "facteurs",
            "description",
        ]


class ClavierForm(forms.ModelForm):
    class Meta:
        model = Clavier
        fields = [
            "type",
            "facteur",
            "is_expressif",
        ]


class JeuForm(forms.ModelForm):
    class Meta:
        model = Jeu
        fields = ["type", "commentaire"]
        labels = {"type": "", "commentaire": ""}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['commentaire'].widget.attrs['placeholder'] = "Commentaire"


class FichierForm(forms.ModelForm):
    class Meta:
        model = Fichier
        fields = ["file", "description"]


class ImageForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ["image", "credit"]
