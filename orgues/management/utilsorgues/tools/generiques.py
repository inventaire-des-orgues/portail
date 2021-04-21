import unicodedata

LISTE_MINUSCULE = ["le", "la", "les", "de", "des", "du", "in"]
LISTE_MAJUSCULE = ["ND"]


def supprimer_accents_1(chaine):
    # s1 = unicode(s, 'utf-8')
    s1 = chaine
    s2 = unicodedata.normalize('NFD', s1).encode('ascii', 'ignore')
    s3 = str(s2)
    return s3


def supprimer_accents(chaine):
    """
    Supprime les accents et cédilles.
    """
    accents = {'E': ['É', 'È', 'Ê', 'Ë'],
               'A': ['À', 'Á', 'Â', 'Ã'],
               'I': ['Î', 'Ï'],
               'U': ['Ù', 'Ü', 'Û'],
               'O': ['Ô', 'Ö'],
               'C': ['Ç'],
               'e': ['é', 'è', 'ê', 'ë'],
               'a': ['à', 'á', 'â', 'ã'],
               'i': ['î', 'ï'],
               'u': ['ù', 'ü', 'û'],
               'o': ['ô', 'ö'],
               'c': ['ç']
               }
    for (char, accented_chars) in accents.items():
        for accented_char in accented_chars:
            chaine = chaine.replace(accented_char, char)
    return chaine


def supprimer_accents_sur_majuscules(chaine):
    """
    Supprime les accents.
    """
    accents = {'E': ['É', 'È', 'Ê', 'Ë'],
               'A': ['À', 'Á', 'Â', 'Ã'],
               'I': ['Î', 'Ï'],
               'U': ['Ù', 'Ü', 'Û'],
               'O': ['Ô', 'Ö'],
               'C': ['Ç']
               }
    for (char, accented_chars) in accents.items():
        for accented_char in accented_chars:
            chaine = chaine.replace(accented_char, char)
    return chaine


def supprimer_article(terme):
    """
    Suppression de l'article défini en début de terme.
    :param terme: un nom d'édifice
    :return: nom d'édifice corrigé
    """
    if terme[:2] in ["L'", "l'", "L’", "l’"]:
        terme_modifie = terme[2:]
    elif terme[:3] in ["Le ", "le ", "La ", "la ", "Le-", "le-", "La-", "la-"]:
        terme_modifie = terme[3:]
    elif terme[:4] in ['Les ', 'les ', 'Les-', 'les-']:
        terme_modifie = terme[4:]
    elif terme[:2] in ["D'", "d'", "D’", "d’"]:
        terme_modifie = terme[2:]
    elif terme[:3] in ["De ", "de ", "De-", "de-", "Du ", "du "]:
        terme_modifie = terme[3:]
    elif terme[:4] in ["Des ", "des ", "Des-", "des-"]:
        terme_modifie = terme[4:]
    else:
        terme_modifie = terme
    return terme_modifie


def corriger_casse(chaine):
    """
    https://georezo.net/forum/viewtopic.php?pid=256458
    :param chaine:
    :return:
    """
    # Tous les mots de la chaine doivent etre en minuscule
    chaine = chaine.lower()

    # Separation de la chaine par les espaces
    liste_mot = chaine.split(' ')
    for i in range(0, len(liste_mot)):
        mot = liste_mot[i]

        # Si le mot est dans la liste des minuscules
        if mot in LISTE_MINUSCULE:
            liste_mot[i] = mot.lower()

        # Sinon, si le mot contient une apostrophe
        elif "'" in mot:
            # Si le mot est en debut de nom
            # alors la lettre precedant l apostrophe doit etre en majuscule
            if i == 0:
                liste_mot[i] = mot.title()
            # Sinon la lettre precedant l apostrophe est en minuscule,
            # les autres en majuscule
            else:
                mot_split = mot.split("'")
                # Condition permettant de verifier qu il n y avait bien
                # qu une apostrophe
                if len(mot_split) == 2:
                    mot_split[0] = mot_split[0].lower()
                    # L utilisation de title() ici permet de gerer
                    # les mots post-apostrophe avec un tiret
                    mot_split[1] = mot_split[1].title()
                    liste_mot[i] = "'".join(mot_split)

        # Sinon, si le mot contient un tiret
        elif '-' in mot:
            liste_mot[i] = mot.title()

        # Sinon, si le mot contient un element de la liste upper
        # il est mis en majuscule, sinon seulement sa premiere lettre
        else:
            # Si le mot passe en majuscule debute par un element de la liste,
            # le mot est mis en majuscule
            up = False
            for el in LISTE_MAJUSCULE:
                if mot.upper().startswith(el):
                    liste_mot[i] = mot.upper()
                    up = True
            # Enfin, si le mot est passe a travers toutes les conditions
            # sa premiere lettre est mise en majuscule
            if not up:
                liste_mot[i] = mot.capitalize()
    return ' '.join(liste_mot)


def upper_sans_accent(chaine):
    s1 = supprimer_accents(chaine)
    s2 = corriger_casse(s1)
    return s2


def createpaireencode(string):
    alphabet = 'a b c d e f g h i j k l m n o p q r s t u v w x y z'
    vecalphabet = alphabet.split(' ')
    pairevec = vecalphabet + [(x + y) for x in vecalphabet for y in vecalphabet]
    d = []
    for i in pairevec:
        d = d + [string.count(i)]
    return string, d


"""
Algo de comparaison non exacte de chaînes :

Il y a le Sacro saint Levenshtein, son dérivé Damereau-Levenshtein, Jaro-Winkler, une version évoluée.

D'un autre côté tu trouvera par exemple TF-IDF

Sinon tu as des algos comme Soundex et Metaphone qui se basent sur la sonorité des mots et les encodant au préalable.
C'est plus rapide que les autres mais l'efficacité est moindre.

Tu peux faire une recherche sur google des expressions :
"recherche approximative", "comparaison approximative", "approximative matching", "fuzzy matching"...

***

https://towardsdatascience.com/getting-started-with-elasticsearch-in-python-c3598e718380
"""

if __name__ == '__main__':
    print(supprimer_accents('Un bel été !'))
    print(upper_sans_accent('Un bel été !'))
    print(createpaireencode("saint denis"))
    print(createpaireencode("St denis"))

    import stringdist

    distance = stringdist.levenshtein('test', 'testing')
    print(distance)
