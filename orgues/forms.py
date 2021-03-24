from django import forms

from .models import Orgue, Evenement, Clavier, Facteur, Jeu, Fichier, Image, Source


class OrgueGeneralInfoForm(forms.ModelForm):
    class Meta:
        model = Orgue
        fields = [
            "edifice",
            "designation",
            "emplacement",
            "etat",
            "proprietaire",
            "references_palissy",
            "entretien",
            "organisme",
            "lien_reference",
            "resume",
            "commentaire_admin",

        ]

        widgets = {
            'resume': forms.Textarea(attrs={'rows': 5, 'cols': 15}),
            'commentaire_admin': forms.Textarea(attrs={'rows': 2, 'cols': 15}),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        if not self.request.user.has_perm('orgues.edition_avancee'):
            self.fields['edifice'].disabled = True
            self.fields['edifice'].help_text = 'Cette information est figée'

INSTRUMENTALE_COLUMNS = {
    "transmission_notes": 6,
    "transmission_commentaire": 6,
    "tirage_jeux": 6,
    "tirage_commentaire": 6,
    "temperament":12,
    "diapason": 4,
    "sommiers": 12,
    "soufflerie": 12,
    "commentaire_tuyauterie": 12,
}

LOCALISATION_COLUMNS = {
    "commune": 12,
    "code_insee": 12,
    "ancienne_commune": 12,
    "adresse": 12,
    "code_departement": 3,
    "departement": 4,
    "region": 5,
    "latitude": 6,
    "longitude": 6,
    "osm_type": 6,
    "osm_id": 6,
}


class OrgueLocalisationForm(forms.ModelForm):
    class Meta:
        model = Orgue
        fields = LOCALISATION_COLUMNS.keys()

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        if not self.request.user.has_perm('orgues.edition_avancee'):
            for field in ['commune','code_insee','code_departement','departement','region']:
                self.fields[field].disabled = True
                self.fields[field].help_text = 'Cette information est figée'


class OrgueInstrumentaleForm(forms.ModelForm):
    class Meta:
        model = Orgue

        fields = INSTRUMENTALE_COLUMNS.keys()

        widgets = {
            'sommiers': forms.Textarea(attrs={'rows': 3, 'cols': 15}),
            'soufflerie': forms.Textarea(attrs={'rows': 3, 'cols': 15}),
            'commentaire_tuyauterie': forms.Textarea(attrs={'rows': 6, 'cols': 15}),
        }

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     for field in self.fields:
    #         self.fields[field].widget.attrs['columns'] = INSTRUMENTALE_COLUMNS[field]


class OrgueCompositionForm(forms.ModelForm):
    class Meta:
        model = Orgue

        fields = ['accessoires']


class OrgueBuffetForm(forms.ModelForm):
    class Meta:
        model = Orgue
        fields = ['buffet', 'console']


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
            "resume",
        ]


class ClavierForm(forms.ModelForm):
    class Meta:
        model = Clavier
        fields = [
            "type",
            "etendue",
            "is_expressif",
        ]


class JeuForm(forms.ModelForm):
    class Meta:
        model = Jeu
        fields = ["type", "configuration", "commentaire"]
        labels = {"type": "", "configuration": "", "commentaire": ""}

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
        fields = ["image", "legende", "credit"]


class SourceForm(forms.ModelForm):
    class Meta:
        model = Source
        fields = [
            "description",
            "type",
            "lien",
        ]
