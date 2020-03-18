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


Remplacer le fichier `/var/www/portail/orgues/management/commands/data.csv`.  
A noter : la colonne `Codification_instrument` est utilisée comme pivot pour retrouver des orgues potentiellement déjà existants dans la base de données avant
de les mettre à jour.  

Lancer :

```
source /var/www/pythonenv/bin/activate
cd /var/www/portail
python manage.py import_data
```


# Api : 
[voir la doc](documentation/doc_api.md)

