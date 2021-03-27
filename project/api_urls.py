"""main API URL Configuration

The `urlpatterns` list routes URLs to API views.
Examples:
ListCreateAPI views
   1. Add an import:  from my_app.api import views as my_app_views
   2. Add a URL to urlpatterns:  url(r'^objects/$', my_app_views.MyObjectListCreateAPIView.as_view(), name='objects')
RetrieveUpdateDestroyAPI views
   1. Add an import:  from my_app.api import views as my_app_views
   2. Add a URL to urlpatterns:  url(r'^objects/(?P<uuid>[-\w]+)/$', my_app_views.MyObjectRetrieveUpdateDestroyAPIView.as_view(), name='objects')
"""
from django.urls import include, path
from rest_framework import routers
from orgues.api.views import OrgueViewSet, ConfigView


router = routers.DefaultRouter()
router.register(r'orgues', OrgueViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('config.json', ConfigView.as_view())
]
