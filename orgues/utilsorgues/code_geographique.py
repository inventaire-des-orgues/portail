"""
Classes de gestion du code géographique national français de l'INSEE.
https://www.insee.fr/fr/information/4316069
Codification des collectivités d'outre-mer (COM)
https://www.insee.fr/fr/information/2028040
"""
import logging

REP_GEODATA = 'orgues/utilsorgues/cog_ensemble_2021_csv/'

FIC_FRANCE_COMMUNES_INSEE = REP_GEODATA + 'commune2021.csv'
FIC_FRANCE_MOUVEMENTS_COMMUNES_INSEE = REP_GEODATA + 'mvtcommune2021.csv'
FIC_FRANCE_DEPARTEMENTS_INSEE = REP_GEODATA + 'departement2021.csv'
FIC_FRANCE_REGIONS_INSEE = REP_GEODATA + 'region2021.csv'

loggerCodegeogaphique = logging.getLogger('codegeographique')
loggerCodegeogaphique.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler('orgues/utilsorgues/logs/inventaire--codegeographique.log')
fh.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
loggerCodegeogaphique.addHandler(fh)
loggerCodegeogaphique.addHandler(ch)


class Region(object):
    """
    Une région
    """

    def __init__(self, _code, _cheflieu, _typenomenclair, _nomenclairmaj, _nomenclair, _libelle):
        self.code = _code
        self.cheflieu = _cheflieu
        self.typenomenclair = _typenomenclair
        self.nomenclairmaj = _nomenclairmaj
        self.nomenclair = _nomenclair
        self.libelle = _libelle

    def __repr__(self):
        return '<objet Region : {}, {}>'.format(self.nomenclair, self.code)


class Regions(dict):
    """
    Dictionnaire des régions
    clés: codes
    valeurs: objets Region
    """

    def __init__(self):
        super().__init__()
        with open(FIC_FRANCE_REGIONS_INSEE, 'r', encoding='utf-8') as fic_csv:
            # on ignore l'entête
            lignes = fic_csv.readlines()[1:]
            ll = [item.strip('\r\n').split(',') for item in lignes]
            regions = [Region(*ligne) for ligne in ll]
            # Construction d'un dictionnaire {nom: commune}
            for region in regions:
                if region.code not in self.keys():
                    self[region.code] = region
            loggerCodegeogaphique.info('Chargement de {} régions.'.format(len(self)))


class Departement(object):
    """
    Un département
    """

    def __init__(self, _code, _region, _cheflieu, _typenomenclair, _nomenclairmaj, _nomenclair, _libelle):
        self.code = _code
        self.region = _region
        self.cheflieu = _cheflieu
        self.typenomenclair = _typenomenclair
        self.nomenclairmaj = _nomenclairmaj
        self.nomenclair = _nomenclair
        self.nom = _libelle

    def __repr__(self):
        return '<objet Departement {}, code {}, code région {}>'.format(self.nom, self.code, self.region)


class Departements(dict):
    """
    Dictionnaire des départements
    """

    def __init__(self):
        super().__init__()
        with open(FIC_FRANCE_DEPARTEMENTS_INSEE, 'r', encoding='utf-8') as fic_csv:
            # on ignore l'entête
            lignes = fic_csv.readlines()[1:]
            ll = [item.strip('\r\n').split(',') for item in lignes]
            departements = [Departement(*ligne) for ligne in ll]
            # Construction d'un dictionnaire {nom: commune}
            for departement in departements:
                if departement.code not in self.keys():
                    self[departement.code] = departement
            loggerCodegeogaphique.info('Chargement de {} départements.'.format(len(self)))

    def to_dict_nom_code(self):
        dict_nom_code = dict()
        for departement in self.values():
            dict_nom_code[departement.nom] = departement.code
        return dict_nom_code


class Evenements(list):
    def __init__(self):
        # Classement par ordre anti-chronologique
        with open(FIC_FRANCE_MOUVEMENTS_COMMUNES_INSEE, 'r', encoding='utf-8') as fic_csv:
            # on ignore l'entête
            lignes_fic_evenements = fic_csv.readlines()[1:]
            ll = [item.split(',') for item in lignes_fic_evenements]
            self.extend([Evenement(*ligne) for ligne in ll])

    def to_list_anciennne_nouvelle(self):
        """
        clés : code INSEE de la commune avant transition
        valeurs : liste de codes INSEE des communes après la transition
        :return: dictionnaire
        Nota bene : On ne tient pas compte ici de la chronologie.
        """
        transitions_communes = dict()
        for ev in self:
            # On ne regarde que les évènements de type transition
            # et non les créations ou rétablissements, suppressions, changements de code.
            if ev.mod in ['10', '31', '32', '33', '34', '70']:
                if ev.com_av != ev.com_ap:
                    if ev.com_av not in transitions_communes.keys():
                        transitions_communes[ev.com_av] = [ev.com_ap]
                    elif ev.com_ap not in transitions_communes[ev.com_av]:
                        transitions_communes[ev.com_av].append(ev.com_ap)
        return transitions_communes


class Evenement(object):
    """
    """

    def __init__(self, _mod, _date_eff,
                 _typecom_av, _com_av, _tncc_av, _ncc_av, _nccenr_av, _libelle_av,
                 _typecom_ap, _com_ap, _tncc_ap, _ncc_ap, _nccenr_ap, _libelle_ap):
        self.significationmod = {
            '10': 'Changement de nom',  # COM|COMA -> COM|COMA
            '20': 'Création',  # COM -> COM
            '21': 'Rétablissement',  # COM|COMD|COMA|ARM -> COM|COMA|ARM
            '30': 'Suppression',  # COM -> COM
            '31': 'Fusion simple',  # COM -> COM
            '32': 'Création de commune nouvelle',  # COM|COMA|COMD -> COM|COMA
            '33': 'Fusion association',  # COM|COMA -> COM|COMA
            '34': 'Transformation de fusion association en fusion simple',  # COM|COMD|COMA -> COM|COMD
            '41': 'Changement de code dû à un changement de département',  # COM -> COM
            '50': 'Changement de code dû à un transfert de chef-lieu',  # COM|COMA -> COM|COMA
            '70': 'Transformation de commune associé en commune déléguée'  # COM -> COMD
        }
        self.mod = _mod
        self.date_eff = _date_eff
        self.typecom_av = _typecom_av
        self.com_av = _com_av
        self.tncc_av = _tncc_av
        self.ncc_av = _ncc_av
        self.nccenr_av = _nccenr_av
        self.libelle_av = _libelle_av
        self.typecom_ap = _typecom_ap
        self.com_ap = _com_ap
        self.tncc_ap = _tncc_ap
        self.ncc_ap = _ncc_ap
        self.nccenr_ap = _nccenr_ap
        self.libelle_ap = _libelle_ap


class Commune(object):
    """
    Une commune de France
    https://www.insee.fr/fr/information/2668350
    """

    def __init__(self, _typecom, _codecommune, _coderegion, _codedepartement, _CTCD, _codearr,
                 _typenomenclair, _nomenclairmaj, _nomenclairsansarticle, _nomenclairavecarticle, _can, _comparent,
                 les_departements):
        """
        :param _typecom:
            COM
            COMA
            COMD
            ARM
        :param _codecommune:
        :param _coderegion:
        :param _codedepartement:
        :param _codearr:
        :param _typenomenclair:
            0 	Pas d'article et le nom commence par une consonne sauf H muet 	charnière = DE
            1 	Pas d'article et le nom commence par une voyelle ou un H muet 	charnière = D'
            2 	Article = LE 	charnière = DU
            3 	Article = LA 	charnière = DE LA
            4 	Article = LES 	charnière = DES
            5 	Article = L' 	charnière = DE L'
            6 	Article = AUX 	charnière = DES
            7 	Article = LAS 	charnière = DE LAS
            8 	Article = LOS 	charnière = DE LOS
        :param _nomenclairmaj
        :param _nomenclairsansarticle:
        :param _nomenclairavecarticle:
        :param _can: Code canton. Pour les communes « multi-cantonales » code décliné de 99 à 90 (pseudo-canton) ou de 89 à 80 (communes nouvelles)
        :param _comparent:
        """
        self.typecom = _typecom
        self.codecommune = _codecommune
        self.coderegion = _coderegion
        self.nomregion = ''
        self.codedepartement = _codedepartement
        self.codearr = _codearr
        self.nomenclairmaj = _nomenclairmaj
        self.nomenclairsansarticle = _nomenclairsansarticle
        self.nom = _nomenclairavecarticle
        self.can = _can
        self.comparent = _comparent
        self.code_insee = self.codecommune
        if self.typecom == 'COM' or self.typecom == 'ARM':
            self.nomdepartement = les_departements[self.codedepartement].nom
        self.nomcomparent = ''

    def __repr__(self):
        if self.typecom == 'COM' or self.typecom == 'ARM':
            return '<objet Commune {}, {}, {}, {}, {}>'.format(
                self.nom, self.codecommune, self.codedepartement, self.nomdepartement, self.typecom)
        else:
            return '<objet Commune {}, {}, {}>'.format(
                self.nom, self.codecommune, self.typecom)


class Communes(list):
    """
    Liste des communes de France
    """

    def __init__(self):
        #
        # On charge les départements.
        departements_francais = Departements()
        #
        with open(FIC_FRANCE_COMMUNES_INSEE, 'r', encoding='utf-8') as fic_csv:
            # on ignore l'entête
            lignes_fic_communes = fic_csv.readlines()[1:]
            ll = [item.rstrip('\r\n').split(',') for item in lignes_fic_communes]
            # On ne prend que les communes actuelles, associées et déléguées
            for ligne in ll:
                self.append(Commune(*ligne, departements_francais))
            #loggerCodegeogaphique.info('Chargement de {} communes.'.format(len(self)))
        # Pour les communes associées ou déléguées, ainsi que les arrondissements,
        # on ajoute en attribut le nom de la commune parente.
        self.ajouter_noms_comparent()
        self.ajouter_region()

    def __repr__(self):
        return '<objet Communes, {} communes'.format(len(self))

    def to_dict_par_code(self):
        communes_par_code = dict()
        for commune in self:
            # On ne considère que les communes de pleins droits (COM).
            if commune.typecom == 'COM' or commune.typecom == 'ARM':
                # Construction d'un dictionnaire {code INSEE: commune COM}
                if commune.code_insee not in communes_par_code.keys():
                    communes_par_code[commune.code_insee] = commune
                else:
                    print("Code INSEE {} en double !".format(commune.code_insee))
                    loggerCodegeogaphique.critical("Code INSEE {} en double !".format(commune.code_insee))
        return communes_par_code

    def to_dict_par_nom(self):
        communes_par_nom = dict()
        for commune in self:
            # Construction d'un dictionnaire {nom: [communes]}
            # Plusieurs communes possibles
            if commune.nom not in communes_par_nom.keys():
                communes_par_nom[commune.nom] = [commune]
            else:
                # Si la commune n'existe pas déjà (l'unicité est donnée par le code INSEE) :
                if commune.code_insee not in [com.code_insee for com in communes_par_nom[commune.nom]]:
                    communes_par_nom[commune.nom].append(commune)
                else:
                    del commune
        return communes_par_nom

    def ajouter_noms_comparent(self):
        communes_codes = self.to_dict_par_code()
        for commune in self:
            if commune.typecom in ['COMA', 'COMD']:
                commune_parente = communes_codes[commune.comparent]
                commune.nom_comparent = commune_parente.nom
                commune.codedepartement = commune_parente.codedepartement
                commune.coderegion = commune_parente.coderegion

    def ajouter_region(self):
        dict_regions = Regions()
        for commune in self:
            if commune.typecom == "COM" or commune.typecom == 'ARM':
                commune.nomregion = dict_regions[commune.coderegion].libelle

def test_communes():
    communes_francaises = Communes()
    print(communes_francaises)

    print(communes_francaises.to_dict_par_nom()["L'Argentière-la-Bessée"])
    print(communes_francaises.to_dict_par_nom()["Rochefort"])
    print(communes_francaises.to_dict_par_nom()["Rochefort"][1])
    print(communes_francaises.to_dict_par_nom()["Corcelles"][0])  # Commune associée
    print(communes_francaises.to_dict_par_nom()["Corcelles"][0].typecom)
    print(communes_francaises.to_dict_par_nom()["Corcelles"][0].nom_comparent)
    print(communes_francaises.to_dict_par_nom()["Cordieux"])
    print(communes_francaises.to_dict_par_nom()["Bagnoles-de-l'Orne"])
    #
    print(communes_francaises.to_dict_par_code()['01262'])
    return


def test_departements():
    departements_francais = Departements()
    print(departements_francais["22"])
    return


def test_inverse_departements():
    departements_francais = Departements()
    print(departements_francais.to_dict_nom_code()["Côtes-d'Armor"])
    assert departements_francais.to_dict_nom_code()["Côtes-d'Armor"] == '22'
    return


def test_regions():
    regions_francaises = Regions()
    print(regions_francaises["93"])
    return


def test_evenements():
    transitions = Evenements()
    transitions_dict = transitions.to_list_anciennne_nouvelle()
    print(transitions_dict['74125'])

if __name__ == '__main__':
    test_regions()
    test_departements()
    test_inverse_departements()
    test_communes()
    test_evenements()