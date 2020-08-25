# Structure de la fiche descriptive d'un orgue de l'inventaire

#TODO : reprendre fiche type des orgue d'IdF.

## Définition des notes
Une seule notation doit être retenue dans l'inventaire des orgues pour la description des notes : les octaves sont numérotées de 1 à 6.
C1, C#1, D1, D#1...

## Diapason
Hauteur en Hertz du A2 joué par le prestant 4.

Valeur_par_defaut = Néant

## Classement
On ne distingue que Inscription et Classement, comme objets evenement.
Le champ TICO de Palissy sera mis dans le commentaire de l'évenement.
De même pour les autres champs issus de la mise en correspondance entre l'inventaire et la base Palissy.

## Orgues polyphones de Louis Debierre
is_polyphone [bool] spécifie si l'orgue un polyphone de la manufacture Debierre.

Valeur_par_defaut = False

## Sommiers
Champ texte libre. [string]

Valeur_par_defaut = Néant

## Soufflerie
Champ texte libre. [string]

Valeur_par_defaut = Néant

## Transmission des notes
transmission_notes est indiqué pour tout l'instrument, et non par clavier.
Lorsque les claviers disposent d'un autre mode de transmission que celle généralement ou originellement utilisée pour l'instrument (ex: pédalier à transmission électrique) seront précisés dans les commentaires du clavier.

    "Mécanique",
    "Mécanique suspendue",
    "Mécanique Barker",
    "Pneumatique haute pression",
    "Pneumatique basse pression",
    "Electrique",


## Transmission des registres
tirage_jeux est indiqué pour tout l'instrument

## Propriété de l'orgue
Le propriétaire de l'orgue (qui n'est pas nécessairement le même que l'édifice).
Le plus souvent, il s'agit de la commune pour des instruments datant d'avant 1905 (de l'Etat pour les orgues de cathédrales), et d'association cultuelle (généralement paroisse) pour les orgues d'après 1905 ou de congrégation.
Bien sûr, il existe plusieurs exceptions : par exemple, les orgues des cathédrales de la petite couronne parisienne, n'appartiennent pas à l'Etat, mais l'orgue de la basilique royale de Saint-Denis si.

Valeur_par_defaut= commune

    "commune",
    "Etat",
    "association culturelle",
    "diocèse",
    "paroisse"

## Etat de fonctionnement
Il s'agit d'un avis à date de mise à jour de la fiche descriptive. Nécessairement pour partie subjectif, il est rapporté à l'utilisation possible de l'instrument. Les défauts courants et réversible d'un orgue (cornement occasionnel par exemple) ne rentrent pas en compte dans l'appréciation. L'état de fonctionnement ne décrit pas l'état du buffet ou des boiseries dès lors qu'il n'altère pas le jeu.

Valeur_par_defaut = Néant

    "Très bon ou bon : tout à fait jouable",
    "Altéré : difficilement jouable",
    "Dégradé ou en ruine : injouable"

## emplacement
emplacement

Valeur_par_defaut = Néant

    "en tribune",
    "au sol""

## Emplacement dans l'édifice
A ce stade, aucun attribut n'est prévu pour préciser la position de l'orgue dans l'édifice.
Dans le cas de plusieurs instruments au sein d'un même édifice, l'attribut emplacement et les coordonnées géographiques permettent de positionner et distinguer précisément l'instrument.

## Jeux

Cf. (https://fr.wikipedia.org/wiki/Liste_des_jeux_d%27orgue)

Valeur_par_defaut = "Bourdon 8"

Les registres sont énumérés selon un ordre harmonique (hauteur du jeu).
On suit la disposition suivante :
- Fonds
- Mixtures
- Cornet
- Batterie d'anches
- Anches de détail

La hauteur est indiquée par convention en pieds, en chiffres arabes, sans précision de l'unité.
La nombre de rangs des fournitures, plein-jeux, cornet, etc. est indiqué en chiffre romains, sans précision du terme "rangs" (ni "rgs").

## Accessoires

Valeur_par_defaut = Néant

Les accessoires peuvent être :
- accouplement :
    - on peut préciser s'il s'agit d'un accouplement classique à l'unisson, à l'octave basse ou bien à l'octave aigüe.
    - On peut aussi préciser le clavier accouplé et le clavier jouant avec l'accouplement.
- trémolo : on peut préciser le clavier
- appel : appel d'un jeu ou de plusieurs jeux, généralement les jeux d'anches ou mixtures.
- renvoi : renvoi d'un jeu ou de plusieurs jeux, généralement les jeux d'anches ou mixtures. N'est complété que si une cuillère spécifique effectue le renvoi. Si la cuillère de l'appel permet le renvoi lorsqu'elle est relâchée, il n'y pas lieu d'indiquer un renvoi.

    "accouplement",
    "trémolo",
    "appel",
    "renvoi"

## Evènements
Les types d'évènement possibles sont les suivants :

Valeur_par_defaut = Néant

    "Construction",
    "Reconstruction",
    "Destruction",
    "Restauration",
    "Déménagement",
    "Relevage",
    "Disparition",
    "Dégâts",
    "Classement aux monuments historiques",
    "Inscription aux monuments historiques"

- Relavage : simple opération de conservation de l'instrument, menée à intervalles réguliers.
- Reconstruction : des éléments nouveaux sont ajoutés en grand nombre, la structure de l'instrument est modifiée.
- Restauration : opération d'importance, à caractère patrimonial : il s'agit de revenir à un état antérieur de l'instrument.
- Destruction : dégâts sur l'ensemble de l'instrument, rendu totalement inutilisable.
- Disparition : distincte de destruction, car l'orgue a pu disparaître suit à un déménagement, ou être stocké dans un endroit inconnu.

Chaque évènement est décrit par :
- l'année de l'évènement [int]
- le type d'évènement [objet]
- la liste des facteurs ayant contribué à l'évènement [liste]
- une description libre de l'évènement [string sans limite de taille]

*Question ouverte* Ne faut-il pas ajouter un résumé de l'évènement, pour la chronologie notamment ?

## Buffet
Champs libre [string sans limite de taille] pour la description du buffet et de son état.

## Console
console [string sans limite de taille] Décrit la position de la console.

Valeur_par_defaut = Néant

Les type les plus courants sont :
- en fenêtre
- séparée, organiste tourné vers l'orgue
- séparée, organiste dos à l'orgue

Dans le cas d'une console mobile ou en fenêtre sur le côté ou l'arrière de l'instrument, on précisera la disposition.
Idem dans le cas d'une seconde console.
