# -*- coding: utf-8 -*-
"""
Codification d'un orgue
"""
import logging
import orgues.utilsorgues.tools.generiques as gen

logger_codification = logging.getLogger('codification')
logger_codification.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
# create console handler with a higher log level
chd = logging.StreamHandler()
chd.setLevel(logging.INFO)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
chd.setFormatter(formatter)
# add the handlers to the logger
logger_codification.addHandler(chd)


ABREVIATIONS_4 = {'BEAU': 'BX',
                  'BOUR': 'BZ',
                  'BONN': 'BN',
                  'CHAU': 'CX',
                  'COUR': 'CZ',
                  'FONT': 'FT',
                  'MONT': 'MT',
                  'PONT': 'PT',
                  'VIGN': 'VN',
                  'VILL': 'VL'}

ABREVIATIONS_5 = {'CASTE': 'CS',
                  'CHAMB': 'CB',
                  'CHAMP': 'CP',
                  'CHATE': 'CT',
                  'MARQU': 'MQ',
                  'MARTI': 'MR',
                  'ROQUE': 'RQ'}

ABREVIATIONS_6 = {'BELLEV': 'BV',
                  'CHANTE': 'CN',
                  'PIERRE': 'PRR'}

ABREVIATIONS_8 = {'CHAMPAGN': 'CPN'}


def codifie_commune(commune):
    """
    Codification d'une commune française, sur cinq lettres.
    :param commune:
    :return: code
    Source : Codification nationale de sites du réseau public de transport d'électricité.
    Nota : Une codification n'est pas unique, car plusieurs communes peuvent avoir même codification.
    """
    # REGLE : L'article inital est omis.
    commune_modifiee = gen.supprimer_article(commune)
    # On corrige les e dans l'o (car deux caractères au lieu d'un seul):
    commune_modifiee = commune_modifiee.replace('œ', 'oe')
    #
    code = commune_modifiee.upper()
    # REGLE : Abréviations, pour les noms de plus de cinq caractères :
    if len(commune_modifiee) > 5:
        if code[:8] in ABREVIATIONS_8:
            code = ABREVIATIONS_8[code[:8]] + code[8:10]
        elif code[:6] in ABREVIATIONS_6:
            code = ABREVIATIONS_6[code[:6]] + code[6:9]
        elif code[:5] in ABREVIATIONS_5:
            code = ABREVIATIONS_5[code[:5]] + code[5:8]
        elif code[:4] in ABREVIATIONS_4:
            code = ABREVIATIONS_4[code[:4]] + code[4:7]
    # REGLE : Noms composés :
    # Les espaces sont considérés comme des tirets
    if ' ' in commune_modifiee:
        commune_modifiee = commune_modifiee.replace(' ', '-')
    # REGLE : on ne prend que le premier et dernier des mots, sans article :
    if '-' in commune_modifiee:
        mots = commune_modifiee.split('-')
        mots = [gen.supprimer_article(m) for m in mots]
        code = commune_modifiee[0] + '_' + mots[-1][:3]
        # REGLE : Saint devient SS :
        if mots[0] in ['Saint', 'Sainte', 'Saints', 'Saintes']:
            code = 'SS' + mots[-1][:3]
            # REGLE : MARC devient MC et MAUR devient MR :
            if mots[-1][:4] in ['MARC', 'MAUR']:
                code = 'SS' + 'M' + mots[-1][4] + mots[-1][5]
    if code == commune_modifiee.upper():
        code = commune_modifiee[:5]
    # REGLE : Si moins de cinq caractères, on répète le dernier jusqu'à cinq.
    if 0 < len(code) < 5:
        code = code + code[-1] * (5 - len(code))
    # Post-traitements :
    code = gen.supprimer_accents(code).upper()
    return code


def codifie_edifice(edifice, type_edif):
    """
    Codification d'un édifice sur 6 caractères.
    :param edifice: nom standardisé de l'édifice
    :param type_edif: type de l'édifice
    :return: codification sur 6 caractères
    """
    code_edifice = '------'

    if edifice == '' and type_edif is None:
        logger_codification.error("Pas de nom d'édifice, ni de type.")

    # Si l'edifice n'a pas de nom (qu'un type), exemple fréquent : '[Temple]'
    elif (edifice == '' or edifice is None) and type_edif is not None:
        if type_edif in [
                'temple',
                'grand temple',
                'temple protestant',
                'temple réformé',
                ]:
            code_edifice = 'TEMPLE'
        elif type_edif in [
                'église protestante',
                'temple prostestant',
                'chapelle protestante',
                ]:
            code_edifice = 'PROTES'
        elif type_edif == 'église réformée':
            code_edifice = 'REFORM'
        elif type_edif == 'église luthérienne':
            code_edifice = 'LUTHER'

        elif type_edif in ['église évangélique',
                           'église évangélique luthérienne',
                           'église néo-apostolique']:
            code_edifice = 'EVANGE'
        elif type_edif in [
                'église catholique',
                'église paroissiale',
                'église',
                'église abbatiale',
                ]:
            code_edifice = 'EGLISE'
        elif type_edif == 'église mixte':
            code_edifice = 'EMIXTE'
        elif type_edif == 'église anglicane':
            code_edifice = 'ANGLIC'
        elif type_edif == 'synagogue':
            code_edifice = 'SYNAGO'
        elif type_edif == 'loge maçonnique':
            code_edifice = 'LOGEFM'
        elif type_edif in [
                'conservatoire national de région',
                'conservatoire national de musique',
                'conservatoire national régional',
                'conservatoire',
                'conservatoire municipal',
                'école de musique',
                ]:
            code_edifice = 'MUSIQU'
        elif type_edif == 'séminaire' or type_edif == 'grand séminaire':
            code_edifice = 'SEMINA'
        elif type_edif == "chapelle de l'hôpital":
            code_edifice = 'HOPITA'
        elif type_edif == "chapelle du collège":
            code_edifice = 'COLLEG'
        elif type_edif == 'maison de retraite':
            code_edifice = 'MRETRA'
        elif type_edif == 'musée':
            code_edifice = 'MUSEEE'
        else:
            logger_codification.critical("Absence codification avec uniquement le type {}".format(type_edif))
    else:
        # On supprime jusqu'à deux articles en début de nom :
        edifice = gen.supprimer_article(edifice)
        edifice = gen.supprimer_article(edifice)
        # On corrige les e dans l'o (car deux caractères au lieu d'un seul):
        edifice = edifice.replace('œ', 'oe')
        # Sacré-Coeur:
        if 'Sacré-Coeur' in edifice:
            code_edifice = 'SCOEUR'
        # Coeur de Marie
        if 'Coeur Immaculé de Marie' in edifice:
            code_edifice = 'COEURM'
        # Codification des GRAND (séminaire, théâtre, casino, ...)
        elif edifice[:5] == 'grand':
            if len(edifice) >= 10:
                code_edifice = 'GD' + edifice[6:10]
            else:
                code_edifice = 'GRANDD'
        # Codification des églises au sein d'une congrégation :
        if edifice[:12] == 'congrégation':
            edifice = edifice[12:]
            edifice = gen.supprimer_article(edifice)
            edifice = gen.supprimer_article(edifice)
        # Codification Missions étrangères
        if 'Missions Étrangères' in edifice:
            code_edifice = 'MISSET'
        # Codification des églises au sein d'une école :
        if edifice[:5] == 'école' or edifice[:5] == 'ecole' or edifice[:7] == 'collège':
            if len(edifice) < 5:
                code_edifice = 'ECOLEE'
            else:
                code_edifice = 'ECO' + edifice[-3:]
        # Codification des églises dédicacées à un saint ou une sainte :
        # Cas particuliers :
        if edifice == 'Saint-Pierre-ès-Liens' or edifice == 'Saint-Pierre-aux-Liens':
            code_edifice = 'STPIEL'
        elif edifice == 'Jean-Marie-Vianney':
            code_edifice = 'STJMVI'
        elif edifice == 'Saint-Marceau':
            code_edifice = 'STMARU'
        elif edifice == 'Saint-Martin-ès-Vignes':
            code_edifice = 'STMAEV'
        elif edifice == "Sainte-Thérèse d’Avila":
            code_edifice = 'STTHEA'
        elif edifice == "Sainte-Thérèse-de-l’Enfant-Jésus" \
                or edifice == "Sainte-Thérèse-de-Lisieux":
            code_edifice = 'STTHEL'
        elif edifice == 'Saint-Jean-Bosco':
            code_edifice = 'STJBOS'
        elif edifice == 'Saint-Jean-Baptiste':
            code_edifice = 'STJBAP'
        elif edifice == 'Saint-Jean-Baptiste-de-la-Salle':
            code_edifice = 'STJDLS'
        elif edifice == "Saint-François-d’Assise":
            code_edifice = 'STFASS'
        elif edifice == "Saint-François-de-Paule":
            code_edifice = 'STFPAU'
        elif edifice == "Saint-François-de-Sales":
            code_edifice = 'STFSAL'
        elif edifice == "Sainte-Jeanne-d’Arc":
            code_edifice = 'STJARC'
        # Cas général
        elif edifice[:6] == 'Saint-':
            saint = edifice[6:]
            # Exception : Plusieurs saints, mais sans regarder dans les parenthèses :
            if 'Saint' in saint and saint.find('(') <= saint.find('Saint'):
                if saint == 'Denis-du-Saint-Sacrement':
                    code_edifice = 'ST' + 'DSSS'
                elif '&' in saint:
                    premier_saint = saint.split('&')[0].rstrip()
                    deuxieme_saint = ''
                    if 'Saint-' in saint:
                        deuxieme_saint = saint.split('&')[1].lstrip().lstrip('Saint-')
                    elif 'Sainte-' in saint:
                        deuxieme_saint = saint.split('&')[1].lstrip().lstrip('Sainte-')
                    code_edifice = 'SS' + premier_saint[0] + premier_saint[-1] + deuxieme_saint[0] + deuxieme_saint[-1]
                else:
                    logger_codification.error("Nom d'édifice avec plusieurs saints non géré : {}".format(edifice))
                    code_edifice = 'SS' + saint[:4]
            else:
                code_edifice = 'ST' + saint[:4]
        elif edifice[:7] == 'Sainte-':
            sainte = edifice[7:]
            code_edifice = 'ST' + sainte[:4]
        # églises dédicacées à Saint-Jean-Baptiste :
        elif 'Nativité-de-Saint-Jean-Baptiste' in edifice:
            code_edifice = 'NATSJB'
        # Codification des églises dédicacées à la Sainte-Vierge :
        elif edifice.lower() == 'notre-dame':
            code_edifice = 'NDAMEV'
        elif edifice[:10].lower() == 'notre-dame':
            notre_dame = edifice[10:]
            # On force les titres de Notre-Dame avec des traits d'union :
            notre_dame = notre_dame.replace(' ', '-')
            fin_notre_dame = notre_dame
            if '-' in notre_dame:
                fin_notre_dame = notre_dame.split('-')[-1]
            code_edifice = 'ND' + gen.supprimer_article(fin_notre_dame)[:4]
        # Nativité :
        elif edifice[:8].lower() == 'nativité':
            nativite = edifice[8:]
            if nativite == '':
                code_edifice = 'NATIVI'
            elif 'B.V.M' in nativite:
                code_edifice = 'NATBVM'
            elif 'Notre-Dame' in nativite:
                code_edifice = 'NATNDM'
            elif 'Sainte-Vierge' in nativite or 'Vierge' in nativite:
                code_edifice = 'NATSVI'
            else:
                code_edifice = 'NATIVI'
        # Ramasse-miettes
        elif code_edifice == '------':
            code_edifice = edifice[:6]
        # On complète les caractères manquant par le dernier caractère.
        code_edifice = code_edifice.ljust(6, code_edifice[-1])
        code_edifice = code_edifice.upper()
        code_edifice = gen.supprimer_accents(code_edifice)
        code_edifice = code_edifice.replace(' ', '_')
        code_edifice = code_edifice.replace('.', '_')
        code_edifice = code_edifice.replace('-', '_')
    # Contrôle final
    if code_edifice == '------':
        logger_codification.critical("Echec de la codification de l'édifice : {}".format(edifice))
    return code_edifice


def codifie_denomination(denomination):
    """
    Codification de la dénomination d'un orgue.
    :param denomination: (str)
    :return: code (str)
    Dans les ouvrages d'inventaire, et d'une façon générale, dénomination et emplacement sont souvent confondus.
    """
    denominations_orgue = {'G.O.': 'T',
                           'Grand Orgue': 'T',
                           'orgue de tribune': 'T',
                           'orgue de transept': 'C',
                           'orgue positif': 'D',
                           'orgue régale': 'D',
                           "orgue d'accompagnement": 'C',
                           'petit orgue': 'D',
                           "orgue d'étude": 'D',
                           'positif': 'D',
                           'grand positif': 'D',
                           'chapelle': 'D',
                           'oratoire': 'D',
                           "chapelle d'hiver": 'D',
                           'chapelle de la Vierge': 'D',
                           'sacristie': 'D',
                           'O.C.': 'C',
                           'O.C.1': 'C',
                           'O.C.2': 'D',
                           'O.C. 1': 'C',
                           'O.C. 2': 'D',
                           'crypte': 'Y',
                           'coffre': '0',
                           'Coffre': '0',
                           'orgue coffre': '0',
                           'auditorium': '1',
                           'orgue 1': '1',
                           'orgue 2': '2',
                           'ancien': '1',
                           'nouveau': '2',
                           '1': '1',
                           '2': '2',
                           '3': '3',
                           '4': '4',
                           '5': '5',
                           '6': '6',
                           '7': '7',
                           'I': '1',
                           'II': '2',
                           'III': '3',
                           'IV': '4',
                           'V': '5',
                           'VI': '6',
                           'VII': '7',
                           "Orgue d'étude": '1',
                           'Orgue espagnol': '2',
                           'Orgue majorquin': '3',
                           'Orgue napolitain': '4',
                           "orgue d'étude (1982)": '1',
                           "orgue d'étude (1968)": '2',
                           'polyphone': 'P',
                           'buffet': 'B',
                           'orgue à rouleau': 'R',
                           'orgue à cylindre': 'R',
                           'orgue': 'X',
                           '': 'X'}
    if denomination in denominations_orgue.keys():
        code_denomination = denominations_orgue[denomination]
    # Les dénominations de type 1--blabla sont décryptées
    elif '--' in denomination:
        code_denomination = denomination.split('--')[0]
    # Code dénomination par défaut :
    else:
        logger_codification.error('Dénomination inconnue : {}'.format(denomination))
        code_denomination = 'X'
    return code_denomination


def codifier_instrument(code_insee, commune, edifice_standard, type_edifice, designation):
    """
    Codification d'un orgue de l'inventaire.
    :param orgue: objet de la classe OrgueInventaire
    :return: codification (str)
    """
    logger_codification.debug('codifier_instrument {} {}'.format(str(edifice_standard), str(commune)))
    code_orgue = ''
    code_orgue += 'FR'
    code_orgue += '-'
    code_orgue += code_insee
    code_orgue += '-'
    code_orgue += codifie_commune(commune)
    code_orgue += '-'
    code_orgue += codifie_edifice(edifice_standard, type_edifice)
    code_orgue += '1' # TODO gestion de l'indice édifice
    code_orgue += '-'
    code_orgue += codifie_denomination(designation)
    return code_orgue


def test_codifie_edifice():
    for edifice_et_type in edifices_tests:
        logger_codification.info('Codage édifice : {} {}'.format(codifie_edifice(*edifice_et_type), edifice_et_type))
        pass

def test_codifie_commune():
    for com in communes_tests:
        logger_codification.info('Codage commune : {} {}'.format(codifie_commune(com), com))
        pass


if __name__ == '__main__':
    test_codifie_commune()
    test_codifie_edifice()