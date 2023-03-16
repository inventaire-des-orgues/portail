from django import forms

from fabutils.forms import Select2Single, Select2Multiple
from .models import Orgue, Evenement, Clavier, Facteur, Jeu, Fichier, Image, Source


class OrgueGeneralInfoForm(forms.ModelForm):
    class Meta:
        model = Orgue
        fields = [
            "edifice",
            "designation",
            "qualification_palissy",
            "emplacement",
            "etat",
            "proprietaire",
            "references_palissy",
            "references_inventaire_regions",
            "lien_inventaire_regions",
            "entretien",
            "organisme",
            "lien_reference",
            "resume",
            "commentaire_admin",

        ]

        widgets = {
            'resume': forms.Textarea(attrs={'rows': 5, 'cols': 15}),
            'commentaire_admin': forms.Textarea(attrs={'rows': 2, 'cols': 15}),
            'entretien': Select2Multiple
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        if not self.request.user.has_perm('orgues.edition_avancee'):
            self.fields['qualification_palissy'].disabled = True
            self.fields['qualification_palissy'].help_text = 'Cette information est figée'
            self.fields['edifice'].disabled = True
            self.fields['edifice'].help_text = 'Cette information est figée'
            self.fields['references_palissy'].disabled = True
            self.fields['references_palissy'].help_text = 'Cette information est figée'
            self.fields['references_inventaire_regions'].disabled = True
            self.fields['references_inventaire_regions'].help_text = 'Cette information est figée'


INSTRUMENTALE_COLUMNS = {
    "transmission_notes": 6,
    "transmission_commentaire": 6,
    "tirage_jeux": 6,
    "tirage_commentaire": 6,
    "temperament": 12,
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
    "departement": 4,
    "region": 5,
    "osm_type": 6,
    "osm_id": 6,
    "latitude": 6,
    "longitude": 6,
}


class OrgueLocalisationForm(forms.ModelForm):
    class Meta:
        model = Orgue
        fields = LOCALISATION_COLUMNS.keys()

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        if not self.request.user.has_perm('orgues.edition_avancee'):
            for field in ['commune', 'ancienne_commune', 'code_insee', 'departement', 'region']:
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
            "commune",
            "edifice",
            "designation",
            "osm_type",
            "osm_id"
        ]
        widgets = {
            'commune': forms.Select(),
            'designation': forms.Select()
        }


class ChoiceFieldNoValidation(forms.ChoiceField):
    def validate(self, value):
        pass


class EvenementForm(forms.ModelForm):
    class Meta:
        model = Evenement
        fields = [
            "annee",
            "annee_fin",
            "circa",
            "type",
            "facteurs",
            "resume",
        ]

        widgets = {
            "facteurs": Select2Multiple
        }


class ClavierForm(forms.ModelForm):
    class Meta:
        model = Clavier
        fields = [
            "type",
            "is_expressif",
            "etendue",
            "commentaire",
        ]


class JeuForm(forms.ModelForm):
    class Meta:
        model = Jeu
        fields = ["type", "configuration", "commentaire"]
        labels = {"type": "", "configuration": "", "commentaire": ""}

        widgets = {
            "type": Select2Single
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['commentaire'].widget.attrs['placeholder'] = "Commentaire"


class FichierForm(forms.ModelForm):
    class Meta:
        model = Fichier
        fields = ["file", "description"]


class SourceForm(forms.ModelForm):
    class Meta:
        model = Source
        fields = [
            "description",
            "type",
            "lien",
        ]


class OrgueCarteForm(forms.Form):
    MIN_JEUX = 0
    MAX_JEUX = 140
    jeux = forms.CharField(required=False)
    etats = forms.MultipleChoiceField(choices=[(etat[1], etat[1]) for etat in Orgue.CHOIX_ETAT], required=False, label="Par état de fonctionnement :")
    facteurs = forms.ModelMultipleChoiceField(queryset=Facteur.objects.all(), required=False, label="Par facteur d'orgue : ", widget=Select2Multiple)
    monument = forms.BooleanField(label="Uniquement monuments historiques (orange)", required=False)

    def clean_jeux(self):
        jeux = self.cleaned_data['jeux']
        if jeux:
            result = [int(jeu) for jeu in jeux.split(';')]
            if result != [self.MIN_JEUX, self.MAX_JEUX]:
                return result
        return
