
import numpy as np
import copy
from praktikal.sysdat import *
from praktikal.conf import config as config_main
config = getConfig(config_main)

np.seterr(divide='ignore')
np.seterr(invalid='ignore')

intSigFig = int(config['printNuSigFigs'])
intDimLim = int(config['printNuDimLim'])
intExpThr = int(config['printNuExpThreshold'])
intExpStep = int(config['printNuExpStep'])
config['printNuTypeFix'] = 'abs'

if intSigFig < 1:
    raise ValueError(f'Number of Significant figures must be 1 or more, not {intSigFig}')

if intExpThr < 1:
    raise ValueError(f'Threshold decimal exponent must be 1 or more, not {intExpThr}')

if intExpStep < 1:
    raise ValueError(f'Decimal exponent step must be 1 or more, not {intExpStep}')

if intExpThr % intExpStep != 0:
    raise ValueError('Threshold decimal exponent must be a multiple of Decimal exponent step')

def cartesianProdFlat(listVars):
        listReturn = []
        arr1 = listVars[0]
        if len(listVars) > 1:
                arr2 = cartesianProdFlat(listVars[1:])
                for el1 in arr1:
                        for el2 in arr2:
                                listReturn.append((el1,) + el2)
                return listReturn
        else:
                for el in arr1:
                        listReturn.append((el,))
                return listReturn

def projectToAxis(axisIdx, list0):
        listReturn = []
        for tup in list0:
                listReturn.append(tup[axisIdx])
        return listReturn

def getUnits():
    dictUnitsBase = sysdatconf['units_base']

    dictUnitsComposite = {}
    dictUnitsCompositeDefault = sysdatconf['units_composite']
    dictUnitsCompositeCustom = config.get('printNuCompositeUnits', {})
    tupUnitsComposite = (dictUnitsCompositeDefault, dictUnitsCompositeCustom)
    for dictUnits in tupUnitsComposite:
        for strUnit, dictDef in dictUnits.items():
            dictUnitsComposite[strUnit] = dictDef
    for strUnit, dictDef in dictUnitsComposite.copy().items():
        if dictDef == {}:
            dictUnitsComposite.pop(strUnit)

    dictUnitsLen = {}
    for dictUnits_ in (dictUnitsBase, dictUnitsComposite):
        for strUnit in dictUnits_:
            l = len(strUnit)
            dictUnitsLen[l] = dictUnitsLen.get(l, set())
            dictUnitsLen[l].add(strUnit)
    return dictUnitsBase, dictUnitsComposite, dict(sorted(dictUnitsLen.items(), reverse=True))

def arrConstant(arr):
    if type(arr) in [int, float, np.float64]:
        return arr
    an = np.nonzero(~np.isnan(arr))
    if len(arr[an]) > 0:
        suspVal = arr[an][0]
        suspZeroes = np.nan_to_num(arr - suspVal)
        if np.size(an) != 0 and np.max(np.abs(suspZeroes)) <= suspVal * (10 ** -config['printNuFloatToleranceDigits']):
            return suspVal

def getLeadingExponent(x_, intSgFg):
    # vrne desetiški eksponent vodilne števke zaokroženega števila
    x = np.abs(x_)
    if (float(x) == 0.):
        return 1
    decExpLeading = int(np.floor(np.log10(x))) # desetiški eksponent vodilne števke (pred zaokroževanjem)
    if intSgFg != np.inf:
        decExpLeading = int(np.floor(np.log10(x + 5 * 10 ** int(decExpLeading-intSgFg)))) # popravek zaradi preliva
    return decExpLeading

def getDecExponent(x, bPermitDecimalSignificand=True):
    # returns logarithmically averaged exponent of number or ndarray
    # excluding NaN values
    x_ = np.abs(copy.deepcopy(x))
    try:
        len(x_)
        idxs_aN = np.argwhere(~np.isnan(x_)).T
        # 0 len check
        if len(idxs_aN) == 0:
            return
        idxs_aN = idxs_aN[0]
        x_ = x_[idxs_aN]
    except: # ni seznam        
        if np.isnan(x_):
            return
    
    if type(x_) == np.ndarray and len(x_) == 0:
        return

    if type(x_) == np.ndarray:
        exp_min = np.floor(np.log10(np.sort(x_)[1])) # drugi najmanjši element - seznam se pogosto začne z vrednostjo 0
        exp_max = np.floor(np.log10(np.sort(x_)[-1])) # največji element
        exp_avg = 0.5 * (exp_max + exp_min)
    else:
        exp_avg = np.floor(np.log10(x_))
    # rounding exp. down, so there are no 0.XYZ values
    dec_exp = (exp_avg // intExpStep) * intExpStep
    # permitting 0.XYZ values if exp. is small enough

    # if np.isnan(dec_exp):
    #     dec_exp = 0
    # print(x_, dec_exp)

    if bPermitDecimalSignificand:
        dec_exp *= (np.abs(dec_exp) - intExpStep != 0)
    
    if np.abs(dec_exp) >= intExpThr:
        return int(dec_exp)
    # return 0

def strNuFormat(nu, bLimitDims=True):
        # order of magnitude pre-formatting
        # bLimitDims omeji število prikazanih elementov (s tropičjem) - onemogočeno pri tabelah

        decExp = getDecExponent(nu.val, False)
        # kompenzacija izpostavljenega desetiškega eksponenta
        if decExp != None:
            nu *= 10 ** (-decExp)
        # ustrezna oblika negotovosti
        if config['printNuTypeFix'] == 'abs':
            nu += 0
        if config['printNuTypeFix'] == 'rel':
            nu *= 1
        
        # zaznavanje konstantnih seznamov (negotovosti)
        const = arrConstant(nu.unc)
        if const != None:
            nu.unc = const
        
        # brez negotovosti
        if np.sum(np.abs(nu.unc)) == 0:
            # string formatting
            # str_val = strNumFormat(nu.val, np.inf, bLimitDims=bLimitDims, decExpForced=decExp) # neskončna natančnost
            str_val = strNumFormat(nu.val, np.inf, bLimitDims=bLimitDims, decExpForced=None) # neskončna natančnost
            str_unit = str(nu.unit)
            return str_val, '0', decExp, str_unit
        
        # negotovost
        else:
            if config['printNuSigFigsDependentOnUnc']:
                # red velikosti negotovosti
                if type(nu.unc) == np.ndarray:
                    idx_an = np.argwhere(~np.isnan(nu.unc))
                    intExpUnc = np.floor(np.average(np.log10(nu.unc[idx_an])))
                else:
                    intExpUnc = np.floor(np.log10(nu.unc))
                
                intExpUncRound = intExpUnc - intSigFig + 1
                # rounding digits beyond uncertainty threshold
                nu.val = np.floor(0.5 + nu.val * 10 ** -(intExpUncRound - 1)) * 10 ** (intExpUncRound - 1)
                # string formatting
                valSigFigs = np.int16(np.log10(np.abs(nu.val)) - intExpUncRound + 1)
                str_val = strNumFormat(nu.val, valSigFigs, bLimitDims=bLimitDims)
            else:
                # string formatting
                str_val = strNumFormat(nu.val, intSigFig, bLimitDims=bLimitDims)

            # print(a.val)
            # rounding digits beyond uncertainty threshold
            nu.unc = np.int16(0.5 + nu.unc * 10 ** -intExpUncRound) * 10 ** intExpUncRound
            # string formatting
            str_unc = strNumFormat(nu.unc, intSigFig, bLimitDims=bLimitDims)
            str_unit = str(nu.unit)

        return str_val, str_unc, decExp, str_unit

def strNumFormatDec(x, decExp, suppressOuterParenthesis=False, bLimitDims=True):
    # iz števila ustvari niz, pomožna funkcija za števila oblike X.YZeW
    if suppressOuterParenthesis:
        return f'{strNumFormat(x * 10 ** (-decExp), bLimitDims=bLimitDims)} \\cdot 10^{{{decExp}}}'
    return f'\\left( {strNumFormat(x * 10 ** (-decExp), bLimitDims=bLimitDims)} \\cdot 10^{{{decExp}}} \\right)'

def strNumFormat(x, sgFg=intSigFig, decExpForced=None, suppressOuterParenthesis=False, bLimitDims=True):
    # iz števila ustvari niz
    symDec = config['printNuSymbolDec']
    bLeading0 = not config['printNuRemoveLeading0']
    floatTolerance = 10 ** (-config['printNuFloatToleranceDigits'])

    if decExpForced == None:
        decExp = getDecExponent(x)
    else:
        decExp = decExpForced
    
    # fix sig figs
    if type(sgFg) == np.ndarray:
        try:
            # pogosto je prvi element enak 0, zato privzamemo, da drugi predstavlja število mest
            sgFg = np.sort(sgFg)[1]
        except:
            # v primeru trivialnega seznama
            sgFg = sgFg[0]
    
    if decExp == None: # vedno == True?
        if type(x) in (float, int, np.float64):
            # napačne vrednosti
            if np.isnan(x):
                return config['printNuSymbolNaN']

            # negativne vrednosti pretvori v pozitivne
            strSgn = ''
            if x < 0:
                x = -x
                strSgn = '-'
            
            if x == 0: # 0 == 0.
                return '0'

            if sgFg == np.inf:
                if np.abs(x % 1) < floatTolerance * np.abs(x):
                    return f'{int(x)}'
                return f'{x}'
            else:
                def insertSeperator3Digit(strInput, bStartLeft):
                    if type(strInput) != str:
                        raise ValueError(f'Delitelje troštevčnih nizov lahko vstavimo samo v nize, ne [{type(strInput)}]')
                    if type(bStartLeft) != bool:
                        raise ValueError(f'type(bStartLeft) = {type(bStartLeft)} != bool')
                    if len(strInput) < config['printNuThresholdSeperator3Digit']:
                        return strInput
                    intDir = 2*bStartLeft - 1
                    strDir = strInput[::intDir]
                    strReturn = ''
                    for i in range(len(strDir)):
                        sym = strDir[i]
                        if not sym.isdigit():
                            raise ValueError(f'Niz [{strInput}] ni sestavljen iz števk')
                        symSep = config['printNuSymbolSeperator3Digit'] * (i != 0) * (i % 3 == 0)
                        strReturn += symSep[::intDir] + sym
                    return strReturn[::intDir]
                
                decExpLeading = getLeadingExponent(x, sgFg)
                xSgFg = int(0.5 + x * (10 ** int(sgFg - decExpLeading - 1))) # sig. števke števila ...
                strSgFg = str(xSgFg) # ... v obliki niza
                if decExpLeading >= 0: # x > 1
                    if sgFg - decExpLeading > 1:
                        strReturn = insertSeperator3Digit(strSgFg[:1+decExpLeading], False) + symDec + insertSeperator3Digit(strSgFg[1+decExpLeading:], True)
                    else:
                        strReturn = insertSeperator3Digit(strSgFg[:1+decExpLeading] + (1 + decExpLeading - sgFg) * '0', False)
                else: # x < 1
                    strReturn = insertSeperator3Digit(bLeading0 * '0', False) + symDec + insertSeperator3Digit((-1 - decExpLeading) * '0' + strSgFg, True)

                return strSgn + strReturn # dobi pravilen predznak

            # stara koda, ki ni zaokroževala
            # st = str(x).rstrip('.')
            # if not '.' in st and len(st) < sgFg:
            #     st += '.0' # natančnost števila sega čez decimalno vejico, zato jo dopiše
            # int_ = st[:]
            # if '.' in st:
            #     int_, _ = st.split('.')
            #     # exclude floats 0.XYZ
            #     if int_ != '0':
            #         if sgFg != np.inf: # končna natančnost
            #             while len(st) <= sgFg:
            #                 st += '0' # za decimalno vejico doda ustrezno število ničel
            #             if st[0] == '0': # oblike 0.XYZ
            #                 while len(st[2:].lstrip('0')) > sgFg:
            #                     st = st[:-1]
            #             if len(int_) < sgFg:
            #                 st = st[:sgFg+1]
            #         if '.' in st:
            #             _, dec_ = st.split('.')
            #             intFPError = 0
            #             for char in dec_[::-1]:
            #                 intFPError = 1 + intFPError * (char != 0)
            #                 if intFPError >= config['printNuFloatToleranceDigits']:
            #                     st = st[:-config['printNuFloatToleranceDigits']]
            #                     break
            #             st = st.rstrip('0')
            #         if st.rstrip('0')[-1] == '.':
            #             st = st.rstrip('0')[:-1]
                        
            # # trim trailing zeroes and overprecise ints
            # if int_ != '0':
            #     if len(int_) >= sgFg:
            #         st = st[:sgFg] + '0' * (len(int_) - (sgFg))
            # else:
            #     if sgFg != np.inf:
            #         idx_1st_sgFg = len(st) - len(st[2:].lstrip('0'))
            #         st = st[:idx_1st_sgFg + sgFg] + '0' * (len(int_) - (idx_1st_sgFg + sgFg))
            
            # strReturn = strSgn + strReturn # dobi pravilen predznak
            # return st
        
        elif type(x) == np.ndarray:
            if np.shape(x) != (len(x),): # mora biti vektor
                ValueError(f'ndarray must be in shape (N,), not {np.shape(x)}')

            if len(x) == 1: # trivialni vektor
                return strNumFormat(x[0], sgFg=sgFg, bLimitDims=bLimitDims)
                # return strNumFormat(x[0], bLimitDims=bLimitDims)

            st = '\\begin{bmatrix}'

            # omejitev števila prikazanih elementov s tropičjem
            if not bLimitDims or intDimLim == -1 or intDimLim > len(x):
                l = len(x)
            else:
                l = intDimLim
            bPlus1 = bLimitDims and (len(x) == intDimLim + 1)
            
            for i in range(l + bPlus1):
                x_i = x[i]
                decExp_i = getLeadingExponent(x_i, sgFg)-1
                # problematično sgFg=sgFg_i
                st += f'{strNumFormat(x_i, sgFg=decExp_i+sgFg, decExpForced=decExp, suppressOuterParenthesis=True, bLimitDims=bLimitDims)} \\\\'
            if l == intDimLim and len(x) > intDimLim + 1:
                st += f'\\vdots\\ ({len(x)-l}) \\\\'
            
            st += '\\end{bmatrix}'
            return st
        
        return x
    else:
        # raise ValueError('Izgleda, da ni vedno True')
        return strNumFormatDec(x, decExp, suppressOuterParenthesis, bLimitDims=bLimitDims)

def strUnitFixEnvironment(strUnit):
    # sets environment if already in math mode
    if strUnit[0] == '\\':
        return strUnit
    return f'\\ \\mathrm{{{strUnit}}}'

def geteExpUnitDist():
    # returns the total diffrence of exponents of base units between two complex units
    return

def conv2arr(a):
    if type(a) != np.ndarray:
        return np.array([a])
    return a

def nuStr2Arr(a):
    a = a*1+0
    a.fxt()
    # ne rab bit kle sam nikol ne veš
    return Nu(conv2arr(a.val), conv2arr(a.unc), False, a.unit)

def NuExp(a):
    # if type(a) != Nu: a = Nu(a)
    a.fxt()
    if np.average(a.unc) >= 1: raise ValueError('Uncertainty greater or equal to 1')
    return Nu(np.exp(a.val), a.unc / (1 - a.unc), True)

def powCertain(a, b):
    # exponent without uncertainty
    a *= 1
    # print(f'\npowCertain {a.val} +- {a.unc} {b}, type {a.typ}')
    # print('powCertainr', a.val ** b, np.abs(a.unc * b))
    return Nu(a.val ** b, np.abs(a.unc * b), True, a.unit * b)

def ln(a_):
    # if type(self) != Nu: self = Nu(self)
    a = copy.deepcopy(a_)
    a = Nu(1)
    if not a.unitless():
        RuntimeWarning(f'Logaritem enot [{a.unit()}] dopuščen samo pri prilagajanju')
    a.fxt(True)
    if np.average(a.unc) == 0:
        return Nu(np.log(a.val))
    return Nu(np.log(a.val), a.unc / (1 + a.unc))

def logNu(a, base=np.e):
    return ln(a) / ln(base)

def getLinFit(x_input, y_input):
    x_ = copy.deepcopy(x_input)
    y_ = copy.deepcopy(y_input)
    x_unit, y_unit = x_.unit, y_.unit
    idxs_aN = np.argwhere(~np.isnan(x_.val + x_.unc + y_.val + y_.unc)).T[0]
    # sumljiv line was here (nasledn) (zakomentiran ker je povzroču neko napako k sm jo že pozabu (mislm de neki z NaN))
    x_ = x_[idxs_aN]
    y_ = y_[idxs_aN]
    # idxs_aN = np.argwhere(~np.isnan(y_.unc)).T[0] # BUG - mrbit - ne vem zakuga j biu ta line kle
    x_ = x_[idxs_aN]
    y_ = y_[idxs_aN]

    # x_ += 0
    # y_ += 0
    
    x_val = x_.val
    x_unc = x_.unc
    y_val = y_.val
    y_unc = y_.unc

    x_range = np.max(x_val) - np.min(x_val)
    y_range = np.max(y_val) - np.min(y_val)

    # print(y_unc)

    if np.prod(y_unc == 0) == 1:
        bUncs = False
        k_val, n_val = np.polyfit(x_val, y_val, 1)
    elif np.prod(y_unc != 0) == 1:
        bUncs = True
        # print(y_val)
        # weights = np.nan_to_num(np.abs(y_unc) ** -1)
        weights = np.abs(y_unc) ** -1
        k_val, n_val = np.polyfit(x_val, y_val, 1, w=weights)
    else:
        raise ValueError('Can only fit a set of values, all with nonzero or zero uncertainty.')
    # print(k_val, n_val)
    
    y_fit = n_val + k_val * x_val
    y_fit_inv = (y_val - n_val) / k_val
    # delta_y = np.abs(y_val - y_fit) + bUncs * np.abs(y_unc)
    # kvadrati napake
    delta_y2 = (y_val - y_fit) ** 2
    delta_x2 = (x_val - y_fit_inv) ** 2

    n_unc = np.sqrt(np.average(delta_y2 + delta_x2 + bUncs * ( y_unc ** 2 + (x_range * x_unc) ** 2 )))
    k_unc = np.sqrt(np.average(delta_y2 + (k_val ** 2) * delta_x2)) / x_range

    return Nu(k_val, k_unc, unit=(y_unit - x_unit)), Nu(n_val, n_unc, unit=y_unit)

def dictToStrExponential(dic):
    st = ''
    for unit, exp in dic.items():
        st += strUnitFixEnvironment(unit)
        if exp == 1:
            continue
        st += '^{'
        if exp % 1 == 0:
            st += str(int(exp))
        else:
            st += str(exp)
        st += '}'
    return st

def lenUnitDict(dic):
    return int(np.ceil(np.sum(np.abs(list(dic.values())))))

dictUnitsBase, dictUnitsComposite, _ = getUnits()
class Nu_unit:
    def __init__(self, dic={}):
        if dic == {}:
            self.dic = {}
        else:
            self.dic = dic
        if None in self.dic:
            if self.dic[None] <= 0:
                raise ValueError(f'Numerični multiplikator enote mora biti pozitiven, ne [{self.dic[None]}]')
    
    def __len__(self):
        return lenUnitDict(self.dic)

    def __neg__(self):
        return Nu_unit(Nu_unit.negDict(self.dic))

    def __add__(self, oth):
        return Nu_unit(Nu_unit.addDicts(self.dic, oth.dic))
    
    def __sub__(self, oth):
        return Nu_unit(Nu_unit.addDicts(self.dic, (-oth).dic))
    
    def __mul__(self, fOth):
        return Nu_unit(Nu_unit.mulDict(self.dic, fOth))
    
    def addDictEntry(dic, key, val):
        # prišteje eksponent v kontekstu enot (množenje enote in enostavne (samo 1 vrsta osnovne enote) enote)
        dictReturn = copy.deepcopy(dic)
        if key == None: # multiplikator - množimo
            dictReturn[key] = dictReturn.get(key, 1) * val
            if dictReturn[key] == 1: # odstrani trivialne vnose
                dictReturn.pop(key)
        else: # eksponenti potenc - seštevamo
            dictReturn[key] = dictReturn.get(key, 0) + val
            if dictReturn[key] == 0: # odstrani trivialne vnose 
                dictReturn.pop(key)
        return dictReturn
    
    def mulDictEntry(dic, key, val):
        # primnoži eksponent v kontekstu enot (potenciranje enote z realnim numeričnim eksponentom)
        # tedaj naj bi vedno veljalo, da obstaja dictReturn[key]; sicer dobimo trivialen rezultat
        dictReturn = copy.deepcopy(dic)
        if key == None: # multiplikator - eksponentiramo
            dictReturn[key] = dictReturn.get(key, 1) ** val
            if dictReturn[key] == 1: # odstrani trivialne vnose
                dictReturn.pop(key)
        else: # eksponenti potenc - množimo
            dictReturn[key] = dictReturn.get(key, 0) * val
            if dictReturn[key] == 0: # odstrani trivialne vnose 
                dictReturn.pop(key)
        return dictReturn
    
    def negDict(dic):
        # negira slovar v kontekstu enot (obrne enoto)
        dictReturn = copy.deepcopy(dic)
        for key in dic.keys():
            if key == None: # multiplikator - obrne
                dictReturn[key] = 1 / dic[key]
            else: # potenca - negira
                dictReturn[key] = -dic[key]
        return dictReturn
    
    def addDicts(dict1, dict2):
        # sešteje slovarja v kontekstu enot (zmnoži enoti)
        dictReturn = copy.deepcopy(dict1)
        for key, val in dict2.items():
            dictReturn = Nu_unit.addDictEntry(dictReturn, key, val) # prišteje* vrednosti 2. slovarja
        return dictReturn
    
    def mulDict(dic, val):
        # celotnemu slovarju primnoži eksponent v kontekstu enot (potenciranje enote z realnim numeričnim eksponentom)
        dictReturn = copy.deepcopy(dic)
        for key in dic.keys():
            dictReturn = Nu_unit.mulDictEntry(dictReturn, key, val)
        return dictReturn

    def __str__(self):
        dictOpt = self.getOptimalUnit() # slovar, ki pove iz koliko katerih enot je sestavljena enota
        return Nu_unit.dictToStrUnit(dictOpt)
    
    def dictToStrUnit(dictUnit):
        # iz slovarja enote (lahko so sestavljene, njihovega obstoja ne preverjamo) ustvari ustrezen niz

        dictNumer = {}
        dictDenom = {}
        if dictUnit == {}: # trivialna enota
            return ''
        
        for key in dictUnit:
            if key != None: # zanimajo nas samo potence enot
                exp = dictUnit[key]
                if exp > 0:
                    dictNumer[key] = dictNumer.get(key, 0) + exp
                else:
                    dictDenom[key] = dictDenom.get(key, 0) - exp
        dictNumer = dict(sorted(dictNumer.items(), key=lambda item: item[1])) # urejeno po potencah
        strNumer = dictToStrExponential(dictNumer)
        if strNumer[:2] == '\\ ':
            strNumer = strNumer[2:]
        strNumer += (strNumer == '') * '1'
        strNumer = strNumer.replace('}\\ \\mathrm{', '')

        dictDenom = dict(sorted(dictDenom.items(), key=lambda item: item[1])) # urejeno po potencah
        if dictDenom == {}:
            return f'\\ {strNumer}'
        strDenom = dictToStrExponential(dictDenom)
        if strDenom[:2] == '\\ ':
            strDenom = strDenom[2:]

        return f'{config["printNuSymbolSeperatorUnit"]}\\frac{{{strNumer}}}{{{strDenom}}}'
        # return f'\\ \\frac{{{strNumer}}}{{{strDenom}}}'.replace('}\\ \\mathrm{', '')

    def sort(self):
        dicCopy = copy.deepcopy(self.dic) # zaradi iteracije
        self.dic = {}
        for dictUnits in (dictUnitsComposite, dictUnitsBase):
            for strUnit in dictUnits:
                for strUnitSelf, expUnitSelf in dicCopy.items():
                    if strUnit == strUnitSelf:
                        self.dic[strUnitSelf] = expUnitSelf
    
    def dictNoMult(dictInput):
        # z enote odstrani numerični faktor (multiplikator), ki ga predstavlja vnos s ključem None
        dictReturn = {}
        for key, val in dictInput.items():
            if key != None:
                dictReturn[key] = val
        return dictReturn

    def getOptimalUnit(self):
        # if config['debugPrintUnitAsDict']:
        #     return str(self.dic)
        self.sort()

        dictOpt = self.dic
        if config['printNuCompositeUnitIfExactMatch']:
            for unitComposite, dictUnitComposite in dictUnitsComposite.items():
                # if dictOpt == dictUnitComposite:
                if dictOpt == Nu_unit.dictNoMult(dictUnitComposite):
                    return strUnitFixEnvironment(dictUnitComposite)
        else: # privzeto
            # poskusi, če enota postane "manjša", če se 1 sestavljena enota izpostavi v števcu ali imenovalcu
            # za več kot 1 enoto bi blo treba def. rekurzivno funkcijo
            for strUnitComposite, dictUnitComposite in dictUnitsComposite.items():
                dic = Nu_unit.dictNoMult((self - Nu_unit(dictUnitComposite)).dic)
                dic = {**{strUnitComposite: 1}, **dic} # v primeru ekvivalence sest. enoto napiše prvo
                if lenUnitDict(dic) <= lenUnitDict(dictOpt):
                    dictOpt = dic

                dic = (self + Nu_unit(dictUnitComposite)).dic
                dic = {**{strUnitComposite: -1}, **dic} # v primeru ekvivalence sest. enoto napiše prvo
                if lenUnitDict(dic) <= lenUnitDict(dictOpt):
                    dictOpt = dic
        # strDenom = strDenom.replace('}\\ \\mathrm{', '')

        return dictOpt
    
    def getMult(dictInput):
        # vrne numerični multiplikator enote
        unitMult = 1
        for strUnit, numUnit in dictInput.items():
            if strUnit in dictUnitsComposite.keys():
                dictUnit = dictUnitsComposite[strUnit]
                if None in dictUnit.keys():
                    unitMult *= dictUnit[None] ** numUnit
        return unitMult
    
    def unitless(self):
        return self.dic == {}
    
    def __eq__(self, other):
        return type(self) == Nu_unit and type(other) == Nu_unit and self.dic == other.dic

class Nu:
    # number with uncertainty
    def __init__(self, val, unc=0.0, typ=False, unit=Nu_unit()):
        if type(val) == Nu:
            self = val # kle j mrbit ERROR
            # self.val = val.val
            # self.unc = val.unc
            # self.typ = val.typ
            # self.strDecExp = val.strDecExp
        else:
            self.val = val
            self.unc = unc
            self.typ = typ
            self.unit = unit

            if type(self.val) in [int, float, np.int32]:
                self.val = np.float64(val)
            if type(self.unc) in [int, float, np.int32]:
                self.unc = np.float64(unc)
            if self.unit == None:
                self.unit = Nu_unit()
            
            if not (type(self.val) in [np.float64, np.ndarray]):
                raise TypeError(f'1st argument ({self.val}) must be real number, not {type(self.val)}')
            if not (type(self.unc) in [np.float64, np.ndarray]):
                raise TypeError(f'2nd argument ({self.unc}) must be real number, not {type(self.unc)}')
            if type(self.typ) != bool:
                raise TypeError(f'3rd argument must be boolean, not {type(self.typ)}')
            if type(self.unit) != Nu_unit:
                raise TypeError(f'4th argument must be Nu_unit, not {type(self.unit)}')
    
    def __eq__(self, other):
        if type(other) == Nu:
            raise NotImplementedError
        return False
        # return self.val == other.val and self.unc == other.unc and self.typ == other.typ and self.unit == other.unit

    def __str__(self):
        # str_val, str_unc, decExp, str_unit = strNuFormat(self)
        # print(str_val, str_unc, decExp, str_unit)
        # if the line is: [decExp = getDecExponent(a.val)], there are errors
        
        # enote
        str_unit = str(self.unit)
        dictOptUnit = self.unit.getOptimalUnit()
        # print('dictOpt:', dictOptUnit)
        unitMult = Nu_unit.getMult(dictOptUnit)
        # print(unitMult)
        self /= unitMult

        decExp = getDecExponent(self.val, False)
        if decExp != None:
            self *= 10 ** (-decExp)
        if config['printNuTypeFix'] == 'abs':
            self += 0
        if config['printNuTypeFix'] == 'rel':
            self *= 1
        
        # detecting constants
        const = arrConstant(self.unc)
        if const != None:
            self.unc = const

        

        # precise values
        if np.sum(np.abs(self.unc)) == 0:
            # string formatting
            str_val = strNumFormat(self.val, intSigFig)
            # final formatting
            if self.typ:
                if decExp != None:
                    return f'{str_val}  \\cdot 10^{{{decExp}}}{str_unit}'.replace('.', config['printNuSymbolDec'])
                return f'{str_val} {str_unit}'.replace('.', config['printNuSymbolDec'])
            if decExp != None:
                return f'{str_val} \\cdot 10^{{{decExp}}}{str_unit}'.replace('.', config['printNuSymbolDec'])
            if str_unit == '':
                return f'{str_val}'.replace('.', config['printNuSymbolDec'])
            return f'{str_val} {str_unit}'.replace('.', config['printNuSymbolDec'])
            # return f'\\left( {str_val} \\pm {str_unc} \\right) {str_unit}'.replace('.', config['printNuSymbolDec'])
        
        # values with uncertainty
        else:
            if config['printNuSigFigsDependentOnUnc']: # privzeto True
                # uncertainty order of magnitude
                if type(self.unc) == np.ndarray:
                    idx_an = np.argwhere(~np.isnan(self.unc))
                    intExpUnc = np.floor(np.average(np.log10(np.abs(self.unc[idx_an]))))
                else:
                    intExpUnc = np.floor(np.log10(np.abs(self.unc)))
                
                intExpUncRound = intExpUnc - intSigFig + 1
                # rounding digits beyond uncertainty threshold, sign correction
                signVal = 1 - 2 * (self.val < 0) # +-1
                self.val = signVal * np.floor(0.5 + np.abs(self.val) * 10 ** -(intExpUncRound)) * 10 ** (intExpUncRound)
                # string formatting
                valSigFigs = np.int16(np.log10(np.abs(self.val)) - (intExpUncRound-1))
                str_val = strNumFormat(self.val, sgFg=valSigFigs)
            else:
                # string formatting
                str_val = strNumFormat(self.val, intSigFig)

            # print(self.val)
            # rounding digits beyond uncertainty threshold
            self.unc = np.int16(0.5 + self.unc * 10 ** -intExpUncRound) * 10 ** intExpUncRound
            # string formatting
            str_unc = strNumFormat(self.unc, intSigFig)
            
            # final formatting
            if self.typ:
                if decExp != None:
                    return f'{str_val} \\cdot \\left(1 \\pm {str_unc} \\right) \\cdot 10^{{{decExp}}}{str_unit}'.replace('.', config['printNuSymbolDec'])
                return f'{str_val} \\cdot \\left(1 \\pm {str_unc} \\right){str_unit}'.replace('.', config['printNuSymbolDec'])
            if decExp != None:
                return f'\\left( {str_val} \\pm {str_unc} \\right) \\cdot 10^{{{decExp}}}{str_unit}'.replace('.', config['printNuSymbolDec'])
            if str_unit == '':
                return f'{str_val} \\pm {str_unc}'.replace('.', config['printNuSymbolDec'])
            return f'\\left( {str_val} \\pm {str_unc} \\right) {str_unit}'.replace('.', config['printNuSymbolDec'])
    
    def __getitem__(self, slc):
        try:
            return Nu(self.val[slc], self.unc[slc], self.typ)
        except:
            return Nu(self.val[slc], self.unc, self.typ)
    
    def __len__(self):
        l1 = 1
        l2 = 1
        if type(self.val) != np.float64:
            l1 = len(self.val)
        if type(self.unc) != np.float64:
            l2 = len(self.unc)
        b = l1 > l2
        return b * l1 + (not b) * l1
    
    def unitless(self):
        return self.unit.unitless()
    
    def iszero(self):
        return np.sum(np.abs(self.val)) == 0
    
    def iszerounc(self):
        return np.sum(np.abs(self.unc)) == 0
    
    def cht(self):
        # change uncertainty type
        if self.typ:
            self.typ = False
            self.unc *= self.val
        else:
            self.typ = True
            if np.sum(np.abs(self.unc)) + np.sum(np.abs(self.val)) > 0:
                self.unc /= self.val

    def fxt(self, bool=False):
        # fixtype
        if self.typ != bool:
            self.cht()
        self.unc = np.abs(self.unc)
        
    def __iter__(self):
        self.fxt()
        if type(self.unc) != np.ndarray or len(self.unc) == 1:
            unc = self.unc
            for val in self.val:
                yield Nu(val, unc, unit=self.unit)
        else:
            for val, unc in zip(self.val, self.unc):
                yield Nu(val, unc, unit=self.unit)
    
    def __neg__(self):
        return Nu(-self.val, self.unc, self.typ, self.unit)

    def __abs__(self):
        return Nu(abs(self.val), self.unc, self.typ, self.unit)

    def __add__(self, a):
        if type(a) != Nu: a = Nu(a)
        self.fxt()
        a.fxt()
        if not (self.iszero() or a.iszero() or (self.unitless() and a.unitless()) or self.unit == a.unit):
            raise ValueError(f'Addition requires arguments have same units, not {self.unit} and {a.unit}')
        
        if self.iszero():
            unitCommon = a.unit
        else:
            unitCommon = self.unit
        return Nu(self.val + a.val, self.unc + a.unc, False, unitCommon)
    
    def __sub__(self, a):
        if type(a) != Nu: a = Nu(a)
        self.fxt()
        a.fxt()
        if not (self.iszero() or a.iszero() or (self.unitless() and a.unitless()) or self.unit == a.unit):
            raise ValueError(f'Subtraction requires arguments have same units, not {self.unit} and {a.unit}')
        
        if self.iszero():
            unitCommon = a.unit
        else:
            unitCommon = self.unit
        return Nu(self.val - a.val, self.unc + a.unc, False, unitCommon)
    
    def sum(self):
        nuReturn = Nu(0)
        for el in self:
            if not np.isnan(el.val + el.unc):
                nuReturn += el
        return nuReturn
    
    def __mul__(self, a):
        if type(a) != Nu: a = Nu(a)
        self.fxt(True)
        a.fxt(True)
        # print(self.val, self.unc, a.val, a.unc)
        # print(self.val * a.val, self.unc + a.unc)
        return Nu(self.val * a.val, self.unc + a.unc, True, self.unit + a.unit)
    
    def __rmul__(self, oth):
        return self.__mul__(oth)
    
    def __truediv__(self, a):
        if type(a) != Nu: a = Nu(a)
        self.fxt(True)
        a.fxt(True)
        return Nu(self.val / a.val, self.unc + a.unc, True, self.unit - a.unit)
    
    def __pow__(self, oth):
        if type(oth) != Nu: oth = Nu(oth)
        if not oth.unitless():
            raise ValueError('Exponent needs to be unitless')
        
        if oth.iszerounc():
            return powCertain(self, oth.val)
        
        if self.unitless():
            return NuExp(oth * ln(self))
        
        raise ValueError('Exponent value error')
        # if type(a) != Nu: a = Nu(a)
        # self.fxt(True)
        # if np.sum(np.floor(np.abs(a.val)) != np.abs(a.val)) == 0:
        #     return powCertain(self, a.val)
        # print(a)
        # # if self.val <= 0:

        # if np.sum(np.abs(self.val) - self.val) != 0:
        #     raise TypeError('Negative Base With Non-Interger Power')
        
        # if not self.unitless:
        #     raise ValueError('Exponent needs to be unitless')
        
        # # possible unit error
        # return NuExp(a * ln(self))
    
    # def Nu(d):
    #     with open(d + '.txt', 'r' , encoding='utf-8') as file:
    #         print(file.read())

class Trig:
    def sin(a):
        if type(a) != Nu: a = Nu(a)
        if not a.unitless():
            raise ValueError('Sin function argument needs to be unitless')
        a.fxt()
        return Nu(np.sin(a.val), np.abs(np.cos(a.val)*a.unc))
    
    def cos(a):
        if type(a) != Nu: a = Nu(a)
        if not a.unitless():
            raise ValueError('Cos function argument needs to be unitless')
        a.fxt()
        return Nu(np.cos(a.val), np.abs(np.sin(a.val)*a.unc))
    
    def tan(a):
        if type(a) != Nu: a = Nu(a)
        if not a.unitless():
            raise ValueError('Tan function argument needs to be unitless')
        return Trig.sin(a) / Trig.cos(a)
    
    def cot(a):
        if type(a) != Nu: a = Nu(a)
        if not a.unitless():
            raise ValueError('Cot function argument needs to be unitless')
        return Trig.cos(a) / Trig.sin(a)
    
    def asin(a):
        if type(a) != Nu: a = Nu(a)
        if not a.unitless():
            raise ValueError('Arcsin function argument needs to be unitless')
        print('Arcsin not Implemented')
        return Nu(0.0)
    
    def acos(a):
        if type(a) != Nu: a = Nu(a)
        if not a.unitless():
            raise ValueError('Arccos function argument needs to be unitless')
        print('Arccos not Implemented')
        return Nu(0.0)
    
    def atan(a):
        if type(a) != Nu: a = Nu(a)
        if not a.unitless():
            raise ValueError('Arctan function argument needs to be unitless')
        print('Arctan not Implemented')
        return Nu(0.0)
    
    def acot(a):
        if type(a) != Nu: a = Nu(a)
        if not a.unitless():
            raise ValueError('Arccot function argument needs to be unitless')
        print('Arccot not Implemented')
        return Nu(0.0)

class Stat:
    def getValid(a_or_tup):
        # returns non-NaN values of a Nu in absolute uncertainty form
        def removeInvalid(a, slc):
            if type(a.val) != np.ndarray:
                if not np.isnan(a.val):
                    return a
                else:
                    raise ValueError('The only array value is not a number.')
            val_valid = a.val[slc]
            # print(type(a.val))
            unc_valid = a.unc
            if type(a.unc) == np.ndarray:
                unc_valid = a.unc[slc]
            return Nu(val_valid, unc_valid, False, a.unit)
        
        if type(a_or_tup) == tuple:
            for a in a_or_tup:
                a.fxt()
            tup4sum = (a.val + a.unc for a in a_or_tup)
            idxs_aN = np.argwhere(~np.isnan(np.sum(tup4sum))).T[0]
            return (removeInvalid(a, idxs_aN) for a in a_or_tup)
        else:
            # a_or_tup is a
            a_or_tup.fxt()
            idxs_aN = np.argwhere(~np.isnan(a_or_tup.val + a_or_tup.unc)).T[0]
            return removeInvalid(a_or_tup, idxs_aN)
    
    def sample_avg(a, w=Nu(1.)):
        # needs valid Nu
        # print(a.val)
        # print(a.unc)
        # print(w.val)
        # print(w.unc)
        if not w.unitless():
            raise ValueError(f'Statistical weights must be unitless, not [{w.unit}]')
        if type(w.val) == np.float64 or len(w.val) == 1:
            w *= Nu(np.ones_like(a.val))
        n = Nu(np.sum(w.val), np.sum(w.unc))
        a_w = w * a
        a_w += 0
        w += 0
        a_w = Stat.getValid(a_w)
        return Nu(np.sum(a_w.val), np.sum(a_w.unc), False, a.unit) / n + 0
    
    def sample_var(a, w=Nu(1.)):
        # needs valid Nu
        if type(w.val) == np.float64 or len(w.val) == 1:
            w *= Nu(np.ones_like(a.val))
        n = Nu(np.sum(w.val), np.sum(w.unc))
        smp_avg = Stat.sample_avg(a, w)
        a_dev_sq = w * (a - smp_avg) ** 2 + 0
        a_dev_sq = Stat.getValid(a_dev_sq)
        return Nu(np.sum(a_dev_sq.val), np.sum(a_dev_sq.unc), False, a_dev_sq.unit) / (n-1) + 0
    
    def sample_std(a, w=Nu(1.)):
        # needs valid Nu
        return Stat.sample_var(a, w=Nu(1.)) ** (0.5) + 0

    def avg(a, w=Nu(1.)):
        # average
        a += 0
        a_ = Stat.getValid(a)
        if type(w.val) == np.float64 or len(w.val) == 1:
            w *= Nu(np.ones_like(a_.val))
        n = Nu(np.sum(w.val), np.sum(w.unc))
        smp_avg = Stat.sample_avg(a_, w)
        smp_std = Stat.sample_std(a_, w)
        return Nu(smp_avg.val, smp_avg.unc + ((smp_std.val + smp_std.unc) / (n.val ** 0.5)), False, smp_avg.unit)
    
    # def cnt(a):
    #     # count sample
    #     return Nu(np.count_nonzero(a.val))
    
    def var(a, w=Nu(1.)):
        # variance
        a_, w_ = Stat.getValid((a, w))
        if type(w_.val) == np.float64 or len(w_.val) == 1:
            w_ *= Nu(np.ones_like(a_.val))
        # n = Nu(np.sum(w_.val), np.sum(w_.unc))
        n = len(a_.val)
        smp_var = Stat.sample_var(a_, w_)
        var_ = (smp_var * Nu(1, 2 / np.sqrt(2 * n)))
        var_.fxt()
        return var_

    def fitlin(a, b):
        if len(a) != len(b):
            raise ValueError(f'Linear fit calculation demands data of same size, not {len(a)} and {len(b)}')
        # (k_min, _) = getLinFit(a, b, -1)
        # (k_max, _) = getLinFit(a, b, 1)

        # k_unc = (k_max - k_min) / 2
        # return Nu(np.polyfit(a.val, b.val, 1)[0], k_unc, False, b.unit - a.unit)
        return getLinFit(a, b)
    
    def sdv(a, w=Nu(1.)):
        # standard deivation
        return Stat.var(a, w) ** 0.5
    
    def max(a):
        # maximum
        if type(a.val) != np.ndarray:
            return a
        a_ = Stat.getValid(a)
        argmax = np.argmax(a_.val)
        try:
            return Nu(a_.val[argmax], a_.unc[argmax], False, a_.unit)
        except:
            return Nu(a_.val[argmax], a_.unc, False, a_.unit)
    
    def min(a):
        # minimum
        if type(a.val) != np.ndarray:
            return a
        a_ = Stat.getValid(a)
        argmin = np.argmin(a_.val)
        try:
            return Nu(a_.val[argmin], a_.unc[argmin], False, a_.unit)
        except:
            return Nu(a_.val[argmin], a_.unc, False, a_.unit)

class Tens:
    def dim(a):
        return len(nuStr2Arr(a).val)
    
    def slc(a_, b_):
        # print(b, type(b))
        a, b = copy.deepcopy(a_), copy.deepcopy(b_)
        lst = b.split(':')
        lstStrIdx = [lst[0], '', '']
        if len(lst) >= 2:
            lstStrIdx[1] = lst[1]
        if len(lst) >= 3:
            lstStrIdx[2] = lst[2]
        if len(lst) >= 4:
            raise ValueError(f'Slice [{b}] can only have 3 parameters.')
        
        listSlc = []
        for strIdx in lstStrIdx:
            intIdx = None
            if len(strIdx) > 0:
                try:
                    intIdx = int(strIdx) - 1
                except:
                    raise ValueError(f'Invalid slice index [{strIdx}] in slice [{b}].')
            listSlc.append(intIdx)

        if len(lst) == 1:
            listSlc[1] = listSlc[0] + 1
        slc = slice(*listSlc)
        a += 0
        # neki fouš printa sam vrednost je pa taprava
        return Nu(a.val[slc], a.unc[slc], False, a.unit)

    def cnc(a, b):
        if type(a) != Nu: a = Nu(a)
        if type(b) != Nu: b = Nu(b)
        if a.unit != b.unit:
            raise ValueError('Concatenation requires arguments have same units')
        # print(a.val, type(a.val))
        # print(b.val, type(b.val))
        a = nuStr2Arr(a)
        b = nuStr2Arr(b)
        return Nu(np.concatenate((a.val, b.val)), np.concatenate((a.unc, b.unc)), False, a.unit)
    
    def arange(a, b):
        if a.val % 1 + b.val % 1 > 0:
            raise ValueError('Sequence of Numbers must have Whole numbers as upper and lower bound')
        if a.val > b.val:
            raise ValueError('Sequence of Numbers must have upper bound greater or equal to lower bound')
        if a.val == b.val:
            return Nu(a.val)
        return Nu(np.arange(a.val, b.val+1))
    
    def prCartProd(paramProjIdx, listElem):
        # possible unit error
        return projectToAxis(paramProjIdx, cartesianProdFlat(listElem))

if __name__ == '__main__':
    print('Change Run Directory')