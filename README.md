# Installation :

Installer python 3.4+   
Installer les librairies listées dans le fichier `requirements.txt`.  

```
pip install -r requirements.txt
```
Lancer les commandes suivantes :  
 
```
python manage.py makemigrations
python manage.py migrate
python manage.py init_groups
python manage.py init_config
python manage.py import_data
python manage.py createsuperuser
python manage.py runserver
```



# Faire un import de données sur le serveur : 


Placer le fichier JSON d'importation quelque part sur le disque. (s'inspirer du format de `exemple_orgue-v3.json`) 
A noter : la colonne `codification` est utilisée comme pivot pour retrouver des orgues potentiellement déjà existants dans la base de données avant
de les mettre à jour.  

Lancer :

```
source /var/www/pythonenv/bin/activate
cd /var/www/portail
python manage.py import_data chemin/vers/exemple_orgue-v3.json
```

Optionel : ajouter `--delete` pour supprimer les orgues existants avant l'importation


# Api : 
[voir la doc](documentation/doc_api.md)

