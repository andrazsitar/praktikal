
import numpy as np
import copy
from praktikal.sysdat import *
from praktikal.conf import config

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

def getDecExponent(x, bPermitDecimalSignificand=True):
    # returns logarithmically average exponent of number or ndarray
    # excluding NaN values
    x_ = copy.deepcopy(x)
    try:
        len(x_)
        idxs_aN = np.argwhere(~np.isnan(x_)).T
        # 0 len check
        if len(idxs_aN) == 0:
            return
        idxs_aN = idxs_aN[0]
        x_ = x_[idxs_aN]
    except:
        if np.isnan(x_):
            return

    exp_max = np.floor(np.log10(np.max(x_)))
    exp_min = np.floor(np.log10(np.min(x_)))
    exp_avg = 0.5 * (exp_max + exp_min)
    # rounding exp. down, so there are no 0.XYZ values
    dec_exp = (exp_avg // intExpStep) * intExpStep
    # permitting 0.XYZ values if exp. is small enough
    if bPermitDecimalSignificand:
        dec_exp *= (np.abs(dec_exp) - intExpStep != 0)
    
    if np.abs(dec_exp) >= intExpThr:
        return int(dec_exp)

def strNuFormat(nu, bLimitDims=True):
        # order of magnitude pre-formatting
        # print(f'Nu:\t{a.val}\t{a.typ*a.val*a.unc + (not a.typ)*a.unc}')
        # print('unc', a.unc)

        # if the line is: [decExp = getDecExponent(a.val)], there are errors
        decExp = getDecExponent(nu.val, False)
        if decExp != None:
            nu *= 10 ** (-decExp)
        if config['printNuTypeFix'] == 'abs':
            nu += 0
        if config['printNuTypeFix'] == 'rel':
            nu *= 1
        
        # detecting constants
        const = arrConstant(nu.unc)
        if const != None:
            nu.unc = const
        
        # precise values
        if np.sum(np.abs(nu.unc)) == 0:
            # string formatting
            str_val = strNumFormat(nu.val, np.infty, bLimitDims=bLimitDims)
            str_unit = str(nu.unit)
            return str_val, '0', decExp, str_unit
        
        # values with uncertainty
        else:
            if config['printNuSigFigsDependentOnUnc']:
                # uncertainty order of magnitude
                if type(nu.unc) == np.ndarray:
                    idx_an = np.argwhere(~np.isnan(nu.unc))
                    intExpUnc = np.floor(np.average(np.log10(nu.unc[idx_an])))
                else:
                    intExpUnc = np.floor(np.log10(nu.unc))
                
                intExpUncRound = intExpUnc - intSigFig + 1
                # rounding digits beyond uncertainty threshold
                nu.val = np.floor(0.5 + nu.val * 10 ** -(intExpUncRound - 1)) * 10 ** (intExpUncRound - 1)
                # string formatting
                str_val = strNumFormat(nu.val, np.int16(np.log10(nu.val) - intExpUncRound + 1), bLimitDims=bLimitDims)
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
    if suppressOuterParenthesis:
        return f'{strNumFormat(x * 10 ** (-decExp), bLimitDims=bLimitDims)} \\cdot 10^{{{decExp}}}'
    return f'\\left( {strNumFormat(x * 10 ** (-decExp), bLimitDims=bLimitDims)} \\cdot 10^{{{decExp}}} \\right)'

def strNumFormat(x, sgFg=intSigFig, decExpForced=None, suppressOuterParenthesis=False, bLimitDims=True):
    # seemingly always None
    if decExpForced == None:
        decExp = getDecExponent(x)
    else:
        decExp = decExpForced
    
    # fix sig figs
    if type(sgFg) == np.ndarray:
        sgFg = sgFg[0]
    
    if decExp == None:
        if type(x) in (float, int, np.float64):
            strSgn = ''
            if x < 0:
                x = -x
                strSgn = '-'
            st = str(x).rstrip('.')
            if st.lower() == 'nan':
                return config['printNuSymbolNaN']

            if not '.' in st and len(st) < sgFg:
                st += '.0'
            int_ = st[:]
            if '.' in st:
                int_, _ = st.split('.')
                # exclude floats 0.XYZ
                if int_ != '0':
                    if sgFg != np.infty:
                        while len(st) <= sgFg:
                            st += '0'
                        if st[0] == '0':
                            while len(st[2:].lstrip('0')) > sgFg:
                                st = st[:-1]
                        if len(int_) < sgFg:
                            st = st[:sgFg+1]
                    if '.' in st:
                        _, dec_ = st.split('.')
                        intFPError = 0
                        for char in dec_[::-1]:
                            intFPError = 1 + intFPError * (char != 0)
                            if intFPError >= config['printNuFloatToleranceDigits']:
                                st = st[:-config['printNuFloatToleranceDigits']]
                                break
                        st = st.rstrip('0')
                    if st.rstrip('0')[-1] == '.':
                        st = st.rstrip('0')[:-1]

                        
            # trim trailing zeroes and overprecise ints
            if int_ != '0':
                if len(int_) >= sgFg:
                    st = st[:sgFg] + '0' * (len(int_) - (sgFg))
            else:
                if sgFg != np.infty:
                    idx_1st_sgFg = len(st) - len(st[2:].lstrip('0'))
                    st = st[:idx_1st_sgFg + sgFg] + '0' * (len(int_) - (idx_1st_sgFg + sgFg))
                
            st = strSgn + st

            st.replace('.', config['printNuSymbolDec'])
            if config['printNuRemoveLeading0']:
                return st.lstrip('0')
            return st
        
        elif type(x) == np.ndarray:
            if np.shape(x) != (len(x),):
                ValueError(f'ndarray must be in shape (N,), not {np.shape(x)}')

            if len(x) == 1:
                return strNumFormat(x[0], bLimitDims=bLimitDims)

            st = '\\begin{bmatrix}'

            if not bLimitDims or intDimLim == -1 or intDimLim > len(x):
                l = len(x)
            else:
                l = intDimLim
            
            for i in range(l):
                st += f'{strNumFormat(x[i], sgFg=sgFg, decExpForced=decExp, suppressOuterParenthesis=True, bLimitDims=bLimitDims)} \\\\'
            if l == intDimLim and len(x) > intDimLim:
                st += f'\\vdots\\ ({len(x)-l}) \\\\'
            
            st += '\\end{bmatrix}'
            return st
        
        return x
    else:
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
    return Nu(conv2arr(a.val), conv2arr(a.unc), False)

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

def ln(a):
    # if type(self) != Nu: self = Nu(self)
    a.fxt(True)
    if np.average(a.unc) == 0: return Nu(np.log(a.val))
    return Nu(np.log(a.val), a.unc / (1 + a.unc))

def logNu(a, base=np.e):
    return ln(a) / ln(base)

# def getLinFit(x_, y_, bias):
#     idxs_aN = np.argwhere(~np.isnan(x_.val + x_.unc + y_.val + y_.unc)).T[0]
#     x_ = x_[idxs_aN]
#     y_ = y_[idxs_aN]

#     x_val = x_.val
#     x_unc = x_.unc
#     x_int = np.max(x_val) - np.min(x_val)
#     x_coi = (np.max(x_val) + np.min(x_val)) / 2
#     x_t = 2 * (x_val - x_coi) / x_int # od -1 do 1
#     x_bias = x_val - x_t * x_unc * bias

#     y_val = y_.val
#     y_unc = y_.unc
#     y_int = np.max(y_val) - np.min(y_val)
#     y_coi = (np.max(y_val) + np.min(y_val)) / 2
#     y_t = 2 * (y_val - y_coi) / y_int # od -1 do 1
#     y_bias = y_val + y_t * y_unc * bias

#     # some NaN-s still get through
#     idxs_aN = np.argwhere(~np.isnan(x_bias + x_bias + y_bias + y_bias)).T[0]
#     x_bias = x_bias[idxs_aN]
#     y_bias = y_bias[idxs_aN]

#     k, n = np.polyfit(x_bias, y_bias, 1)

#     return k, n

def getLinFit(x_input, y_input):
    x_ = copy.deepcopy(x_input)
    y_ = copy.deepcopy(y_input)
    x_unit, y_unit = x_.unit, y_.unit
    idxs_aN = np.argwhere(~np.isnan(x_.val + x_.unc + y_.val + y_.unc)).T[0]
    # sumljiv line was here (nasledn) (zakomentiran ker je povzroču neko napako k sm jo že pozabu (mislm de neki z NaN))
    x_ = x_[idxs_aN]
    y_ = y_[idxs_aN]
    idxs_aN = np.argwhere(~np.isnan(y_.unc)).T[0]
    x_ = x_[idxs_aN]
    y_ = y_[idxs_aN]

    # x_ += 0
    # y_ += 0
    
    x_val = x_.val
    # x_unc = x_.unc
    y_val = y_.val
    y_unc = y_.unc

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
    y_fit = n_val + k_val * x_val
    delta_y = np.abs(y_val - y_fit) + bUncs * np.abs(y_unc)

    n_unc = np.average(delta_y)
    k_unc = np.average(delta_y) / (np.max(x_val) - np.min(x_val))

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
    
    def __len__(self):
        return lenUnitDict(self.dic)

    def __str__(self):
        if config['debugPrintUnitAsDict']:
            return str(self.dic)
        if self.dic == {}:
            return ''
        self.sort()
        dicNew = self.dic
        if config['printNuCompositeUnitIfExactMatch']:
            for unitComposite, dictUnitComposite in dictUnitsComposite.items():
                if dicNew == dictUnitComposite:
                    return strUnitFixEnvironment(dictUnitComposite)
        else:
            # kle sproba če enota rata manjša če se 1 sestavljena enota izpostav v števcu alpa imenovalcu
            # za več kot 1 enoto bi blo treba def. rekurzivno funkcijo
            for strUnitComposite, dictUnitComposite in dictUnitsComposite.items():
                dic = (self - Nu_unit(dictUnitComposite)).dic
                dic = {**{strUnitComposite: 1}, **dic} # v primeru ekvivalence sest. enoto napiše prvo
                if lenUnitDict(dic) <= lenUnitDict(dicNew):
                    dicNew = dic

                dic = (self + Nu_unit(dictUnitComposite)).dic
                dic = {**{strUnitComposite: -1}, **dic} # v primeru ekvivalence sest. enoto napiše prvo
                if lenUnitDict(dic) <= lenUnitDict(dicNew):
                    dicNew = dic
        
        dictNumer = {}
        dictDenom = {}
        for key in dicNew:
            exp = dicNew[key]
            if exp > 0:
                dictNumer[key] = dictNumer.get(key, 0) + exp
            else:
                dictDenom[key] = dictDenom.get(key, 0) - exp
        dictNumer = dict(sorted(dictNumer.items(), key=lambda item: item[1]))
        strNumer = dictToStrExponential(dictNumer)
        if strNumer[:2] == '\\ ':
            strNumer = strNumer[2:]
        strNumer += (strNumer == '') * '1'
        strNumer = strNumer.replace('}\\ \\mathrm{', '')

        dictDenom = dict(sorted(dictDenom.items(), key=lambda item: item[1]))
        if dictDenom == {}:
            return f'\\ {strNumer}'
        strDenom = dictToStrExponential(dictDenom)
        if strDenom[:2] == '\\ ':
            strDenom = strDenom[2:]
        strDenom = strDenom.replace('}\\ \\mathrm{', '')

        return f'\\ \\frac{{{strNumer}}}{{{strDenom}}}'
        # return f'\\ \\frac{{{strNumer}}}{{{strDenom}}}'.replace('}\\ \\mathrm{', '')

    def sort(self):
        dicCopy = copy.deepcopy(self.dic)
        self.dic = {}
        for dictUnits in (dictUnitsComposite, dictUnitsBase):
            for strUnit in dictUnits:
                for strUnitSelf, expUnitSelf in dicCopy.items():
                    if strUnit == strUnitSelf:
                        self.dic[strUnitSelf] = expUnitSelf

    def addUnit(self, key, num):
        dic = self.dic
        dic[key] = dic.get(key, 0) + num
        if dic[key] == 0:
            dic.pop(key)
    
    def mulUnit(self, key, num):
        dic = self.dic
        dic[key] = dic.get(key, 0) * num
        # if dic[key] == 0:
        #     dic.pop(key)
    
    def unitless(self):
        return self.dic == {}
    
    def __eq__(self, other):
        return type(self) == Nu_unit and type(other) == Nu_unit and self.dic == other.dic
    
    def __neg__(self):
        a = copy.deepcopy(self)
        dic = a.dic
        for key in dic:
            dic[key] = -dic[key]
        return a

    def __add__(self, b):
        a = copy.deepcopy(self)
        for key, val in b.dic.items():
            a.addUnit(key, val)
        return a
    
    def __sub__(self, b):
        a = copy.deepcopy(self)
        for key, val in b.dic.items():
            a.addUnit(key, -val)
        return a
    
    def __mul__(self, b):
        a = copy.deepcopy(self)
        for key, _ in self.dic.items():
            a.mulUnit(key, b)
        return a

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

            if type(self.val) in [int, float]:
                self.val = np.float64(val)
            if type(self.unc) in [int, float]:
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
        decExp = getDecExponent(self.val, False)
        if decExp != None:
            self *= 10 ** (-decExp)
        if config['printNuTypeFix'] == 'abs':
            self += 0
        if config['printNuTypeFix'] == 'rel':
            self *= 1
        # print(decExp)
        
        # detecting constants
        const = arrConstant(self.unc)
        if const != None:
            self.unc = const
        
        # precise values
        if np.sum(np.abs(self.unc)) == 0:
            # string formatting
            str_val = strNumFormat(self.val, intSigFig) # kle j problem
            str_unit = str(self.unit)
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
            if config['printNuSigFigsDependentOnUnc']:
                # uncertainty order of magnitude
                if type(self.unc) == np.ndarray:
                    idx_an = np.argwhere(~np.isnan(self.unc))
                    intExpUnc = np.floor(np.average(np.log10(self.unc[idx_an])))
                else:
                    intExpUnc = np.floor(np.log10(self.unc))
                
                intExpUncRound = intExpUnc - intSigFig + 1
                # rounding digits beyond uncertainty threshold
                self.val = np.floor(0.5 + self.val * 10 ** -(intExpUncRound)) * 10 ** (intExpUncRound)
                # string formatting
                str_val = strNumFormat(self.val, np.int16(np.log10(self.val) - (intExpUncRound-1)))
            else:
                # string formatting
                str_val = strNumFormat(self.val, intSigFig)

            # print(self.val)
            # rounding digits beyond uncertainty threshold
            self.unc = np.int16(0.5 + self.unc * 10 ** -intExpUncRound) * 10 ** intExpUncRound
            # string formatting
            str_unc = strNumFormat(self.unc, intSigFig)
            str_unit = str(self.unit)

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
        self *= 1
        self += 0
        return Nu(self.val[slc], self.unc[slc], self.typ)
    
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
        return self.unit.dic == {}
    
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
    
    def __mul__(self, a):
        if type(a) != Nu: a = Nu(a)
        self.fxt(True)
        a.fxt(True)
        # print(self.val, self.unc, a.val, a.unc)
        # print(self.val * a.val, self.unc + a.unc)
        return Nu(self.val * a.val, self.unc + a.unc, True, self.unit + a.unit)
    
    def __truediv__(self, a):
        if type(a) != Nu: a = Nu(a)
        self.fxt(True)
        a.fxt(True)
        return Nu(self.val / a.val, self.unc + a.unc, True, self.unit - a.unit)
    
    def __pow__(self, a):
        if type(a) != Nu: a = Nu(a)
        if not a.unitless:
            raise ValueError('Exponent needs to be unitless')
        
        if a.iszerounc:
            return powCertain(self, a.val)
        
        if self.unitless:
            return NuExp(a * ln(self))
        
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
        if not a.unitless:
            raise ValueError('Sin function argument needs to be unitless')
        a.fxt()
        return Nu(np.sin(a.val), np.abs(np.cos(a.val)*a.unc))
    
    def cos(a):
        if type(a) != Nu: a = Nu(a)
        if not a.unitless:
            raise ValueError('Cos function argument needs to be unitless')
        a.fxt()
        return Nu(np.cos(a.val), np.abs(np.sin(a.val)*a.unc))
    
    def tan(a):
        if type(a) != Nu: a = Nu(a)
        if not a.unitless:
            raise ValueError('Tan function argument needs to be unitless')
        return Trig.sin(a) / Trig.cos(a)
    
    def cot(a):
        if type(a) != Nu: a = Nu(a)
        if not a.unitless:
            raise ValueError('Cot function argument needs to be unitless')
        return Trig.cos(a) / Trig.sin(a)
    
    def asin(a):
        if type(a) != Nu: a = Nu(a)
        if not a.unitless:
            raise ValueError('Arcsin function argument needs to be unitless')
        print('Arcsin not Implemented')
        return Nu(0.0)
    
    def acos(a):
        if type(a) != Nu: a = Nu(a)
        if not a.unitless:
            raise ValueError('Arccos function argument needs to be unitless')
        print('Arccos not Implemented')
        return Nu(0.0)
    
    def atan(a):
        if type(a) != Nu: a = Nu(a)
        if not a.unitless:
            raise ValueError('Arctan function argument needs to be unitless')
        print('Arctan not Implemented')
        return Nu(0.0)
    
    def acot(a):
        if type(a) != Nu: a = Nu(a)
        if not a.unitless:
            raise ValueError('Arccot function argument needs to be unitless')
        print('Arccot not Implemented')
        return Nu(0.0)

class Stat:
    def getValid(a):
        # returns non-NaN values of a Nu in absolute uncertainty form
        a.fxt()
        idxs_aN = np.argwhere(~np.isnan(a.val + a.unc)).T[0]
        val_valid = a.val[idxs_aN]
        # print(type(a.val))
        unc_valid = a.unc
        if type(a.unc) == np.ndarray:
            unc_valid = a.unc[idxs_aN]
        return Nu(val_valid, unc_valid, False, a.unit)
    
    def sample_avg(a):
        # needs valid Nu
        n = len(a.val)
        return Nu(np.sum(a.val), np.sum(a.unc), False, a.unit) * (1 / n) + 0
    
    def sample_var(a):
        # needs valid Nu
        n = len(a.val)
        smp_avg = Stat.sample_avg(a)
        a_dev_sq = (a - smp_avg) ** 2 + 0
        return Nu(np.sum(a_dev_sq.val), np.sum(a_dev_sq.unc), False, a_dev_sq.unit) * (1 / (n - 1)) + 0
    
    def sample_std(a):
        # needs valid Nu
        return Stat.sample_var(a) ** (0.5) + 0

    def avg(a):
        # average
        a += 0
        a_ = Stat.getValid(a)
        n = len(a_.val)
        smp_avg = Stat.sample_avg(a_)
        smp_std = Stat.sample_std(a_)
        return Nu(smp_avg.val, smp_avg.unc + ((smp_std.val + smp_std.unc) / (n ** 0.5)), False, smp_avg.unit)
    
    # def cnt(a):
    #     # count sample
    #     return Nu(np.count_nonzero(a.val))
    
    def var(a):
        # variance
        a_ = Stat.getValid(a)
        n = len(a_.val)
        smp_var = Stat.sample_var(a_)
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
    
    def sdv(a):
        # standard deivation
        return Stat.var(a) ** 0.5

class Vect:
    def dim(a):
        return len(nuStr2Arr(a).val)

    def cnc(a, b):
        if type(a) != Nu: a = Nu(a)
        if type(b) != Nu: b = Nu(b)
        if a.unit != b.unit:
            raise ValueError('Concatenation requires arguments have same units')
        # print(a.val, type(a.val))
        # print(b.val, type(b.val))
        a = nuStr2Arr(a)
        b = nuStr2Arr(b)
        return Nu(np.concatenate((a.val, b.val)), np.concatenate((a.unc, b.unc)), False)
    
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
