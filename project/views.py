from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def accueil(request):
    """
    Page d'accueil
    """
    context = {}
    return render(request, "accueil.html", context)
