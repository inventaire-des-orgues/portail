# Installation :

Installer python 3.4+   
Installer les librairies listées dans le fichier `requirements.txt`.  
Créer un fichier `project/settings/dev.py` inspiré de `project/settings/dev.example.py` avec les settings de dev.

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

Certaines données sont mises en cache pour améliorer la perfomance des requêtes.  
Pour forcer le recalcul des "résumés clavier" il faut lancer la commande : 
```
python manage.py calcul_resume_composition
```  
Normalement le résumé clavier est recalculé automatiquement à chaque modification de la composition d'un orgue.


Pour rapatrier les facteurs d'un orgue stockés dans ses divers évenements, lancer : 
```
python manage.py calcul_facteurs
```
Normalement les facteurs d'un orgue sont recalculés automatiquement à chaque ajout/suppression d'un evenement. 

# Installation du moteur de recherche 

Suivre la documentation pour installer meilisearch : 

[https://docs.meilisearch.com/](https://docs.meilisearch.com/)

Configurer l'url de meilisearch dans `project/settings/dev.py`, normalement : 

```python
MEILISEARCH_URL = 'http://127.0.0.1:7700'
MEILISEARCH_KEY = ''
```

Puis lancer la tache de création de l'index : 

```python
python manage.py build_meilisearch_index
```

Un signal django récupère les modifications d'orgues faites directement via l'interface et met à jour l'index de recherche meilisearch.  
Ce signal ne récupère pas les modifications faites en ligne de commande, les modifications groupées via l'admin ou encore
les suppression d'orgues. 
Pour mettre à jour l'index de recherche après ce type de modification, il faut lancer la commande `build_meilisearch_index`.  
En production cette commande est lancée toutes les nuits pour s'assurer d'avoir un index toujours à jour. 


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
