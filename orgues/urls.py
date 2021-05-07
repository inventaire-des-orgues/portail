from django.urls import path

import orgues.views as v

app_name = 'orgues'
urlpatterns = [
    path('orgues/', v.OrgueList.as_view(), name='orgue-list'),
    path('orgues/csv/', v.OrgueExport.as_view(), name='orgue-csv'),
    path('recherche/', v.OrgueSearch.as_view(), name='orgue-search'),
    path('liste.json', v.OrgueListJS.as_view(), name='orgue-list-js'),
    path('listeFacteur.json', v.FacteurListJSLeaflet.as_view(), name='facteur-list-js-leaflet'),
    path('etats.json', v.OrgueEtatsJS.as_view(), name='orgue-etats-js'),
    path('etats2.json', v.OrgueEtatsJSDep.as_view(), name='orgue-etats-js2'),
    path('references_palissy.json', v.OrgueHistJS.as_view(), name='orgue-hist-js'),
    path('references_palissyDep.json', v.OrgueHistJSDep.as_view(), name='orgue-histDep-js'),
    path('carte/', v.OrgueCarte.as_view(), name='orgue-carte'),
    path('detail/<slug:slug>/', v.OrgueDetail.as_view(), name='orgue-detail'),
    path('exemple/', v.OrgueDetailExemple.as_view(), name='orgue-detail-exemple'),
    path('conseils/', v.ConseilsFicheView.as_view(),name='orgue-fiche-conseils'),
    path('orgues/filtre', v.OrgueFiltreJS.as_view(), name='orgue-filtre-js'),

    # Administration
    path('creation/', v.OrgueCreate.as_view(), name='orgue-create'),
    path('edition/<uuid:orgue_uuid>/', v.OrgueUpdate.as_view(), name='orgue-update'),
    path('edition/instrumentale/<uuid:orgue_uuid>/', v.OrgueUpdateInstrumentale.as_view(), name='orgue-update-instrumentale'),
    path('edition/composition/<uuid:orgue_uuid>/', v.OrgueUpdateComposition.as_view(), name='orgue-update-composition'),
    path('edition/avancement/<uuid:orgue_uuid>/', v.OrgueDetailAvancement.as_view(), name='orgue-detail-avancement'),
    path('edition/contributions/<uuid:orgue_uuid>/', v.OrgueDetailContributions.as_view(), name='orgue-detail-contributions'),
    path('edition/buffet/<uuid:orgue_uuid>/', v.OrgueUpdateBuffet.as_view(), name='orgue-update-buffet'),
    path('edition/localisation/<uuid:orgue_uuid>/', v.OrgueUpdateLocalisation.as_view(), name='orgue-update-localisation'),
    path('suppression/<uuid:orgue_uuid>/', v.OrgueDelete.as_view(), name='orgue-delete'),
    path('dashboard/', v.Dashboard.as_view(), name='dashboard'),

    # Tableau de bord
    #path('orgues/dashboard', v.OrgueDashboard.as_view(), name='orgue-dashboard'),

    # Evenements
    path('evenements/<uuid:orgue_uuid>/', v.EvenementList.as_view(), name='evenement-list'),
    path('evenement/edition/<int:pk>/', v.EvenementUpdate.as_view(), name='evenement-update'),
    path('evenement/creation/<uuid:orgue_uuid>/', v.EvenementCreate.as_view(), name='evenement-create'),
    path('evenement/suppression/<int:pk>/', v.EvenementDelete.as_view(), name='evenement-delete'),

    # claviers
    path('clavier/creation/<uuid:orgue_uuid>/', v.ClavierCreate.as_view(), name='clavier-create'),
    path('clavier/edition/<int:pk>/', v.ClavierUpdate.as_view(), name='clavier-update'),
    path('clavier/suppression/<int:pk>/', v.ClavierDelete.as_view(), name='clavier-delete'),

    # facteurs
    path('js/facteurs/', v.FacteurListJS.as_view(), name='facteur-list-js'),
    path('js/facteurs/creation/', v.FacteurCreateJS.as_view(), name='facteur-create-js'),
    path('js/facteurs/lonlat/', v.FacteurListJSlonlat.as_view(), name='facteur-list-js-lonlat'),
    path('js/facteurs/lonlatLeaflet/', v.FacteurLonLatLeaflet.as_view(), name='facteur-js-lonlat'),

    # types jeux
    path('types_jeux/creation/', v.TypeJeuCreateJS.as_view(), name='typejeu-create-js'),
    path('types_jeux/edition/<int:pk>/', v.TypeJeuUpdate.as_view(), name='typejeu-update'),
    path('js/liste/jeux/', v.TypeJeuListJS.as_view(), name='typejeu-list-js'),

    # fichiers
    path('fichiers/<uuid:orgue_uuid>/', v.FichierList.as_view(), name='fichier-list'),
    path('fichiers/creation/<uuid:orgue_uuid>/', v.FichierCreate.as_view(), name='fichier-create'),
    path('fichiers/suppression/<int:pk>/', v.FichierDelete.as_view(), name='fichier-delete'),

    # images
    path('images/<uuid:orgue_uuid>/', v.ImageList.as_view(), name='image-list'),
    path('images/creation/<uuid:orgue_uuid>/', v.ImageCreate.as_view(), name='image-create'),
    path('images/update/<int:pk>/', v.ImageUpdate.as_view(), name='image-update'),
    path('images/suppression/<int:pk>/', v.ImageDelete.as_view(), name='image-delete'),
    path('images/principale/<int:pk>/', v.ImagePrincipaleUpdate.as_view(), name='image-principale'),

    # Sources
    path('sources/<uuid:orgue_uuid>/', v.SourceList.as_view(), name='source-list'),
    path('source/edition/<int:pk>/', v.SourceUpdate.as_view(), name='source-update'),
    path('source/creation/<uuid:orgue_uuid>/', v.SourceCreate.as_view(), name='source-create'),
    path('source/suppression/<int:pk>/', v.SourceDelete.as_view(), name='source-delete'),

    path('searchlog/', v.SearchLogView.as_view(), name='search-log'),

    #Création d'orgue
    path('js/communes/', v.CommuneListJS.as_view(), name='commune-list-js'),
    path('js/designation/', v.DesignationListJS.as_view(), name='designation-list-js')
]
