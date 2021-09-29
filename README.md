# Installation

Installer python 3.4+
Installer les librairies listées dans le fichier `requirements.txt`.

```
pip install -r requirements.txt
```

Créer un fichier `project/settings/dev.py` inspiré de `project/settings/dev.example.py` avec les settings de dev.
## Créer la base de donnée 

Lancer les commandes suivantes :  
 
```shell script
python manage.py makemigrations
python manage.py migrate
python manage.py init_groups
python manage.py createsuperuser
```

## Installation du moteur de recherche 

Suivre la documentation pour installer meilisearch : 

[https://docs.meilisearch.com/](https://docs.meilisearch.com/)

Pour Windows, le script d'installation via curl ne fonctionnera pas, mais un binaire existe ici :
https://github.com/meilisearch/MeiliSearch/releases

Configurer l'url de meilisearch dans `project/settings/dev.py`, normalement : 

```python
MEILISEARCH_URL = 'http://127.0.0.1:7700'
MEILISEARCH_KEY = ''
```

Puis lancer la tache de création de l'index : 

```shell script
python manage.py build_meilisearch_index
```

Un signal django récupère les modifications d'orgues faites directement via l'interface et met à jour l'index de recherche meilisearch.
Ce signal ne récupère pas les modifications faites en ligne de commande, les modifications groupées via l'admin ou encore
les suppressions d'orgues. 
Pour mettre à jour l'index de recherche après ces types de modifications, il faut lancer la commande `build_meilisearch_index`.
En production cette commande est lancée toutes les nuits (à 2 h) pour garantir que l'index soit à jour. 

Si l'installation de meilisearch ne fonctionne pas, on peut utiliser un moteur de recherche dégradé en paramétrant : 

```python
MEILISEARCH_URL = False
```

## Insérer la config 

Pour récupérer les configs depuis le site inventaire des orgues (Facteurs, types de jeux, types de claviers et )
Téléchargez le fichier config.json depuis l'url du site : https://inventaire-des-orgues.fr/api/v1/config.json (il faut être connecter au site inventaire)
et lancer la commande suivante :

```shell script
python manage.py init_config --delete path/ver/config.json
```

## Importer des données

Il est possiblde de récupérer un fichier d'import pour les [orgues des pays de la loire](https://github.com/inventaire-des-orgues/paillasse/raw/master/paysdelaloire/paysdelaloire.json) : 

```shell script
python manage.py import_data --create path/ver/import.json
```

## Calculer les résumé de composition

Certaines données sont mises en cache pour améliorer la perfomance des requêtes.
Pour forcer le recalcul des "résumés clavier" il faut lancer la commande : 
```shell script
python manage.py calcul_resume_composition
```  
Normalement le résumé clavier est recalculé automatiquement à chaque modification de la composition d'un orgue.



l'option --delete permet de vider la base préalablement si nécessaire


## Démarrer le serveur 

Démarre un serveur qui sera automatiquement relancé lors de changement dans le code.

```shell script
python manage.py runserver
````

# Faire un import de données sur le serveur

Placer le fichier JSON d'importation quelque part sur le disque. (s'inspirer du format de `exemple_orgue-v3.json`) 
A noter : la colonne `codification` est utilisée comme pivot pour retrouver des orgues potentiellement déjà existants dans la base de données avant
de les mettre à jour.  

Lancer :

```shell script
source /var/www/pythonenv/bin/activate
cd /var/www/portail
python manage.py import_data chemin/vers/exemple_orgue-v3.json
```

Optionel : ajouter `--delete` pour supprimer les orgues existants avant l'importation

# Travailler directement sur la base de données

```python
source /var/www/pythonenv/bin/activate
cd /var/www/portail
python manage.py shell

from orgues.models import Orgue
Orgue.objects.all()
Orgue.objects.filter(departement="Ardennes")
```

Se référer à la [documentation Django](https://docs.djangoproject.com/fr/3.1/topics/db/queries/) pour des requêtes plus poussées, avec usage notamment des commandes comme :
`exclude()`, `get()` et des suffixes : `__startwith`, `__lte`, etc.
`update()` permet les mises à jour simultanées.
Exemple : corriger les noms erronés du champ ancienne_commune :

```python
Orgue.objects.filter(ancienne_commune="/").update(ancienne_commune="")
```

# Renouvellement des certificats

Via un fichier cron. Pour le voir :
```shell
sudo su
crontab -l
```

Commandes manuelles correspondantes si besoin de renouvellement manuel :
```shell
sudo service nginx stop
sudo certbot renew
sudo service nginx start
```

# Rétablir les permissions sur les fichiers

Lors de manipulations sur le serveur, il faut veiller à ne pas modifier les permissions des fichiers manipulés par Django.
Pour rétablir les bonnes permissions :
```python
sudo chown -R fabdev:www-data /var/www/portail/static/media
```

# Création d'un diagramme UML à partir du modèle de données Django

Installer si nécessaire django-extensions et pydotplus (toutefois ces deux modules sont dans `requirements.txt`, donc l'installation n'est normalement pas nécessaire).

Créer un fichier de graphe (.dot) à l'aide de :
```python
python manage.py graph_models orgues -a -g > orgue.dot
```

Puis générer un diagramme .svg (ou .png) en ligne :
https://dreampuf.github.io/GraphvizOnline

# Export CSV

Bien pratique pour travailler sur un tableur type OpenOffice ou Excel...
https://inventaire-des-orgues.fr/orgues/csv

# Api
[Voir la documentation de l'API](https://docs.inventaire-des-orgues.fr/api)

# Pense-bête Python

Pour installer un fichier Wheel depuis la console Python.
```python
import pip
from pip._internal import main as pipmain
pipmain(['install', "Chemin\\vers\\fichier.whl"])
```

# Scripts manage.py

## Localisation et correspondance avec OpenStreetMap

Lancer l’appariement sur tous les orgues qui n’ont pas déjà le champ id_osm rempli :
Attention, en raison du timer entre requêtes OpenStreetMap, la commande peut être très longue.
```python
nohup py manage.py appariement_osm all &
```

Associer à chaque orgue les id d’OSM trouvés dans appariement_osm :
```python
py manage.py import_organ_osm_id orgues/appariement/appariements_osm_all.json
```

Calculer le barycentre de chaque bâtiment. On recalcule pour tous les orgues, mais cela permet de corriger les orgues pour lesquels la position est erronée pour le moment :
```python
py manage.py calcul_barycenter_osm --calculall calculall
```

Associer à chaque orgue les positions en latitude longitude calculées dans calcul_barycenter_osm :
```python
py manage.py import_organ_lonlat coordonnees_osm.json --ecrase if
```

A condition qu’on ne lance pas appariement_osm et calcul_barycenter_osm le même jour, on sera en-dessous de la limite des 10000 requêtes par jour.

## Corrections de données

Supprimer en base de données les liens cassés pointant vers des images
```python
py manage.py remove_broken_images
```

Contrôle général de la qualité des données (casse, nom d'édifice non complétés, etc.) :
```python
py manage.py quality_check
```

Vérification de la présence du code INSEE dans chaque fiche :
```python
py manage.py verif_presence_insee
```

Corriger un attribut sur toutes les fiches :
```python
py manage.py corriger_attribut --replace designation "G.O." "grand orgue" 
```

Remplir toutes les valeurs None de l'attribut designation par une valeur par défaut :
```python
py manage.py corriger_designatio_none --replace "orgue"
```

Supprimer tous les doublons dans la liste des facteurs d'orgues :
```python
py manage.py delete_organ_builder_duplication
```

Renommer des codes de fiche à l'aide d'une liste CSV ancien_code;nouveau_code.
Attention, cette manipulation n'est pas anodine et il ne doit pas y avoir d'erreur de données, car en plus du changement de code les fichiers et images sont déplacés et le fichier PDF extrait du livre d'inventaire est renommé.
```python
py manage.py replace_codes
```

Déployer à partir d'un fichier archive TAR les PDF extraits des livres d'inventaire aux bons endroits sur le disque du serveur :
```python
py manage.py deployer_pdfs
```

