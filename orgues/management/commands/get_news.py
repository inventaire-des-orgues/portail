from django.core.management.base import BaseCommand
import json
import requests
from django.conf import settings
from django.core.mail import get_connection, EmailMessage
import re
import datetime

class Command(BaseCommand):
    """
    Scrappe sur Internet les titres des journaux locaux concernant les orgues datant d'il y a moins d'une semaine 
    """
    help = ''


    def handle(self, *args, **options):


        
        url = "https://www.googleapis.com/customsearch/v1?"

        list_journaux = {
            "Est Republicain":"www.estrepublicain.fr/*",
            "Ouest France":"www.ouest-france.fr/*",
            "Le Dauphine libere":"www.ledauphine.com/*",
            "Le Progres":"www.leprogres.fr/*",
            "Dernieres nouvelles d'Alsace":"www.dna.fr/*",
            "L'Alsace":"www.lalsace.fr/*",
            "Le Journal de Saone-et-Loire":"www.lejsl.com/*",
            "Le Bien public":"www.bienpublic.com/*",
            "Vosges matin":"www.vosgesmatin.fr/*",
            "Journal de la Haute-Marne":"www.jhm.fr/*",
            "Le Republicain lorrain":"www.republicain-lorrain.fr/*",
            "La Voix du nord":"www.lavoixdunord.fr/*",
            "L'Union":"www.lunion.fr/*",
            "L'Ardennais":"www.lardennais.fr/*",
            "Courrier picard":"www.courrier-picard.fr/*",
            "L'Est eclair":"www.lest-eclair.fr/*",
            "Nord littoral":"www.nordlittoral.fr/*",
            "Liberation Champagne":"www.liberation-champagne.fr/*",
            "La Montagne":"www.lamontagne.fr/*",
            "Le Populaire du Centre":"www.lepopulaire.fr/*",
            "La Republique du Centre":"www.larep.fr/*",
            "Le Berry republicain":"www.leberry.fr/*",
            "L'Yonne republicaine":"www.lyonne.fr/*",
            "L'echo republicain":"www.lechorepublicain.fr/*",
            "Le Journal du Centre":"www.lejdc.fr/*",
            "L'eveil de la Haute-Loire":"www.leveil.fr/*",
            "La Depeche du Midi":"www.ladepeche.fr/*",
            "Midi libre":"www.midilibre.fr/*", 
            "L'Independant":"www.lindependant.fr/*",
            "Centre Presse":"www.centre-presse.fr/*",
            "La Nouvelle Republique des Pyrenees":"www.nrpyrenees.fr/*",
            "Le Petit Bleu d'Agen":"www.petitbleu.fr/*",
            "Sud Ouest":"www.sudouest.fr/*",
            "Charente libre":"www.charentelibre.fr/*",
            "La Republique des Pyrenees":"www.larepubliquedespyrenees.fr/*",
            "Dordogne libre":"www.dordognelibre.fr/*",
            "Le Parisien":"www.leparisien.fr/*",
            "Le Telegramme":"www.letelegramme.fr/*",
            "La Nouvelle Republique":"www.lanouvellerepublique.fr/*",
            "La Provence":"www.laprovence.com/*",
            "Corse matin":"www.corsematin.com/*",
            "Nice matin":"www.nicematin.com/*",
            "Var-Matin":"www.varmatin.com/*",
            "Paris-Normandie":"www.paris-normandie.fr/*", 
            "Journal la marseillaise":"www.lamarseillaise.fr/*"
        }

        string = ""

        today = datetime.datetime.now()

        date_expression_reguliere = "((19\d\d|20\d\d)[-/](0[1-9]|1[0-2])[-/](0[1-9]|[12]\d|3[01]))"

        for journal in list_journaux.keys():
            stringRequest = "+".join(journal.split(" ")) + "+orgue"
            params = {"key":settings.GOOGLE_API_KEY, "q":stringRequest, "cx":settings.GOOGLE_API_CX, "dateRestrict":"m1"}

            response = requests.get(url, params=params)
            resultats = json.loads(response.text)

            string += "\n" + journal + "\n"


            

            if "items" in resultats.keys():
                for resultat in resultats["items"]:
                    if not "concert" in resultat["title"].lower() and not "bort-les-orgues" in resultat["title"].lower() and not "bort-les-orgues" in resultat["link"].lower():
                        if "orgue" in resultat["title"].lower() or "orgue" in resultat["link"].lower():
                            date_article = re.findall(date_expression_reguliere, resultat["link"])

                            if len(date_article) >= 1:
                                if "/" in date_article[0][0]:
                                    date_splitted = date_article[0][0].split("/")
                                else:
                                    date_splitted = date_article[0][0].split("-")
                                date_article = datetime.datetime(int(date_splitted[0]), int(date_splitted[1]), int(date_splitted[2]))
                                difference = today - date_article
                                if difference.days < 8:
                                    string += "{}, {}\n".format(resultat["title"], resultat["link"])
                            else:
                                string += "{}, {}\n".format(resultat["title"], resultat["link"])


        with get_connection(  
            host=settings.EMAIL_HOST, 
            port=settings.EMAIL_PORT,  
            username=settings.EMAIL_HOST_USER, 
            password=settings.EMAIL_HOST_PASSWORD, 
            use_tls=settings.EMAIL_USE_TLS  
            ) as connection:  
           subject = "Nouvelles du monde de l'orgue"  
           email_from = settings.DEFAULT_FROM_EMAIL
           recipient_list = settings.NEWS_EMAILS  
           message = string  
           EmailMessage(subject, message, email_from, recipient_list, connection=connection).send()
            
           