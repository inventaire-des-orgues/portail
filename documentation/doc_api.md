# Json public

Pour chaque orgue il est possible d'obtenir un Json en ajoutant `?format=json` à la fin de l'URL publique de la fiche ou
en cliquant sur le lien en bas de page. 
Cette fonctionnalité ne requiert pas d'authentification.

# API : 

Pour pouvoir obtenir des listes de fiches au format JSON il faut suivre les étapes suivantes : 


1. Dans l'admin : S'assurer que l'utilisateur qui veut accéder à l'API a son compte en mode "Statut équipe" (`is_staff=True`) 
   ![Extrait admin](./images/is_staff_true.png)
2. Dans l'admin : Créer un "Jeton" (token) pour l'utilisateur en question
    ![Extrait admin](./images/jeton_admin.png)
3. Utiliser le token pour faire des requêtes avec n'importe quel langage de programmation.   



### Exemples de requêtes en Python 

**Récupérer les 50 premiers orgues** : 

```python
import requests

headers={'Authorization': 'Token b6d113e8bc1b0f205893bca22e46681b4c2f210c'}
response = requests.get("https://inventaire-des-orgues.fr/api/v1/orgues/",headers=headers)
```


**Récupérer les 50 suivants** : 

```python
import requests

headers={'Authorization': 'Token b6d113e8bc1b0f205893bca22e46681b4c2f210c'}
response = requests.get("http://localhost:8000/api/v1/orgues/",params={"offset":"50"},headers=headers)
```


**Récupérer les orgues de la Marne** : 

```python
import requests

headers={'Authorization': 'Token b6d113e8bc1b0f205893bca22e46681b4c2f210c'}
response = requests.get("http://localhost:8000/api/v1/orgues/",params={"code_departement":51},headers=headers)
```




