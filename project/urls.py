"""inventaire_des_orgues URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import include
from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView


from project.views import accueil, ContactView

urlpatterns = [
    path('', include('django.contrib.auth.urls')),
    path('admin/', admin.site.urls),
    path('', accueil, name='accueil'),
    path('contact/', ContactView.as_view(), name='contact'),
    path('', include('orgues.urls')),
    path('api-auth/', include('rest_framework.urls')),
    path('api/v1/', include(('project.api_urls', 'project'), namespace='api')),

    path('lexique/', TemplateView.as_view(template_name='lexique.html'), name='lexique'),
    path('error/403/', TemplateView.as_view(template_name='403.html'), name='403'),
    path('error/404/', TemplateView.as_view(template_name='404.html'), name='404'),
    path('error/500/', TemplateView.as_view(template_name='500.html'), name='500'),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt'), name='robots'),

]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
