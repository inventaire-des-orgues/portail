"""
Fonctions utilitaires pour corriger ou simplifier (dégénéréscence) des noms d'édifices.
"""
import re
import logging
import csv

import orgues.utilsorgues.tools.generiques as gen
import orgues.utilsorgues.code_geographique as codegeo

loggerCorrecteurorgues = logging.getLogger('correcteurogues')

listeMinuscule = ["le", "la", "les", "de", "des", "du", "en", "et", "aux", "ès"]
listeMajuscule = ["ND"]
CHOIX_DEPARTEMENT = (
        ('01', 'Ain'),
        ('02', 'Aisne'),
        ('03', 'Allier'),
        ('04', 'Alpes-de-Haute-Provence'),
        ('05', 'Hautes-Alpes'),
        ('06', 'Alpes-Maritimes'),
        ('07', 'Ardèche'),
        ('08', 'Ardennes'),
        ('09', 'Ariège'),
        ('10', 'Aube'),
        ('11', 'Aude'),
        ('12', 'Aveyron'),
        ('13', 'Bouches-du-Rhône'),
        ('14', 'Calvados'),
        ('15', 'Cantal'),
        ('16', 'Charente'),
        ('17', 'Charente-Maritime'),
        ('18', 'Cher'),
        ('19', 'Corrèze'),
        ('2A', 'Corse-du-Sud'),
        ('2B', 'Haute-Corse'),
        ("21", "Côte-d'Or"),
        ("22", "Côtes-d'Armor"),
        ('23', 'Creuse'),
        ('24', 'Dordogne'),
        ('25', 'Doubs'),
        ('26', 'Drôme'),
        ('27', 'Eure'),
        ('28', 'Eure-et-Loir'),
        ('29', 'Finistère'),
        ('30', 'Gard'),
        ('31', 'Haute-Garonne'),
        ('32', 'Gers'),
        ('33', 'Gironde'),
        ('34', 'Hérault'),
        ('35', 'Ille-et-Vilaine'),
        ('36', 'Indre'),
        ('37', 'Indre-et-Loire'),
        ('38', 'Isère'),
        ('39', 'Jura'),
        ('40', 'Landes'),
        ('41', 'Loir-et-Cher'),
        ('42', 'Loire'),
        ('43', 'Haute-Loire'),
        ('44', 'Loire-Atlantique'),
        ('45', 'Loiret'),
        ('46', 'Lot'),
        ('47', 'Lot-et-Garonne'),
        ('48', 'Lozère'),
        ('49', 'Maine-et-Loire'),
        ('50', 'Manche'),
        ('51', 'Marne'),
        ('52', 'Haute-Marne'),
        ('53', 'Mayenne'),
        ('54', 'Meurthe-et-Moselle'),
        ('55', 'Meuse'),
        ('56', 'Morbihan'),
        ('57', 'Moselle'),
        ('58', 'Nièvre'),
        ('59', 'Nord'),
        ('60', 'Oise'),
        ('61', 'Orne'),
        ('62', 'Pas-de-Calais'),
        ('63', 'Puy-de-Dôme'),
        ('64', 'Pyrénées-Atlantiques'),
        ('65', 'Hautes-Pyrénées'),
        ('66', 'Pyrénées-Orientales'),
        ('67', 'Bas-Rhin'),
        ('68', 'Haut-Rhin'),
        ('69', 'Rhône'),
        ('70', 'Haute-Saône'),
        ('71', 'Saône-et-Loire'),
        ('72', 'Sarthe'),
        ('73', 'Savoie'),
        ('74', 'Haute-Savoie'),
        ('75', 'Paris'),
        ('76', 'Seine-Maritime'),
        ('77', 'Seine-et-Marne'),
        ('78', 'Yvelines'),
        ('79', 'Deux-Sèvres'),
        ('80', 'Somme'),
        ('81', 'Tarn'),
        ('82', 'Tarn-et-Garonne'),
        ('83', 'Var'),
        ('84', 'Vaucluse'),
        ('85', 'Vendée'),
        ('86', 'Vienne'),
        ('87', 'Haute-Vienne'),
        ('88', 'Vosges'),
        ('89', 'Yonne'),
        ('90', 'Territoire de Belfort'),
        ('91', 'Essonne'),
        ('92', 'Hauts-de-Seine'),
        ('93', 'Seine-Saint-Denis'),
        ('94', 'Val-de-Marne'),
        ("95", "Val-d'Oise"),
        ('971', 'Guadeloupe'),
        ('972', 'Martinique'),
        ('976', 'Mayotte'),
        ('973', 'Guyane'),
        ('974', 'La Réunion'),
        ('975', 'Saint-Pierre-et-Miquelon'),
        ('988', 'Nouvelle-Calédonie'),
    )


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
    new_liste_mot = list()
    for mot in liste_mot:
        liste_mini_mots = mot.split('-')
        new_liste_mini_mots = list()
        for mini_mot in liste_mini_mots:
            if mini_mot not in listeMinuscule:
                mini_mot = mini_mot.title()
            # Mise en miniscule des mots avec apostrophe si non au début du nom.
            if "'" in mini_mot or "’" in mini_mot:
                if (mini_mot[1] == "'" or mini_mot[1] == "’") and mini_mot != liste_mini_mots[0]:
                    mini_mot = mini_mot[0].lower() + mini_mot[1:]
            new_liste_mini_mots.append(mini_mot)
        mot = "-".join(new_liste_mini_mots)
        new_liste_mot.append(mot)
    new_chaine = " ".join(new_liste_mot)
    return new_chaine


def detecter_type_edifice(chaine):
    """
    Détecte si l'édifice est d'un type standard.
    Transforme le nom d'édifice pour en extraire le type.
    Par exemple "église Saint-Georges" devient "Saint-Georges"
    :param chaine: dénomination de l'édifice
    :return: (dénomination standardisée, type edifice)
    """
    # Attention, l'ordre de la liste compte : mettre d'abord église catholique, ensuite église...
    types_edifice = ['église catholique',
                     'temple protestant',
                     'temple réformé',
                     'ancienne collégiale',
                     'collégiale',
                     'cathédrale metropole',
                     'métropole',
                     'co-cathédrale',
                     'cathédrale église',
                     'cathédrale',
                     'ancienne cathédrale',
                     'basilique',
                     'basilique collegiale',
                     'synagogue',
                     'communauté',
                     'congrégation',
                     'couvent',
                     'carmel',
                     'monastère',
                     'abbaye de bénédictins',
                     'abbaye de bénédictines',
                     'abbaye',
                     'ancienne abbaye',
                     'ancienne abbatiale',
                     'primatiale',
                     'abbatiale',
                     'chapelle royale',
                     'chapelle paroissiale',
                     'chapelle protestante',
                     'chapelle catholique',
                     'chapelle du collège',
                     "chapelle de l'école",
                     'chapelle du lycée',
                     'chapelle du lycée privé',
                     "chapelle de l'institution",
                     "chapelle de l'orphelinat",
                     'chapelle du pensionnat',
                     "chapelle de l'hôpital",
                     "chapelle de la congregation",
                     "chapelle de l'établissement",
                     'chapelle',
                     'sanctuaire',
                     'séminaire',
                     'grand séminaire',
                     'oratoire',
                     'ancienne église',
                     'église abbatiale',
                     'église paroissiale',
                     'église réformée',
                     'église collégiale'
                     'église réformée protestante',
                     'église anglicane',
                     'église protestante reformée',
                     'église protestante',
                     'église mixte',
                     'église anglo-américaine',
                     'église simultanée',
                     'église évangélique luthérienne',
                     'église luthérienne',
                     'église néo-apostolique',
                     'école de musique',
                     'école',
                     'collège privé',
                     'collège',
                     'église',
                     'prieuré',
                     'grand temple',
                     'temple',
                     'temple luthérien',
                     'institution libre',
                     'institution',
                     'institut',
                     'théâtre',
                     'lycée privé',
                     'lycée',
                     'pensionnat',
                     'externat',
                     'salle',
                     'musée',
                     'conservatoire municipal',
                     'conservatoire national de musique',
                     'conservatoire national de région',
                     'conservatoire national régional',
                     'conservatoire',
                     'clinique',
                     'maison de retraite',
                     'loge maçonnique',
                     'maison d’accueil']
    new_chaine = ''
    type_edifice = None
    if not chaine:
        loggerCorrecteurorgues.error("Pas de libellé d'édifice, détection de type impossible.")
    else:
        chaine_minuscule = gen.supprimer_accents(chaine).lower()
        type_trouve = False
        for _type_edifice in types_edifice:
            index_denomination = chaine_minuscule.find(gen.supprimer_accents(_type_edifice))
            # Si la chaîne ne comprend pas dénomination connue :
            if index_denomination == -1:
                pass
            elif index_denomination == 0 and not type_trouve:
                type_trouve = True
                type_edifice = _type_edifice
                # Suppression du type d'édifice en début de nom
                new_chaine = chaine[len(type_edifice):].strip(' ')
            elif index_denomination > 0 and not type_trouve:
                type_trouve = False
        new_chaine = corriger_casse(new_chaine)
        if not type_trouve:
            type_edifice = None
            new_chaine = chaine
            loggerCorrecteurorgues.info("Aucun type d'édifice reconnu dans : {}.".format(chaine))
        else:
            loggerCorrecteurorgues.info("Type d'édifice reconnu dans : {}.".format(chaine))
    return new_chaine, type_edifice


def corriger_nom_edifice(chaine, commune=''):
    """
    Corrige le nom de l'édifice.
    Par exemple "église St-Georges" devient "église Saint-Georges".

    On tient compte de la commune :
    si la commune est dans le nom de l'édifice (à l'exception des Saint...), elle est supprimée de l'édifice.
    :param chaine: nom de l'édifice (str)
    :param commune: nom de la commune (str)
    :return: nom corrigé de l'édifice
    """
    #
    # Par défaut :
    new_chaine = 'NOM_EDIFICE_NON_STANDARD'
    # église sans nom :
    if chaine == '':
        new_chaine = chaine
    if 'saint' != chaine.lower()[:5]:

        # Si l'édifice est le nom de la commune, à l'exception des "Saint..." :
        if commune.lower() == chaine.lower():
            new_chaine = 'UN_EDIFICE'
        # Si la commune est présente en surcharge dans l'édifice : Dannemarie (Sainte Anne)
        # (Attention à la casse, variable.)
        elif commune.lower() == chaine.split('(')[0].lower().rstrip(' ') \
                and '(' in chaine \
                and ')' in chaine:
            # Recherche du vrai nom de l'édifice, entre parenthèses.
            match = re.match(r".*[(](.*)[)]", chaine)
            new_chaine = match.group(1)
            # On réinjecte dans la suite des traitements :
            chaine = new_chaine
        # Si la commune est en surcharge, mais une autre information se trouve entre parenthèses :
        # Non géré
        # Si le nom de la commune débute le nom de l'édifice, à l'exception des "Saint..." :
        elif commune.lower() == (chaine[:len(commune)]).lower():
            new_chaine = chaine[len(commune):].lstrip(' ')
            # On réinjecte dans la suite des traitements :
            chaine = new_chaine
        # Si le début du nom de la commune débute le nom de l'édifice :
        elif commune.lower().split(' ')[0] == (chaine[:len(commune.lower().split(' ')[0])]).lower():
            new_chaine = chaine[len(commune.lower().split(' ')[0]):].lstrip(' ')
    #
    # Ajout des traits d'union
    if chaine[:3] == 'St ':
        new_chaine = 'Saint-{}'.format(chaine[3:])
    if chaine[:4] == 'St. ':
        new_chaine = 'Saint-{}'.format(chaine[4:])
    if chaine[:4] == 'Ste ':
        new_chaine = 'Sainte-{}'.format(chaine[4:])
    if chaine[:6] == 'Saint ':
        new_chaine = 'Saint-{}'.format(chaine[6:])
    if chaine[:6] == 'Saint-':
        new_chaine = 'Saint-{}'.format(chaine[6:])
    if chaine[:7] == 'Sainte ':
        new_chaine = 'Sainte-{}'.format(chaine[7:])
    if chaine[:7] == 'Sainte-':
        new_chaine = 'Sainte-{}'.format(chaine[7:])
    if chaine[:7] == 'Saints ':
        new_chaine = 'Saints-{}'.format(chaine[7:])
    if chaine[:10] == 'Notre Dame':
        new_chaine = 'Notre-Dame{}'.format(chaine[10:])
    if chaine[:5] == 'N.-D.' or chaine[:2] == 'ND':
        new_chaine = 'Notre-Dame{}'.format(chaine[5:])
    if chaine[:10] == 'Notre-Dame':
        new_chaine = chaine
    if chaine[:14] == 'du Sacré Coeur':
        new_chaine = 'du Sacré-Cœur{}'.format(chaine[14:])
    if chaine[:13] == 'du Sacré Cœur':
        new_chaine = 'du Sacré-Cœur{}'.format(chaine[13:])
    if chaine[:13] == 'du Sacré-Cœur':
        new_chaine = 'du Sacré-Cœur{}'.format(chaine[13:])
    if chaine[:11] == 'Sacré Coeur':
        new_chaine = 'Sacré-Cœur{}'.format(chaine[11:])
    if chaine[:11] == 'Sacré-Coeur':
        new_chaine = 'Sacré-Cœur{}'.format(chaine[11:])
    if chaine[:10] == 'Sacré Cœur':
        new_chaine = 'Sacré-Cœur{}'.format(chaine[10:])
    if chaine[:10] == 'Christ Roi'\
            or chaine[:10] == 'CHRIST ROI':
        new_chaine = 'Christ-Roi{}'.format(chaine[10:])
    if chaine[:13] == 'Le Christ Roi':
        new_chaine = 'Christ-Roi{}'.format(chaine[13:])
    if chaine[:8] == 'Nativité':
        new_chaine = 'de la Nativité{}'.format(chaine[8:])
    if chaine[:11] == 'La Nativité' or chaine[:11] == 'la Nativité':
        new_chaine = 'de la Nativité{}'.format(chaine[11:])
    if chaine[:14] == 'de la Nativité':
        new_chaine = 'de la Nativité{}'.format(chaine[14:])
    if chaine[:10] == 'Assomption' or chaine[:12] == "L'Assomption":
        new_chaine = 'Assomption'
    if chaine[:13] == 'La Providence' or chaine[:13] == 'la Providence':
        new_chaine = 'La Providence'
    if chaine[:20] == 'Immaculée Conception' or chaine[:20] == 'Immaculée-Conception':
        new_chaine = 'Immaculée Conception'
    if chaine[:10] == 'La Trinité' or chaine[:10] == 'la Trinité' or chaine[:7] == 'Trinité':
        new_chaine = 'La Trinité'

    # Ramasse-miettes :
    if new_chaine == 'NOM_EDIFICE_NON_STANDARD':
        loggerCorrecteurorgues.debug('NOM_EDIFICE_NON_STANDARD {}'.format(chaine))
        info = new_chaine
        new_chaine = chaine
    else:
        info = 'NOM_EDIFICE_STANDARD'
    loggerCorrecteurorgues.info("Nom de l'édifice {}".format(info))

    # Suppression espaces
    new_chaine = new_chaine.strip(' ').lstrip('-')

    new_chaine_simple = _simplifier_nom_edifice(new_chaine)
    return new_chaine_simple


def _simplifier_nom_edifice(nom):
    """
    Suppression des informations annexes, supposées balisées par des parenthèses ().
    :param nom:
    :return:
    """
    # On ignore le texte restant entre parenthèses
    chaine_plus_simple = nom.split('(')[0].rstrip(' ')
    # Remplacemnt des espaces
    if ('Notre' in chaine_plus_simple or 'Saint' in chaine_plus_simple) and '&' not in chaine_plus_simple:
        chaine_plus_simple = chaine_plus_simple.replace(' ', '-')
    chaine_plus_simple = chaine_plus_simple.replace('---', ' - ')
    # Nettoyage
    chaine_plus_simple = chaine_plus_simple.rstrip(' ').lstrip(' ')
    # Correction des apostrophes
    chaine_plus_simple = chaine_plus_simple.replace("L'", "L’")
    chaine_plus_simple = chaine_plus_simple.replace("l'", "l’")
    chaine_plus_simple = chaine_plus_simple.replace("D'", "D’")
    chaine_plus_simple = chaine_plus_simple.replace("d'", "d’")
    #
    chaine_plus_simple = chaine_plus_simple.replace('xxiii', 'XXIII')
    chaine_plus_simple = chaine_plus_simple.replace('hopital', 'hôpital')
    chaine_plus_simple = chaine_plus_simple.replace('-Ix', '-IX')
    chaine_plus_simple = chaine_plus_simple.replace('Iv', 'IV')
    chaine_plus_simple = chaine_plus_simple.replace(',-', ', ')
    #
    chaine_plus_simple = chaine_plus_simple
    return chaine_plus_simple


def reduire_edifice(edifice, lacommune):

    # On supprime les termes après parenthèse ouvrante
    edifice2 = edifice.split('(')[0].rstrip(' ')
    # On supprime les termes après première virgule
    edifice2 = edifice2.split(',')[0].rstrip(' ')

    # On cherche le type d'édifice
    edifice3, type_edifice = detecter_type_edifice(edifice2)

    # On corrige le nom
    edifice4 = corriger_nom_edifice(edifice3, lacommune)
    loggerCorrecteurorgues.info("Nom de l'édifice et type de l'édifice :  {}, {}".format(edifice4, type_edifice))
    return edifice4, type_edifice

def geographie_administrative(code_insee):
    communes_francaises = codegeo.Communes()
    dictionnaire_communes = communes_francaises.to_dict_par_code()
    commune = dictionnaire_communes[code_insee]
    return commune.nom, commune.nomdepartement, commune.codedepartement, commune.nomregion, code_insee


def test_corriger_casse():
    print(corriger_casse('Temple de Beaumont'))
    print(corriger_casse('chapelle de l’Annonciation'))
    return


def test_detecter_type_edifice():
    for nom in [
                'Ancien hôtel de Béhague',
                'église de la nativité de la Très-Sainte-Vierge',
                'Eglise de la Nativité de la Sainte-Vierge',
                "église de la Nativité-de-la-Sainte-Vierge",
                "église de la nativité de la Très-Sainte-Vierge",
                'église de la Nativité de Notre-Dame',
                "église Notre-Dame-de-l'Assomption",
                "église Notre-Dame-de-l'Assomption",
                "église Notre-Dame-de-l'Assomption",
                "église Notre-Dame-de-l’Assomption",
                'Ancienne Cathédrale Notre-Dame',
                "Co-Cathédrale Notre-Dame-de-l'Annonciation",
                'église Saint-Amour & Saint-Victor',
                'Ecole de musique',
                'église CATHOLIQUE Saint-ALOYSE DE NEUDORF',
                "Cathédrale Saint-Gervais et Saint-Protais",
                "église du Sacré Coeur",
                'Chapelle du Grand Séminaire',
                'Eglise',
                'LES CHAPELLES BOURBON Saint Vincent',
                'église Notre-Dame',
                'église Notre-Dame (ancienne cathédrale)',
                "église du Vœu",
                "Ecole d'orgue de Guyane",
                "église Notre-Dame",
                "Église du Cœur Immaculé de Marie",
                "institution Les Iris",
                "Chapelle du Château",
                "Chapelle de l'Ecole Saint Elme",
                "Grand Temple",
                ]:
        print("{} ---> {}".format(nom, detecter_type_edifice(nom)))
    return


def test_corriger_nom_edifice():
    print(corriger_nom_edifice('Temple de Beaumont'))
    print(corriger_nom_edifice("Saint-Amour & Saint-Victor [église]", "Saint-Amour"))
    print(corriger_nom_edifice("de la Nativité de la Sainte-Vierge [église]", "Versailles"))
    print(corriger_nom_edifice("notre-dame-de-l'Annonciation [co-cathédrale]", "Bourg-en-Bresse"))
    print(corriger_nom_edifice("notre-dame-de-l'Assomption [église]", "Jassans-Riottier"))
    print(corriger_nom_edifice('les Chapelles Bourbon Saint Vincent', 'LES CHAPELLES BOURBON'))
    return


def test_reduire_edifice():
    print(reduire_edifice('église Notre-Dame (ancienne cathédrale)', 'Utopia'))
    print(reduire_edifice('église Saint-Jacques', 'Utopia'))
    print(reduire_edifice("Eglise de la Nativité de la Sainte-Vierge", 'Utopia'))


def test_simplifier_nom_edifice():
    print(_simplifier_nom_edifice('Saint-Maurice [eglise]'))
    print(_simplifier_nom_edifice('Sainte Elisabeth de Hongrie (Sainte Elisabeth)'))
    print(_simplifier_nom_edifice('Saint Jean-Baptiste (Cathédrale de Belley)'))
    return


if __name__ == '__main__':
    # test_corriger_casse()
    # test_reduire_edifice()
    # test_detecter_type_edifice()
    test_corriger_nom_edifice()
