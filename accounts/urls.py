import accounts.views as aviews
from django.urls import path

app_name = 'accounts'
urlpatterns = [
    path('inscription/', aviews.Inscription.as_view(), name='inscription'),
    path('mon-compte/', aviews.MonCompte.as_view(), name='mon-compte'),
    path('logs/', aviews.AccessLogs.as_view(), name='access-logs'),
]
