import logging
import csv




class Codification():

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

    listeMinuscule = ["le", "la", "les", "de", "des", "du", "en", "et", "aux", "ès"]

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

    def corriger_casse(self, chaine):
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
                if mini_mot not in self.listeMinuscule:
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

    def supprimer_accents(self, chaine):
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

    def supprimer_article(self, terme):
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

    def detecter_type_edifice(self, chaine):
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
            #loggerCorrecteurorgues.error("Pas de libellé d'édifice, détection de type impossible.")
            print("Pas de libellé d'édifice, détection de type impossible.")
        else:
            chaine_minuscule = self.supprimer_accents(chaine).lower()
            type_trouve = False
            for _type_edifice in types_edifice:
                index_denomination = chaine_minuscule.find(self.supprimer_accents(_type_edifice))
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
            new_chaine = self.corriger_casse(new_chaine)
            if not type_trouve:
                type_edifice = None
                new_chaine = chaine
                #loggerCorrecteurorgues.debug("Pas de libellé d'édifice, détection de type impossible.")
                print("Pas de libellé d'édifice, détection de type impossible.")
            else:
                #loggerCorrecteurorgues.debug("Type d'édifice reconnu dans : {}.".format(chaine))
                print("Type d'édifice reconnu dans : {}.".format(chaine))
        return new_chaine, type_edifice


    def corriger_nom_edifice(self, chaine, commune=''):
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
            #loggerCorrecteurorgues.debug('NOM_EDIFICE_NON_STANDARD {}'.format(chaine))
            print('NOM_EDIFICE_NON_STANDARD {}'.format(chaine))
            info = new_chaine
            new_chaine = chaine
        else:
            info = 'NOM_EDIFICE_STANDARD'
        #loggerCorrecteurorgues.info("Nom de l'édifice {}".format(info))
        print("Nom de l'édifice {}".format(info))

        # Suppression espaces
        new_chaine = new_chaine.strip(' ').lstrip('-')

        new_chaine_simple = self._simplifier_nom_edifice(new_chaine)
        return new_chaine_simple


    def _simplifier_nom_edifice(self, nom):
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


    def reduire_edifice(self, edifice, lacommune):

        # On supprime les termes après parenthèse ouvrante
        edifice2 = edifice.split('(')[0].rstrip(' ')
        # On supprime les termes après première virgule
        edifice2 = edifice2.split(',')[0].rstrip(' ')

        # On cherche le type d'édifice
        edifice3, type_edifice = self.detecter_type_edifice(edifice2)

        # On corrige le nom
        edifice4 = self.corriger_nom_edifice(edifice3, lacommune)

        return type_edifice + " " + edifice4, type_edifice

        


    def codifie_commune(self, commune):
        """
        Codification d'une commune française, sur cinq lettres.
        :param commune:
        :return: code
        Source : Codification nationale de sites du réseau public de transport d'électricité.
        Nota : Une codification n'est pas unique, car plusieurs communes peuvent avoir même codification.
        """
        # REGLE : L'article inital est omis.
        commune_modifiee = self.supprimer_article(commune)
        # On corrige les e dans l'o (car deux caractères au lieu d'un seul):
        commune_modifiee = commune_modifiee.replace('œ', 'oe')
        #
        code = commune_modifiee.upper()
        # REGLE : Abréviations, pour les noms de plus de cinq caractères :
        if len(commune_modifiee) > 5:
            if code[:8] in self.ABREVIATIONS_8:
                code = self.ABREVIATIONS_8[code[:8]] + code[8:10]
            elif code[:6] in self.ABREVIATIONS_6:
                code = self.ABREVIATIONS_6[code[:6]] + code[6:9]
            elif code[:5] in self.ABREVIATIONS_5:
                code = self.ABREVIATIONS_5[code[:5]] + code[5:8]
            elif code[:4] in self.ABREVIATIONS_4:
                code = self.ABREVIATIONS_4[code[:4]] + code[4:7]
        # REGLE : Noms composés :
        # Les espaces sont considérés comme des tirets
        if ' ' in commune_modifiee:
            commune_modifiee = commune_modifiee.replace(' ', '-')
        # REGLE : on ne prend que le premier et dernier des mots, sans article :
        if '-' in commune_modifiee:
            mots = commune_modifiee.split('-')
            mots = [self.supprimer_article(m) for m in mots]
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
        code = self.supprimer_accents(code).upper()
        return code


    def codifie_edifice(self, edifice, type_edif):
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
            edifice = self.supprimer_article(edifice)
            edifice = self.supprimer_article(edifice)
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
                edifice = self.supprimer_article(edifice)
                edifice = self.supprimer_article(edifice)
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
            if edifice == 'Saint-Pierre-ès-Liens':
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
                code_edifice = 'ND' + self.supprimer_article(fin_notre_dame)[:4]
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
            code_edifice = self.supprimer_accents(code_edifice)
            code_edifice = code_edifice.replace(' ', '_')
            code_edifice = code_edifice.replace('.', '_')
            code_edifice = code_edifice.replace('-', '_')
        # Contrôle final
        if code_edifice == '------':
            logger_codification.critical("Echec de la codification de l'édifice : {}".format(edifice))
        return code_edifice


    def codifie_denomination(self, denomination):
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
                            '': 'X'}
        if denomination in denominations_orgue.keys():
            code_denomination = denominations_orgue[denomination]
        # Les dénominations de type 1--blabla sont décryptées
        elif '--' in denomination:
            code_denomination = denomination.split('--')[0]
        # Code dénomination par défaut :
        else:
            logger_codification.error('Dénomination inconnue : {}'.format(denomination))
            code_denomination = 'A'
        return code_denomination


    def codifier_instrument(self):
        """
        Codification d'un orgue de l'inventaire.
        :param orgue: objet de la classe OrgueInventaire
        :return: codification (str)
        """
        code_orgue = ''
        code_orgue += 'FR'
        code_orgue += '-'
        code_orgue += self.code_insee
        code_orgue += '-'
        code_orgue += self.codifie_commune(self.commune)
        code_orgue += '-'
        code_orgue += self.codifie_edifice(self.edifice, self.type_edifice)
        code_orgue += '-'
        code_orgue += self.codifie_denomination(self.designation)
        return code_orgue

    def geographie_administrative(self, commune_departement):
        commune_departement_split = commune_departement.split(", ")
        nom_commune = commune_departement_split[0]
        nom_departement = commune_departement_split[1]
        with open('code_INSEE.csv', 'r', encoding='utf-8') as read_obj:
            csv_reader = csv.reader(read_obj, delimiter=';')
            for row in csv_reader:
                ligne=row[0].split(",")
                if nom_commune == ligne[3] and nom_departement == ligne[4]:
                    commune = ligne[3]
                    departement = ligne[4]
                    region = ligne[5]
                    code_insee = ligne[0]
                    break
        for dep in self.CHOIX_DEPARTEMENT:
            if departement == dep[1]:
                code_departement = dep[0]
                break
        return commune, departement, code_departement, region, code_insee
                    


    def __init__(self, commune_departement, edifice, designation):
        self.commune, self.departement, self.code_departement, self.region, self.code_insee = self.geographie_administrative(commune_departement)
        self.edifice, self.type_edifice = self.reduire_edifice(edifice, self.commune)
        self.designation = designation
        self.codification = self.codifier_instrument()