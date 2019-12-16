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



# Faire un import de données : 


Remplacer le fichier `/var/www/portail/orgues/management/commands/data.csv` 

Puis lancer :

```
source /var/www/pythonenv/bin/activate
cd /var/www/portail
python manage.py import_data
```
