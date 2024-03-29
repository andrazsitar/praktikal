
import numpy as np
import os
import copy
import traceback
import time
from datetime import datetime
from praktikal.sysdat import *
from praktikal.conf import config
from praktikal.numunc import Nu, Nu_unit, Trig, Stat, Vect, ln, getUnits, strNuFormat
from praktikal.fileman import dataGet, isFloat, write, plot

setLettSpec = set((
    'alpha',
    'beta',
    'chi',
    'epsilon',
    'eta',
    'iota',
    'kappa',
    'mu',
    'nu',
    'rho',
    'tau',
    'zeta',
    'digamma',
    'varepsilon',
    'varkappa',
    'varphi',
    'varrho',
    'varsigma',
    'vartheta',
    'aleph',
    'beth',
    'daleth',
    'gimel'
))

setLettSpecCap = set((
    'delta',
    'gamma',
    'lambda',
    'omega',
    'phi',
    'pi',
    'psi',
    'sigma',
    'theta',
    'upsilon',
    'xi'
))

fExtDef = f'.{config["fileExtensionDefault"].lstrip(".")}'
str_ditto = config['latexInterpSymbolDitto']

if config['renMaster'] in (None, 'custom'):
    renConf = config['renMasterCustomMode']
else:
    renConf = sysdatconf['renMaster'][config['renMaster']]

class Ps:
    # Praktikal stack
    # https://stackoverflow.com/questions/31229962/efficient-stack-implementation-in-python#31229971
    # hranilni Ps je obrnjen, računski ni (zaradi pop-push zanke) 

    def __init__(self, lst=None):
        if lst == None:
            self.items = []
        else:
            self.items = lst[::-1]

    def isEmpty(self):
        return self.items == []

    def push(self, item):
        self.items.append(item)

    def pop(self):
        if len(self.items) == 0:
            raise ValueError(f'Stack is Empty')
        return self.items.pop()

    def peek(self):
        return self.items[-1]

    def size(self):
        return len(self.items)
    
    def __str__(self):
        st = '['
        for x in reversed(self.items):
            st += f'{x}; '
        return st.rstrip('; ') + ']'

def getFloatableStr(s):
    if not isFloat(s[0]):
        raise Exception(ValueError, 'Does not start with Digit')
    l = 0
    for i in range(1, len(s) + 1):
        if isFloat(s[:i]):
            l = i
        else:
            break
    # printcommented('gf:', s[:l - 1])
    # return s[:l].rstrip('.')
    return s[:l]

def getLxReference(st):
    if st[0:2] != '\\$':
        raise Exception(ValueError, 'Is not LaTeX $-Reference')
    for i in range(0, len(st)):
        # len('\\left[') == 6
        if st[i:i+6] == '\\left[':
            parenth = lxRFindPar(st, '\\left[', '\\right]', True)
            return st[:i], parenth
    raise Exception(SyntaxError, f'Invalid $-Reference: [{st}]')

def getLxFloatOrRef(st):
    if st[0].isdigit():
        return getFloatableStr(st)
    st1, parenth = getLxReference(st)
    return st1 + '\\left[' + parenth + '\\right]'

def isOperator(x, bGetOperandNum=False):
    if type(x) == str:
        listX = x.split('.')
        if bGetOperandNum:
            if listX[0] == 'v' and listX[1] == 'prCartProd':
                return listX[2] + 1
            if (
                x in ['+', '-', '*', '/', '^', 'log'] or
                listX[0] == 's' and listX[1] == 'fitlin' or
                listX[0] == 'v' and listX[1] in ['cnc', 'arange']
            ):
                return 2
            elif (
                x in ['~', 'abs', 'ln'] or 
                listX[0] == 't' and listX[1].lstrip('a') in ['sin', 'cos', 'tan', 'cot'] or
                listX[0] == 's' and listX[1] in ['avg', 'sdv'] or
                listX[0] == 'v' and listX[1] == 'dim'
            ):
                return 1
            return 0
    
        return (
            x in ['~', 'abs', 'ln', '+', '-', '*', '/', '^', 'log'] or
            listX[0] == 't' and listX[1].lstrip('a') in ['sin', 'cos', 'tan', 'cot'] or
            listX[0] == 's' and listX[1] in ['avg', 'sdv', 'fitlin'] or
            listX[0] == 'v' and listX[1] in ['dim', 'cnc', 'arange']
        )
    return False

def isNuArg(s):
    # checks if object can become argument of Nu()
    return isFloat(s) or ('$' in s and not '+-' in s)

def toNuArg(s, dattype='lx'):
    # converts string (floats and $refs) to Nu() argument
    if isFloat(s):
        return np.float64(s)
    if dattype == 'ps' and s[0] == '$' and not '+-' in s:
        s0 = s.split('[')
        # printcommented(dataGet(s0[0][1:], 't_dt')[s0[1][:-1]])
        return dataGet(s0[0][len('$'):], 't_dt')[s0[1][:-len(']')]]
    if dattype == 'lx' and s[0:2] == '\\$' and not '\pm' in s:
        strFilename, strKey = s.split('\\left[')
        # len('\\$') == 2
        # len('\\right]') ==
        try:
            return dataGet(strFilename[2:], 't_dt')[strKey[:-7]]
        except:
            raise KeyError(f'No variable [{strKey[:-7]}] in file [{strFilename[2:]}{config["fileExtensionDefTable"]}]')
    raise TypeError('string cannot become Nu() argument')

def getValStackElem(stack, dic):
    # gets value of stack element with pop()
    y = stack.pop()
    # printcommented('y', y)
    if type(y) == Nu:
        return y
    elif type(y) in [float, np.float64, int, np.ndarray]:
        return Nu(y)
    elif type(dic) == type(None):
        raise Exception(LookupError, 'Dictionary not given')
    # kle j pointer, ne sme bit (zaenkat je samo spremenu vrsto negotovosti)
    return dic[y][0].peek()

def evalStack(stack, dict=None, setIndep=None, key=None, dictDebugOriginal=None):
    # evaluates expression, represented by stack
    if stack.isEmpty():
        raise ValueError('Stack is Empty')
    if setIndep == None:
        setIndep = set()
        if type(dict) != type(None):
            for key in dict:
                if dict[key][1] == set():
                    setIndep.add(key)
    stackE = Ps([])
    while not stack.isEmpty():
        stackE.push(stack.pop())
        lastElem = stackE.peek()
        if ((
            stackE.size() <= 2 and isOperator(lastElem, True) == 2
        ) or (
            stackE.size() <= 1 and isOperator(lastElem, True) == 1
        )):
            if dictDebugOriginal == None:
                stackUneval = 'Alter Config to See Stack'
            else:
                stackUneval = dictDebugOriginal[key][0]
            raise SyntaxError(f'Unevalueable Stack: [{key}]: {stackUneval}')
        
        # printcommented(stackE)
        if isOperator(lastElem):
            if stackE.peek() == '~':
                stackE.pop()
                a = getValStackElem(stackE, dict)
                stackE.push(-a)
            
            if type(stackE.peek()) == str and stackE.peek() == 'abs':
                stackE.pop()
                a = getValStackElem(stackE, dict)
                stackE.push(abs(a))
            
            if type(stackE.peek()) == str and stackE.peek() == 'ln':
                stackE.pop()
                a = getValStackElem(stackE, dict)
                stackE.push(ln(a))

            if type(stackE.peek()) == str and stackE.peek() == '+':
                stackE.pop()
                b = getValStackElem(stackE, dict)
                a = getValStackElem(stackE, dict)
                stackE.push(a + b)
            
            if type(stackE.peek()) == str and stackE.peek() == '-':
                stackE.pop()
                b = getValStackElem(stackE, dict)
                a = getValStackElem(stackE, dict)
                stackE.push(a - b)
            
            if type(stackE.peek()) == str and stackE.peek() == '*':
                stackE.pop()
                b = getValStackElem(stackE, dict)
                a = getValStackElem(stackE, dict)
                stackE.push(a * b)
            
            if type(stackE.peek()) == str and stackE.peek() == '/':
                stackE.pop()
                b = getValStackElem(stackE, dict)
                a = getValStackElem(stackE, dict)
                stackE.push(a / b)
            
            if type(stackE.peek()) == str and stackE.peek() == '^':
                stackE.pop()
                b = getValStackElem(stackE, dict)
                a = getValStackElem(stackE, dict)
                stackE.push(a ** b)
            
            if type(stackE.peek()) == str and stackE.peek() == 'log':
                stackE.pop()
                a = getValStackElem(stackE, dict)
                stackE.push(ln(a))
            
            # if type(stackE.peek()) == str and stackE.peek() == 'log':
            #     stackE.pop()
            #     b = getValStackElem(stackE, dict)
            #     a = getValStackElem(stackE, dict)
            #     stackE.push(logNu(b, a))
            
            if type(stackE.peek()) == str and stackE.peek()[:2] == 't.':
                if stackE.peek()[2:] == 'sin':
                    stackE.pop()
                    a = getValStackElem(stackE, dict)
                    stackE.push(Trig.sin(a))
                    continue
                
                if stackE.peek()[2:] == 'asin':
                    stackE.pop()
                    a = getValStackElem(stackE, dict)
                    stackE.push(Trig.asin(a))
                    continue
                
                if stackE.peek()[2:] == 'cos':
                    stackE.pop()
                    a = getValStackElem(stackE, dict)
                    stackE.push(Trig.cos(a))
                    continue
                
                if stackE.peek()[2:] == 'acos':
                    stackE.pop()
                    a = getValStackElem(stackE, dict)
                    stackE.push(Trig.acos(a))
                    continue
                
                if stackE.peek()[2:] == 'tan':
                    stackE.pop()
                    a = getValStackElem(stackE, dict)
                    stackE.push(Trig.tan(a))
                    continue
                
                if stackE.peek()[2:] == 'atan':
                    stackE.pop()
                    a = getValStackElem(stackE, dict)
                    stackE.push(Trig.atan(a))
                    continue
                
                if stackE.peek()[2:] == 'cot':
                    stackE.pop()
                    a = getValStackElem(stackE, dict)
                    stackE.push(Trig.cot(a))
                    continue
                
                if stackE.peek()[2:] == 'acot':
                    stackE.pop()
                    a = getValStackElem(stackE, dict)
                    stackE.push(Trig.acot(a))
                    continue
            
            if type(stackE.peek()) == str and stackE.peek()[:2] == 's.':
                if stackE.peek()[2:] == 'avg':
                    stackE.pop()
                    a = getValStackElem(stackE, dict)
                    stackE.push(Stat.avg(a))
                    
                if type(stackE.peek()) == str and stackE.peek()[2:] == 'var':
                    stackE.pop()
                    a = getValStackElem(stackE, dict)
                    stackE.push(Stat.var(a))
                    
                if type(stackE.peek()) == str and stackE.peek()[2:] == 'fitlin':
                    stackE.pop()
                    b = getValStackElem(stackE, dict)
                    a = getValStackElem(stackE, dict)
                    try:
                        stackE.push(Stat.fitlin(a, b)[0])
                    except:
                        raise ValueError(f'Unable to fit [{a}] and [{b}] either having all NaN data points')
                    
                if type(stackE.peek()) == str and stackE.peek()[2:] == 'sdv':
                    stackE.pop()
                    a = getValStackElem(stackE, dict)
                    stackE.push(Stat.sdv(a))
        
            if type(stackE.peek()) == str and stackE.peek()[:2] == 'v.':
                if stackE.peek()[2:] == 'cnc':
                    stackE.pop()
                    b = getValStackElem(stackE, dict)
                    a = getValStackElem(stackE, dict)
                    stackE.push(Vect.cnc(a, b))

                if stackE.peek()[2:] == 'dim':
                    stackE.pop()
                    b = getValStackElem(stackE, dict)
                    a = getValStackElem(stackE, dict)
                    stackE.push(Vect.dim(a, b))
                
                if stackE.peek()[2:] == 'arange':
                    stackE.pop()
                    b = getValStackElem(stackE, dict)
                    a = getValStackElem(stackE, dict)
                    stackE.push(Vect.arange(a, b))
                
                if stackE.peek()[2:12] == 'prCartProd':
                    numElem = int(stackE.peek()[13:])
                    stackE.pop()
                    paramProjIdx = getValStackElem(stackE, dict)
                    listElem = []
                    for _ in range(numElem):
                        listElem.append(getValStackElem(stackE, dict))
                    stackE.push(Vect.prCartProd(paramProjIdx, listElem))
        
        else:
            # var is another var
            stackE.push(getValStackElem(stackE, dict))
            

    return stackE

def lxRFindPar(expr, parL, parR, dir=True):
    # dir == True -> forwards
    parNum = 0
    iParRMain = -1
    iParLMain = -1
    lenExpr = len(expr)
    lenParL = len(parL)
    lenParR = len(parR)
    if dir:
        for i in range(0, lenExpr - lenParR, 1):
            if expr[i:i + lenParL] == parL:
                iParLMain = i
                break
        
        for i in range(iParLMain, lenExpr, 1):
            if expr[i:i + lenParL] == parL:
                parNum += 1
            if expr[i:i + lenParR] == parR:
                parNum -= 1
            if parNum == 0:
                iParRMain = i
                break
    else:
        for i in range(lenExpr - lenParR, -1, -1):
            if expr[i:i + lenParR] == parR:
                iParRMain = i
                break
        
        for i in range(iParRMain, -1, -1):
            if expr[i:i + lenParR] == parR:
                parNum += 1
            if expr[i:i + lenParL] == parL:
                parNum -= 1
            if parNum == 0:
                iParLMain = i
                break
    
    if iParLMain == -1 or iParRMain == -1:
        # printcommented(iParLMain, iParRMain)
        raise Exception(SyntaxError, "Parentheses don't have valid pairs.")

    return expr[iParLMain + lenParL: iParRMain]

def lxRGetOpsShift(expr, i0, dir=True):
    # skips parentheses
    # lenE = len(expr)
    lenE = i0
    if dir:
        raise Exception(NotImplementedError, 'Forward is not yet implemented')
    else:
        # printcommented('OpsShift', len(expr), i0)
        # if len(expr) == 0 and i0 == -1:
        #     return - 1

        if expr[i0] == '}':
            return i0 - (lenE + len(lxRFindPar(expr[:i0 + 1], '{', '}', False)) + 1)
        
        if i0 >= 6 and expr[i0-6:i0+1] == '\\right)':
            return i0 - (lenE + len(lxRFindPar(expr[:i0 + 1], '\\left(', '\\right)', False)) + 12)
        
        if expr[i0] == ']':
            if i0 >= 6 and expr[i0-6:i0+1] == '\\right]':
                return i0 - (lenE + len(lxRFindPar(expr[:i0 + 1], '\\left[', '\\right]', False)) + 12)
            return i0 - (lenE + len(lxRFindPar(expr[:i0], '[', ']', False)) + 1)
        
        if i0 >= 6 and expr[i0-6:i0+1] == '\\right|':
            return i0 - (lenE + len(lxRFindPar(expr[:i0 + 1], '\\left|', '\\right|', False)) + 12)
        
        if i0 >= 6 and expr[i0-6:i0+1] == '\\right\\rangle':
            return i0 - (lenE + len(lxRFindPar(expr[:i0 + 1], '\\left\\langle', '\\right\\rangle', False)) + 12)
        
        return -1

def strToStackOperatorMap(op, dattype='lx'):
    if dattype != 'lx':
        raise Exception(NotImplementedError)
    if dattype == 'lx':
        if op == '\\cdot':
            return '*'
        if op == '\\oplus':
            return config['latexInterpFuncOplus']
        else:
            return op

def strToStackInfix(expr, stack0, varSet0, lstOperators, dattype='lx', reverse=False):
    # converts praktial PS or LaTeX string to praktial PS stack-set pair
    # function appends data onto existing stack-set pair
    # function returns True if successful
    if not reverse or dattype != 'lx':
        raise NotImplementedError
    i = len(expr) - 1

    # čudna zadeva - max pa tud lenOper je narobe (če so operatorji različnih dolžin)
    lenOper = len(max(lstOperators, key=len))

    while i >= 0:
        # printcommented(f'{i}\t{expr}')
        if expr[i:i+lenOper] in lstOperators:
            stack0.push(strToStackOperatorMap(expr[i:i+lenOper]))
            # printcommented(f'[264]\t{expr[:i]}\t{expr[i+lenOper:]}')
            strToStack(expr[i+lenOper:], stack0, varSet0, dattype, reverse)
            if i > 0:
                strToStack(expr[:i], stack0, varSet0, dattype, reverse)
                return True
            # only for + and -
            stack0.push(Nu(0))
            return True
        i += lxRGetOpsShift(expr, i, False)

def strToStack(expr, stack0=Ps, varSet0=set(), dattype='lx', reverse=True, unit=Nu_unit()):
    # converts [praktial PS or] LaTeX string to praktial PS stack-set pair
    # function appends data onto existing stack-set pair
    if not unit.unitless():
        stack0.push('*')
        stack0.push(Nu(1, 0, unit=unit))

    if type(expr) != str:
        raise TypeError(f'Expression is not type {str}, instead: {type(expr)}')
    if dattype == 'ps':
        DeprecationWarning
        if expr[0] == '[' and expr[-1] == ']':
            listExpr = expr[1:-1].split(';')
        else:
            listExpr = expr.split(';')
        # printcommented('stack0', stack0)
        if reverse == True:
            listExpr = reversed(listExpr)
        for x in listExpr:
            x = x.strip(' ')
            if isNuArg(x):
                a = Nu(toNuArg(x))
            elif '+-' in x:
                b = x.split('+-')
                if '(' in x:
                    bl = toNuArg(b[0].rstrip('1 ').rstrip('*('))
                    # 2*strip ker od imena odreže 1-ice
                    br = toNuArg(b[1].strip(' )'))
                    boolType = True
                else:
                    bl = toNuArg(b[0].rstrip(' '))
                    br = toNuArg(b[1].lstrip(' '))
                    boolType = False
                a = Nu(bl, br, boolType)
            else:
                a = str(x)
                if not isOperator(a):
                    varSet0.add(a)
            stack0.push(a)
        # printcommented('stack0', stack0)
        return
    if dattype == 'lx':
        # only implemented in reverse
        if not reverse:
            raise NotImplementedError
        
        # reads string from right to left
        # idxMulWODot is the rightmost str index of the start of a variable, where 2 variables are written side-by-side without any operator, which indicates multiplication (see end of this branch)
        idxMulWODot = 0
        
        if len(expr) == 0:
            return

        if expr[0] == '{':
            a = lxRFindPar(expr, '{', '}', True)
            idxMulWODot = len(a) + 2
            if idxMulWODot == len(expr):
                strToStack(a, stack0, varSet0, dattype, reverse)
                return
        
        if expr[0] == '\\':
            if expr[1:6] == 'left(':
                a = lxRFindPar(expr, '\\left(', '\\right)', True)
                # len('\\left(\\right)') == 13
                idxMulWODot = len(a) + 13
                if idxMulWODot == len(expr):
                    strToStack(a, stack0, varSet0, dattype, reverse)
                    return
            
            if expr[1:6] == 'left\\langle':
                a = lxRFindPar(expr, '\\left\\langle', '\\right\\rangle', True)
                # len('\\left\\langle\\right\\rangle') == 25
                idxMulWODot = len(a) + 25
                if idxMulWODot == len(expr):
                    stack0.push(config['latexInterpFuncAngle'])
                    strToStack(a, stack0, varSet0, dattype, reverse)
                    return
            
            if expr[1:6] == 'left|':
                a = lxRFindPar(expr, '\\left|', '\\right|', True)
                # len('\\left|\\right|') == 13
                idxMulWODot = len(a) + 13
                if idxMulWODot == len(expr):
                    stack0.push('abs')
                    strToStack(a, stack0, varSet0, dattype, reverse)
                    return
            
            if expr[1:8] in ('mathrm{', 'textrm{'):
                lenStrFunc = 0
                lenStrParamSubscript = 0
                lenStrParamSuperscript = 0
                lenStrParams = 0

                exprShifted = expr[:]
                # printcommented('mrm', expr[idxMulWODot:], expr)
                strFunc = lxRFindPar(exprShifted, '{', '}', True)
                # len('\\mathrm{}') == 9
                if strFunc != '':
                    lenStrFunc = 9 + len(strFunc)
                    exprShifted = exprShifted[lenStrFunc:]
                else:
                    raise SyntaxError(f"\\mathrm and \\textrm need name of function")
                
                if exprShifted[0] == '_':
                    if exprShifted[1] != '{':
                        raise SyntaxError(f'Expression {expr} needs "{{}}" after "_".')
                    strParamSubscript = lxRFindPar(exprShifted, '{', '}', True)
                    # len('_{}') == 3
                    if strParamSubscript != '':
                        lenStrParamSubscript = 3 + len(strParamSubscript)
                        exprShifted = exprShifted[lenStrParamSubscript:]
                    else:
                        raise SyntaxError(f"Function {strFunc} has empty Subscript.")
                
                if exprShifted[:2] == '^{':
                    strParamSuperscript = lxRFindPar(exprShifted, '{', '}', True)
                    # len('_{}') == 3
                    if strParamSuperscript != '':
                        lenStrParamSuperscript = 3 + len(strParamSuperscript)
                        exprShifted = exprShifted[lenStrParamSuperscript:]
                    else:
                        raise SyntaxError(f"Function {strFunc} has empty Superscript.")

                strParams = lxRFindPar(expr, '\\left(', '\\right)', True)
                # len('\\left(\\right)') == 13
                if strParams != '':
                    lenStrParams = 13 + len(strParams)
                    listParamsComma = strParams.split(',')
                    listParamsSemicolon = strParams.split(';')
                else:
                    raise SyntaxError(f"Function {strFunc} needs parameters inside ()")
                
                idxMulWODot = lenStrFunc + lenStrParamSubscript + lenStrParamSuperscript + lenStrParams
                if idxMulWODot == len(expr):
                    if strFunc == 'fitlin':
                        numParams = len(listParamsSemicolon)
                        if numParams != 2:
                            raise SyntaxError(f'Function [{strFunc}] needs 2 parameters, not {numParams}: {listParamsSemicolon}')
                        stack0.push('s.fitlin')
                        strToStack(listParamsSemicolon[1], stack0, varSet0, dattype, reverse)
                        strToStack(listParamsSemicolon[0], stack0, varSet0, dattype, reverse)
                        return
                    
                    if strFunc == 'pr':
                        if strParamSuperscript == '\\times':
                            stack0.push(f'v.prCartProd.{len(listParamsComma)}')
                            strToStack(strParamSubscript, stack0, varSet0, dattype, reverse)
                            for param in listParamsComma:
                                strToStack(param, stack0, varSet0, dattype, reverse)
                            return
                        raise SyntaxError(f"Invalid Projection: pr_{{{strParamSubscript}}}^{{{strParamSuperscript}}}")
                    
                    raise SyntaxError(f"'{strFunc}()' is not a valid function")
            
            if expr[1:8] == 'mathbb{':
                # printcommented('mrm', expr[idxMulWODot:], expr)
                parenth = lxRFindPar(expr, '{', '}', True)
                # len('\\mathbb{}') == 9
                expr_params = expr[len(parenth) + 9:]
                parenth_subscript = ''
                parenth_superscript = ''
                
                if parenth == 'Z':
                    if len(expr_params) > 2 and expr_params[0] == '_':
                        if expr_params[1] != '{':
                            raise SyntaxError(f'Expression {expr} needs "{{}}" after "_".')
                        parenth_subscript = lxRFindPar(expr_params, '{', '}', True)
                        expr_params = expr_params[len(parenth_subscript)+3:]
                    else:
                        SyntaxError(f'Invalid Expression: {expr}')
                
                if parenth in ('N', 'Z'):
                    if len(expr_params) > 2 and expr_params[:2] == '^{':
                        parenth_superscript = lxRFindPar(expr_params, '{', '}', True)
                    else:
                        SyntaxError(f'Invalid Expression: {expr}')
                else:
                    SyntaxError(f'Invalid Expression: {expr}')
                
                # len('\\mathbb{}') == 9
                # len('_{}') == 3
                # len('^{}') == 3
                idxMulWODot = len(parenth) + len(parenth_subscript) + len(parenth_superscript) + 12 + 3*(parenth == 'Z')
                if idxMulWODot == len(expr):
                    if parenth == 'N':
                        parenth_subscript = '1'
                    stack0.push('v.arange')
                    strToStack(parenth_superscript, stack0, varSet0, dattype, reverse)
                    strToStack(parenth_subscript, stack0, varSet0, dattype, reverse)
                    return

            if expr[1:5] == 'frac':
                # printcommented('frac', idxMulWODot, expr)
                a = lxRFindPar(expr, '{', '}', True)
                b = lxRFindPar(expr[len(a) + 7:], '{', '}', True)
                # len('\\frac{}') == 7
                # len('\\frac{}{}') == 9
                idxMulWODot = len(a) + len(b) + 9
                # printcommented('postfrac', expr[idxMulWODot:])
                if idxMulWODot == len(expr):
                    stack0.push('/')
                    strToStack(b, stack0, varSet0, dattype, reverse)
                    strToStack(a, stack0, varSet0, dattype, reverse)
                    return
            
            if expr[1:5] == 'sqrt':
                if expr[5:11] == '\\left[':
                    b = lxRFindPar(expr, '\\left[', '\\right]', True)
                    a = lxRFindPar(expr[len(b) + 11:], '{', '}', True)
                    # len('\\sqrt[]{}') == 9
                    idxMulWODot = len(a) + len(b) + 20
                    if idxMulWODot == len(expr):
                        stack0.push('^')
                        stack0.push('/')
                        strToStack(b, stack0, varSet0, dattype, reverse)
                        stack0.push(Nu(1))
                        strToStack(a, stack0, varSet0, dattype, reverse)
                        return
                a = lxRFindPar(expr, '{', '}', True)
                # len('\\sqrt{}') == 7
                idxMulWODot = len(a) + 7
                if idxMulWODot == len(expr):
                    stack0.push('^')
                    stack0.push(Nu(0.5))
                    strToStack(a, stack0, varSet0, dattype, reverse)
                    return
            
            if expr[1:4] == 'log':
                if expr[4] == '_':
                    if expr[5] != '{':
                        raise SyntaxError(f'Expression {expr} needs "{{}}" after "_".')
                    NotImplementedError('Based Logs not Implemented')
                    # b = lxRFindPar(expr, '{', '}', True)
                    # a = lxRFindPar(expr, '\\left(', '\\right)', True)
                    # # len('\\log_{}') == 7
                    # # len('\\log_{}\\left(\\right)') == 20
                    # idxMulWODot = len(a) + len(b) + 20 + 'd'
                    # if idxMulWODot == len(expr):
                    #     stack0.push('^')
                    #     stack0.push('/')
                    #     strToStack(b, stack0, varSet0, dattype, reverse)
                    #     stack0.push(Nu(1))
                    #     strToStack(a, stack0, varSet0, dattype, reverse)
                    #     return
                a = lxRFindPar(expr, '\\left(', '\\right)', True)
                # len('\\log\\left(\\right)') == 17
                idxMulWODot = len(a) + 17
                if idxMulWODot == len(expr):
                    stack0.push('ln')
                    strToStack(a, stack0, varSet0, dattype, reverse)
                    return

            if expr[1:11] == 'derivative':
                # len('derivative') == 10
                a = lxRFindPar(expr, '{', '}', True)
                b = lxRFindPar(expr[len(a) + 13:], '{', '}', True)
                # len('\\derivative{}') == 13
                # len('\\derivative{}{}') == 15
                idxMulWODot = len(a) + len(b) + 15
                if idxMulWODot == len(expr):
                    stack0.push('s.fitlin')
                    strToStack(a, stack0, varSet0, dattype, reverse)
                    strToStack(b, stack0, varSet0, dattype, reverse)
                    return
            

            if len(expr) == 2 and expr[1] == '#':
                a = lxRFindPar(expr, '\\left(', '\\right)', True)
                # len('\\#\\left(\\right)') == 15
                idxMulWODot = len(a) + 15
                if idxMulWODot == len(expr):
                    stack0.push('v.dim')
                    strToStack(a, stack0, varSet0, dattype, reverse)
                    return
            
            if len(expr) >= 4:
                bTrigInverse = False
                idxTrig = 1
                # if expr[1] == 'a':
                #     bTrigInverse = True
                #     idxTrig = 2
                
                if expr[1:4] == 'arc':
                    bTrigInverse = True
                    idxTrig = 4
                
                if expr[idxTrig:idxTrig+3] == 'sin':
                    # len('\\abc\\left(\\right)') == 17
                    lenTrig = 17
                    idxTrig += 3
                    if expr[idxTrig:idxTrig+5] == '^{-1}':
                        bTrigInverse = True
                        lenTrig += 5
                        idxTrig += 5
                    if expr[idxTrig:idxTrig+6] != '\\left(':
                        raise SyntaxError('Trig functions need connected parentesis (-1st power is permitted)')
                    a = lxRFindPar(expr[idxTrig:], '\\left(', '\\right)', True)
                    idxMulWODot = len(a) + lenTrig
                    if idxMulWODot == len(expr):
                        if bTrigInverse:
                            stack0.push('t.asin')
                        else:
                            stack0.push('t.sin')
                        strToStack(a, stack0, varSet0, dattype, reverse)
                        return
                
                if expr[idxTrig:idxTrig+3] == 'cos':
                    # len('\\abc\\left(\\right)') == 17
                    lenTrig = 17
                    idxTrig += 3
                    if expr[idxTrig:idxTrig+5] == '^{-1}':
                        bTrigInverse = True
                        lenTrig += 5
                        idxTrig += 5
                    if expr[idxTrig:idxTrig+6] != '\\left(':
                        raise SyntaxError('Trig functions need connected parentesis (-1st power is permitted)')
                    a = lxRFindPar(expr[idxTrig:], '\\left(', '\\right)', True)
                    idxMulWODot = len(a) + lenTrig
                    if idxMulWODot == len(expr):
                        if bTrigInverse:
                            stack0.push('t.acos')
                        else:
                            stack0.push('t.cos')
                        strToStack(a, stack0, varSet0, dattype, reverse)
                        return
                
                if expr[idxTrig:idxTrig+3] == 'tan':
                    # len('\\abc\\left(\\right)') == 17
                    lenTrig = 17
                    idxTrig += 3
                    if expr[idxTrig:idxTrig+5] == '^{-1}':
                        bTrigInverse = True
                        lenTrig += 5
                        idxTrig += 5
                    if expr[idxTrig:idxTrig+6] != '\\left(':
                        raise SyntaxError('Trig functions need connected parentesis (-1st power is permitted)')
                    a = lxRFindPar(expr[idxTrig:], '\\left(', '\\right)', True)
                    idxMulWODot = len(a) + lenTrig
                    if idxMulWODot == len(expr):
                        if bTrigInverse:
                            stack0.push('t.atan')
                        else:
                            stack0.push('t.tan')
                        strToStack(a, stack0, varSet0, dattype, reverse)
                        return
                
                if expr[idxTrig:idxTrig+3] == 'cot':
                    # len('\\abc\\left(\\right)') == 17
                    lenTrig = 17
                    idxTrig += 3
                    if expr[idxTrig:idxTrig+5] == '^{-1}':
                        bTrigInverse = True
                        lenTrig += 5
                        idxTrig += 5
                    if expr[idxTrig:idxTrig+6] != '\\left(':
                        raise SyntaxError('Trig functions need connected parentesis (-1st power is permitted)')
                    a = lxRFindPar(expr[idxTrig:], '\\left(', '\\right)', True)
                    idxMulWODot = len(a) + lenTrig
                    if idxMulWODot == len(expr):
                        if bTrigInverse:
                            stack0.push('t.acot')
                        else:
                            stack0.push('t.cot')
                        strToStack(a, stack0, varSet0, dattype, reverse)
                        return

            if expr[1:9] == 'overline':
                a = lxRFindPar(expr, '{', '}', True)
                # len('\\overline{}') == 11
                idxMulWODot = len(a) + 11
                if idxMulWODot == len(expr):
                    stack0.push(config['latexInterpFuncOverline'])
                    strToStack(a, stack0, varSet0, dattype, reverse)
                    return
            
            if expr[1:7] == 'sigma_':
                if expr[7] != '{':
                    raise SyntaxError(f'Expression {expr} needs "{{}}" after "_".')
                a = lxRFindPar(expr, '{', '}', True)
                # len('\\sigma_{})') == 9
                idxMulWODot = len(a) + 9
                if idxMulWODot == len(expr):
                    stack0.push(config['latexInterpFuncSigma'])
                    strToStack(a, stack0, varSet0, dattype, reverse)
                    return
                # zna probleme delat, nevem
                # # len('^{2}') == 4
                # if expr[idxMulWODot:idxMulWODot+4] == '^{2}':
                #     idxMulWODot += 4
                #     if idxMulWODot == len(expr):
                #         stack0.push('s.var')
                #         strToStack(a, stack0, varSet0, dattype, reverse)
                #         return

        # expr is not parentheses or function with parentheses

        if strToStackInfix(expr, stack0, varSet0, ['\\oplus'], 'lx', True):
            return

        if strToStackInfix(expr, stack0, varSet0, ['+', '-'], 'lx', True):
            return
        
        if strToStackInfix(expr, stack0, varSet0, ['\\cdot'], 'lx', True):
            return

        if expr[0].isdigit() or expr[:2] == '\\$':
            a = getLxFloatOrRef(expr)
            idxMulWODot = len(a)
            
            if a == expr:
                stack0.push(Nu(toNuArg(expr)))
                return
            if expr[idxMulWODot:idxMulWODot+3] == '\\pm':
                b = getLxFloatOrRef(expr[idxMulWODot+3:])
                if idxMulWODot + len(b) + 3 == len(expr):
                    stack0.push(Nu(toNuArg(a, 'lx'), toNuArg(b, 'lx')))
                    return
        
        if idxMulWODot == 0:
            idxMulWODot = 1
            if expr[0] == '\\':
                for x in setLettSpec:
                    if expr[1:1+len(x)] == x:
                        idxMulWODot = 1 + len(x)
                for x in setLettSpecCap:
                    # if expr[1:1+len(x)] == x:
                    if expr[1:1+len(x)].capitalize() == x.capitalize():
                        idxMulWODot = 1 + len(x)
            expr_tr = expr[idxMulWODot:]
            boolFoundLetterTrail = True
            while boolFoundLetterTrail:
                boolFoundLetterTrail = False
                if len(expr_tr) >= 1 and expr_tr[0] == "'":
                    boolFoundLetterTrail = True
                    idxMulWODot += 1
                    expr_tr = expr[idxMulWODot:]
                if len(expr_tr) >= 1 and expr_tr[0] == '_':
                    if expr_tr[1] != '{':
                        raise SyntaxError(f'Expression {expr} needs "{{}}" after "_".')
                    boolFoundLetterTrail = True
                    a = lxRFindPar(expr_tr, '{', '}', True)
                    lenA = len(a)
                    if lenA == 0:
                        raise SyntaxError(f'{expr[:idxMulWODot+3]} has empty index')
                    idxMulWODot += lenA + 3
                    expr_tr = expr[idxMulWODot:]
            if idxMulWODot == len(expr):
                stack0.push(expr)
                varSet0.add(expr[:idxMulWODot])
                return
        # expr is not variable

        if expr[idxMulWODot] == '^':
            a = expr[:idxMulWODot]
            if '{' in expr[idxMulWODot+1:]:
                b = lxRFindPar(expr[idxMulWODot+1:], '{', '}', True)
                idxMulWODot += 3 + len(b)
            else:
                b = expr[idxMulWODot+1:]
                # print('DEBUG ERROR: ^ WO {}')
                raise SyntaxError(f'Expression {expr} needs "{{}}" after "^".')
                # idxMulWODot not needed
            if idxMulWODot == len(expr):
                stack0.push('^')
                strToStack(b, stack0, varSet0, dattype, reverse)
                strToStack(a, stack0, varSet0, dattype, reverse)
                return
        
        stack0.push('*')
        strToStack(expr[idxMulWODot:], stack0, varSet0, dattype, reverse)
        strToStack(expr[:idxMulWODot], stack0, varSet0, dattype, reverse)
        return

def strToUnitExponentNum(expr):
    # permits trailing data
    len_buffer = 0
    if expr[0] == '{':
        str_exp = lxRFindPar(expr, '{', '}', True)
        # TODO: še floate (tud ulomke)
        exp, _ = strToUnitExponentNum(str_exp)
        len_buffer = 3 + len(str_exp)
    else:
        try:
            exp = float(expr)
        except:
            if len(expr) >= 7 and '\\frac' in expr:
                strNumer = lxRFindPar(expr, '{', '}', True)
                strDenom = lxRFindPar(expr[len(strNumer) + 7:], '{', '}', True)
                exp = float(strNumer) / float(strDenom)
            else:
                raise ValueError(f'Invalid expression: {expr}')
                
    return exp, len_buffer

def strToUnit(expr):
    # dela za 1. potence brez ulomkov
    _, dictUnitsComposite, dictUnitsLen = getUnits()
    if type(expr) != str:
        raise ValueError(f'strToUnit converts {str}, not {type(expr)}')
    if len(expr) >= 5 and expr[:5] == '\\frac':
        strNumer = lxRFindPar(expr, '{', '}', True)
        strDenom = lxRFindPar(expr[len(strNumer) + 7:], '{', '}', True)
        unitNumer = strToUnit(strNumer)
        unitDenom = strToUnit(strDenom)
        return unitNumer - unitDenom
    unit = Nu_unit()
    str_r = expr[:]
    str_r_last = str_r[:]
    while len(str_r) > 0:
        if str_r == '1':
            str_r = ''
        else:
            for length, setUnits in dictUnitsLen.items():
                str_unit = str_r[:length]
                exp = 1.0
                # printcommented(units[length])
                if len(str_r) >= length and str_unit in setUnits:
                    len_buffer = 0
                    if len(str_r) >= length + 2 and str_r[length] == '^':
                        exp, len_buffer = strToUnitExponentNum(str_r[length + 1:])
                    if str_unit in dictUnitsComposite.keys():
                        dictUnitComposite = dictUnitsComposite[str_unit]
                        for str_unit_base in dictUnitComposite:
                            unit.addUnit(str_unit_base, exp * dictUnitComposite[str_unit_base])
                    else:
                        unit.addUnit(str_unit, exp)
                    str_r = str_r[length + len_buffer:]
                    break
            if str_r_last == str_r:
                raise ValueError(f'Invalid unit: [{expr}]')
            str_r_last = str_r[:]
    return unit

def dictStrToDictStack(dic, dattype='lx', reverse=False):
    # converts values of Dictionary from string to stack, see strToStack()
    # DeprecationWarning - idk zakva j blo to kle k build() kliče
    eqs = {}
    eqs['\\pi'] = (Ps([Nu(np.pi)]), set())
    eqs['e'] = (Ps([Nu(np.e)]), set())
    eqs['g'] = (Ps([Nu(9.81, 0.005, unit=Nu_unit({'m':1, 's':-2}))]), set())
    # eqs['c'] = (Ps([Nu(299792458, 1)]), set())
    bErrorBSInVarSet = False
    for key in dic:
        strEqn, unit = dic[key]
        unit = strToUnit(unit)
        # strEqn = dic[key]
        eqs[key] = (Ps([]), set())
        stack = Ps([])
        varSet = set()
        strToStack(strEqn, stack, varSet, dattype, reverse, unit)
        eqs[key] = (stack, varSet)
        if '\\' in varSet or '\\\\' in varSet:
            bErrorBSInVarSet = True
    
    # debug code
    eqsDebugC = None
    if config['debugRememberStack']:
        eqsDebugC = copy.deepcopy(eqs)
    
    if config['debugPrintStack']:
        for key in eqs:
            var = eqs[key][0].peek()
            var += 0
            print(f'{key}\t\t{var.val}\t\t+-{var.unc}\t\t{eqs[key][1]}')
            # printcommented(f'DEBUG1:\t{key}')
            # printcommented(f'DEBUG2:\t{eqs[key][0].peek().unit}')
            # printcommented(f'DEBUG3:\t{eqs[key][1]}')
    
    # error detection
    if bErrorBSInVarSet:
        raise SyntaxError(f'\\ Detected as Variable in [{key}]')

    return (eqs, eqsDebugC)

def stackDictGet(filename, dattype='e_lx', encod='utf-8', reverse=False):
    # returns Praktikal PS Dictionary
    DeprecationWarning
    if dattype[:2] != 'e_':
        raise TypeError(f'Unsupported Data Type: {dattype}')
    if '.' in filename:
        filen = filename
    else:
        filen = filename + fExtDef
    dictEqsRaw = dataGet(filen, dattype, encod)
    if dattype[2:4] in ['ps', 'lx']:
        # praktikal PostScript or LaTeX string
        (a, aDebug) = dictStrToDictStack(dictEqsRaw, dattype[2:4], reverse)
        # printcommented('dddd\t', a)
        return a, aDebug
    raise TypeError(f'Unsupported Data Type: {dattype}')

def resultGet(filen, dattype='e_lx', encod='utf-8'):
    DeprecationWarning
    # formerly stackDictGetEval 
    # returns evaluated PS Dictionary
    if dattype[:2] != 'e_' or dattype[2:4] not in ['ps', 'lx']:
        raise Exception(TypeError, f'Unsupported Data Type: {dattype}')
    if '.' in filen:
        filename = filen
    else:
        filename = filen + fExtDef
    
    dictEqs0, dictEqs0Debug = stackDictGet(filename, dattype, encod, True)
    setVarsAll = set(dictEqs0.keys())
    setVarsIndep = set()
    dictEqs = dict(dictEqs0)
    # printStackDictcommented(dictEqs, '')
    while setVarsIndep != setVarsAll:
        bSetVarsIndepChanged = False
        # -----------------------
        # -----------------------
        for key in dictEqs:
            # printcommented(f'478 Stack:\t\t{dictEqs[key][0]}\nSet:\t\t{dictEqs[key][1]}')
            if dictEqs[key][1] == set() and dictEqs[key][0].size() == 1:
                setVarsIndep.add(key)
            elif dictEqs[key][1] <= setVarsIndep:
                if dictEqs[key][0] == Ps():
                    return ValueError(f'Stack [{key}] is empty')
                res = evalStack(dictEqs[key][0], dictEqs, setVarsIndep, key, dictEqs0Debug)
                bSetVarsIndepChanged = True
                dictEqs[key] = (res, set())
        if bSetVarsIndepChanged == False and setVarsIndep != setVarsAll:
            raise RecursionError(f'Not all Equations are Solvable:\t{setVarsAll-setVarsIndep}')
    dictEqs.pop('\\pi', None)
    dictEqs.pop('e', None)
    dictEqs.pop('g', None)
    # dictEqs.pop('c', None)
    if config['wEqsKeepOther']:
        lines_ctxt = dataGet(filename, 'c_lx', encod)
        eqs_w_txt = {}
        bEqs = False
        idxDictOth = 0
        for ty, st in lines_ctxt:
            if st == '\\end{eqnarray*}':
                bEqs = False
            if bEqs:
                if ty == 'eqt':
                    key0, _ = st.split('&=&')
                    key = key0.replace(' ', '').replace('\t', '')
                    # printcommented(key)
                    # eqs_w_txt.append(f'{key0}&=& {str(dictEqs[key][0])[1:-1]} \\nonumber\\\\')
                    eqs_w_txt[key] = dictEqs[key][0], set()
                    continue
                # eqs_w_txt.append(st)
                eqs_w_txt[f'$str_{idxDictOth}'] = st, set()
                idxDictOth += 1
            if st == '\\begin{eqnarray*}':
                bEqs = True
        return eqs_w_txt
    return dictEqs

def buildFunc(flInRaw, flOutRaw):
    # fix file name
    if '.' in flInRaw:
        flIn = flInRaw
    else:
        flIn = flInRaw + fExtDef
    if '.' in flOutRaw:
        flOut = flOutRaw
    else:
        flOut = flOutRaw + fExtDef

    if config['buildUseAux']:
        flOutFinal = flOut[:]
        flOut += '.praktikal_aux'
        try:
            os.remove(f'{flOut}')
        except:
            ...

    # get file - categorised text (type-string pairs)
    lines_ctxt = dataGet(flIn, 'c_lx')
    try:
        lines_ctxt[0]
    except:
        return 'NF'
    
    # get equations - text (strings)
    lines_eqs = []
    for typ, line in lines_ctxt:
        if typ == 'eqt':
            lines_eqs.append(line)
    

    # get equation dictionary - {string: string}
    eqs = {}
    for line in lines_eqs:
        line = line.strip('$').replace('\t', '').replace('\\\\', '\\\\\\ ').replace('\\ ', '').replace(' ', '').replace('&', '').rstrip('\\\\')
        # line = line.replace('\t', '').replace('\\\\', '\\\\\\ ').replace('\\ ', '').replace(' ', '').replace('&', '').rstrip('\\\\')
        # be silly
        key, expr = line.split('=')
        unit = ''
        if '[' in key:
            key = key.replace('\\left', '').replace('\\right', '').replace(']', '')
            key, unit = key.split('[')
        # printcommented('KU:', key, unit)
        if key in eqs.keys():
            raise ValueError(f'Duplicate keys in {flIn}: [{key}]')
        eqs[key] = (expr, unit)
        # eqs[key] = expr
    
    # converts items of Dictionary from string to stack
    dictEqs0, dictEqs0Debug = dictStrToDictStack(eqs, 'lx', True)

    # set of all variables (str)
    setVarsAll = set(dictEqs0.keys())
    # set of vars which are not dependant on other variables (increases iteratively)
    setVarsIndep = set()
    dictEqs = copy.deepcopy(dictEqs0)
    
    # loop adds independent vars to setVarsIndep and evaluates vars that depend on independent vars
    while setVarsIndep != setVarsAll:
        bSetVarsIndepChanged = False
        # -----------------------
        # -----------------------
        for key, val in dictEqs.items():
            stack, set_vars_in_stack = val
            # variable is independent and value (not expression)
            if set_vars_in_stack == set() and stack.size() == 1:
                setVarsIndep.add(key)
            elif set_vars_in_stack <= setVarsIndep:
                if stack.isEmpty():
                    return ValueError(f'Stack [{key}] is empty')
                # evaluates stack
                res = evalStack(stack, dictEqs, setVarsIndep, key, dictEqs0Debug)
                bSetVarsIndepChanged = True
                # sets eval. value
                dictEqs[key] = (res, set())
        # if bSetVarsIndepChanged == False and setVarsIndep != setVarsAll: delal probleme pr fitu
        if bSetVarsIndepChanged == False and setVarsIndep != setVarsAll and len(set_vars_in_stack - setVarsIndep) > 0:
            setDiff = (setVarsAll - setVarsIndep)
            for el in setDiff:
                stack, set_vars_in_stack = dictEqs[el]
                raise RecursionError(f'Variable [{el}] depends on undefined or undeterminable variables {set_vars_in_stack - setVarsIndep}')
            # raise RecursionError(f'Not all Equations are Solvable:\t{setVarsAll-setVarsIndep}')
    dictEqs.pop('\\pi', None)
    dictEqs.pop('e', None)
    dictEqs.pop('g', None)
    
    # clears output file
    write(None, flOut)

    # writes output file from categorised text
    for typ, line in lines_ctxt:
        # debug
        if config['debugWriteLineCategory']:
            write(f'% TYPE: [{typ}]', flOut)
            # continue

        # equation line
        if typ == 'eqt':
            strBegLine = '$$'
            strEndLine = '$$'
            strEqualsSign = '='
            if '&=&' in line:
                strBegLine = '\t'
                strEndLine = '\\\\ '
                strEqualsSign = '&=&'
            
                
            key, expr = line.replace('&','').strip('$').split('=')
            key = key.replace('\t', '').replace(' ', '')
            expr = expr.rstrip('\\\\').strip('\t')
            str_unit_input = ''
            if '[' in key:
                key = key.replace('\\left', '').replace('\\right', '').replace(']', '')
                key, str_unit_input = key.split('[')
            exprEval = str(dictEqs[key][0]).lstrip('[').rstrip(']')

            # if config['buildKeepDataImports'] or not (expr.lstrip(' ')[0:2] == '\\$'):
            if config['buildKeepDataImports'] or not ('\\$' in expr):
                write(f'{strBegLine + key + strBegLine.replace("$$", "")} = {expr}{strToUnit(str_unit_input)}{strEqualsSign} {exprEval + strEndLine}', flOut)
            # write(f'\t{key}\t={expr}{dictEqs[key][0].peek().unit}&=& {exprEval}\\\\ ', flOut)
            continue
        
        # praktikal indicator line
        if '\\pkt{eqs' in line:
            lineRpl = line.replace('\\pkt{eqsb}', '').replace('\\pkt{eqse}', '')
            if lineRpl != '':
                write(lineRpl, flOut)
            continue

        # figure line
        if typ == 'fig':
            # string cleanup
            # line = line[10:-2].replace(' ', '').replace('$', '').rstrip('\\\\')
            line = line[10:].rstrip()[:-1].replace(' ', '').replace('$', '').rstrip('\\\\')
            slcs = line.split(';')
            # slcs[-1] = slcs[-1].rstrip('}').rstrip(')')
            # slcs[0] = slcs[0][9:].rstrip(')')
            xySlc = slice(0, None, 1)
            eBar = False
            fitPlot = False
            bLegend = False
            figsize = '(6,4)'
            strCaptionCustom = ''
            bExtendCaption = True
            nBins = 10
            bDensity = True
            bStackedHist = False
            bFillHist = False

            # determine fig type and prepairing data
            if '/' in slcs[0]:
                figType = 'lineChart'
                plotType = 'o'
                grid = True
                y, x = slcs[0].split('/')

                if '\\{' in x:
                    xParent, xChildren = x.split('\\{')
                    x = (xParent, xChildren[:-2].split('\\&'))
                else:
                    x = (x, [x])
                
                if '\\{' in y:
                    yParent, yChildren = y.split('\\{')
                    y = (yParent, yChildren[:-2].split('\\&'))
                else:
                    y = (y, [y])
            
            elif '\\sim' in slcs[0]:
                figType = 'histogram'
                plotType = 'bar'
                grid = False
                x, distr = slcs[0].split('\\sim')

                if x[:2] == '\\{':
                    x = x[2:-2].split('\\&')
                else:
                    x = [x]

            else:
                raise SyntaxError(f'Invalid figure string: [{line}]')
                            
            # reading parameters
            for param in slcs[1:]:
                bValidParam = False
                name, val = param.split('=')
                if name == 'slc':
                    bValidParam = True
                    xySlcListStr = val[1:-1].split(',')
                    xySlcList = []
                    for xySlcEl in xySlcListStr:
                        # printcommented(xySlcEl)
                        if isFloat(xySlcEl):
                            xySlcList.append(int(xySlcEl))
                        elif xySlcEl == '':
                            xySlcList.append(None)
                    if len(xySlcList) == 2:
                        xySlc = slice(xySlcList[0], xySlcList[1], 1)
                    else:
                        xySlc = slice(xySlcList[0], xySlcList[1], xySlcList[2])

                if name == 'figsize':
                    bValidParam = True
                    figsize = val

                if name in ('type', 'plotType'):
                    bValidParam = True
                    plotType = val

                if name in ('error', 'errorBar', 'eBar'):
                    bValidParam = True
                    if val.lower() == 'true':
                        eBar = True
                
                if name == 'fit':
                    bValidParam = True
                    if val.lower() != 'false':
                        fitPlot = val
                    if val.lower() == 'true':
                        if figType == 'lineChart':
                            fitPlot = 'lin'
                        elif figType == 'histogram':
                            fitPlot = 'pkt_default'
                
                if name == 'nBins':
                    bValidParam = True
                    nBins = int(val)
                
                if name.lower() in ('dens', 'density', 'pdensity', 'probdensity'):
                    bValidParam = True
                    if val.lower() == 'true':
                        bDensity = True
                    elif val.lower() == 'false':
                        bDensity = False
                    else:
                        raise ValueError(f'Invalid value for parameter [{name}]: [{val}]')
                
                if name.lower() in ('stacked', 'bstacked'):
                    bValidParam = True
                    if val.lower() == 'true':
                        bStackedHist = True
                    elif val.lower() == 'false':
                        bStackedHist = False
                    else:
                        raise ValueError(f'Invalid value for parameter [{name}]: [{val}]')
                
                if plotType == 'bar':
                    bFillHist = True
                elif plotType == 'step':
                    bFillHist = False
                elif figType == 'histogram':
                    raise ValueError(f'Invalid plot type for a histogram: [{plotType}]')
                if name.lower() in ('fill', 'bfill'):
                    bValidParam = True
                    if val.lower() == 'true':
                        bFillHist = True
                    elif val.lower() == 'false':
                        bFillHist = False
                    else:
                        raise ValueError(f'Invalid value for parameter [{name}]: [{val}]')
                
                if name in ('leg', 'legend'):
                    bValidParam = True
                    if val.lower() == 'true':
                        bLegend = True
                
                if name == 'grid':
                    bValidParam = True
                    if val.lower() == 'true':
                        grid = True
                    elif val.lower() == 'false':
                        grid = False
                
                if name.lower() in ('title', 'caption', 'capt'):
                    bValidParam = True
                    bExtendCaption = False
                    i_ = 0
                    if val[:len(str_ditto)] == str_ditto:
                        bExtendCaption = True
                        i_ = len(str_ditto)
                    strCaptionCustom = val[i_:].replace(',', ' ')
                
                if not bValidParam:
                    raise ValueError(f'Parameter [{param}] is not a valid parameter.')
            
            if figType == 'lineChart':
                pTitle = f'plot_{y[0]};{x[0]}'
                pTitle = pTitle.replace('\\','')
                pCapt = f'Graf ${y[0]}$ v odvisnosti od ${x[0]}$' * bExtendCaption + strCaptionCustom
                plot(figType, dictEqs, x, y, figSize=figsize, fl=pTitle, slc=xySlc, plotType=plotType, eBar=eBar, fit=fitPlot, leg=bLegend, grid=grid)
                write(f'\\begin{{figure}}[H]\n\t\\begin{{center}}\n\t\t\\includegraphics{{{pTitle}}}\n\t\\caption{{{pCapt}}}\n\t\\label{{fig:{pTitle}}}\n\t\\end{{center}}\n\\end{{figure}}',
                flOut)
                continue
            
            if figType == 'histogram':
                strTitle = ''
                for x_ in x:
                    strTitle += (x_ + ';')
                pTitle = f'hist_{strTitle[:-1]}'
                pTitle = pTitle.replace('\\','')
                pCapt = (bDensity * 'Verjetnostna porazdelitev' + (not bDensity) * 'Število dogodkov' + f' ${strTitle.replace(";", ", ")}$') * bExtendCaption + strCaptionCustom
                plot(figType, dictEqs, x, None, figSize=figsize, fl=pTitle, slc=xySlc, plotType=plotType, nBins=nBins, bDensity=bDensity, bStackedHist=bStackedHist, bFillHist=bFillHist, fit=fitPlot, leg=bLegend, grid=grid)
                write(f'\\begin{{figure}}[H]\n\t\\begin{{center}}\n\t\t\\includegraphics{{{pTitle}}}\n\t\\caption{{{pCapt}}}\n\t\\label{{fig:{pTitle}}}\n\t\\end{{center}}\n\\end{{figure}}',
                flOut)
                continue

        # table line
        if typ == 'tab':
            line = line.lstrip('\\pkt{tab}').replace(' ', '').replace('$', '').rstrip('\\\\')
            slcs = line.split(';')
            slcs[-1] = slcs[-1][:-1]
            slcs[0] = slcs[0].split('\\&')
            listStrVars = slcs[0]

            listVars = []
            numVars = len(listStrVars)
            lenVarMax = 0
            for strVar in listStrVars:
                tupVarVals = (strVar,)
                # var_unit = dictEqs[strVar][0].peek().unit
                # for i in range(len(dictEqs[strVar][0].peek())):
                #     var = dictEqs[strVar][0].peek()
                #     var_val, var_unc = var.val[i], var.unc[i * (len(var.unc) != 1)]
                #     tupVarVals.append(Nu(val=var_val, unc=var_unc, unit=var_unit))
                str_val, str_unc, decExp, str_unit = strNuFormat(dictEqs[strVar][0].peek(), False)

                vals = [str_val]
                if '\\begin{bmatrix}' in str_val:
                    vals = str_val.lstrip('\\begin{bmatrix}').rstrip('\\\\\\end{bmatrix}').split(' \\\\')

                uncs = [str_unc]
                if '\\begin{bmatrix}' in str_unc:
                    uncs = str_unc.lstrip('\\begin{bmatrix}').rstrip('\\\\\\end{bmatrix}').split(' \\\\')

                tupVarVals += vals, uncs, decExp, str_unit
                if len(vals) > lenVarMax:
                    lenVarMax = len(vals)
                listVars.append(tupVarVals)
            
            for param in slcs[1:]:
                name, val = param.split('=')
                bValidParam = False

                # there are no arguments yet
                if name == 'dddd':
                    bValidParam = True
                    dddd = val
                
                if not bValidParam:
                    raise ValueError(f'Parameter [{param}] is not a valid parameter.')
            
            # printcommented(xQt, yQt)
            write(f'\\begin{{table}}[H]\n\\centering\n\\begin{{tabular}}{{{"|c"*numVars}|}}\n\\hline', flOut)
            str2write = ''
            for tup in listVars:
                str_str, _, _, decExp, str_unit = tup
                str_unit = (str_unit != '') * str_unit + (str_unit == '' and decExp == None) * '/'

                str2write += '$' + str_str + ('\\left[' + (decExp != None) * f'\\cdot 10^{{{decExp}}}' + str_unit).replace('\\cdot', '').replace('\\left[\\ ', '\\left[') + '\\right]' + '$  & '
            str2write = str2write[:-2] + '\\\\ \\hline'
            write(str2write, flOut)

            for i in range(lenVarMax):
                str2write = ''
                for tup in listVars:
                    _, vals, uncs, _, _ = tup
                    try:
                        try:
                            if uncs[0] == '0':
                                str2write += f'${vals[i]}$ & '
                            else:
                                str2write += f'${vals[i]} \pm {uncs[i]}$ & '
                        except:
                            if uncs[0] == '0':
                                str2write += f'${vals[i]}$ & '
                            else:
                                str2write += f'${vals[i]} \pm {uncs[0]}$ & '
                    except:
                        str2write += '  & '
                str2write = str2write[:-2] + '\\\\'
                if i - lenVarMax + 1 == 0:
                    str2write += ' \\hline'
                write(str2write, flOut)
            tabLabel = ('table:{' + line[0:-1].split(';')[0].replace('\\&', ';') + '}').replace('\\', '')
            write(f'\\end{{tabular}} \n\\label{{{tabLabel}}}\n\\end{{table}}', flOut)
            # write(f'\\end{{tabular}}\n\\caption{{}} \n\\label{{{tabLabel}}}\n\\end{{table}}', flOut)
            continue

        # comment line
        if typ == 'cmt':
            if config['buildKeepComments']:
                write(line, flOut)
            continue
        
        # latex import line
        if '\\usepackage{xcolor}' in line:
            write(f'\\usepackage{{xcolor}} \pagecolor[HTML]{{{renConf["renColIn"][1:]}}} \color[HTML]{{{renConf["renColCont"][1:]}}}', flOut)
            continue
        
        strPrint = ''
        i = 9
        i_match = 0
        while i < len(line):
            if line[i-9:i] == '\\pkt{ref}':
                strParenth = lxRFindPar(line[i:], '{', '}')
                if strParenth != '':
                    try:
                        strPrint += line[i_match:i-9] + str(dictEqs[strParenth][0])[1:-1]
                        # exprEval = str(dictEqs[key][0]).lstrip('[').rstrip(']')
                        i += len(strParenth) + 2
                        i_match = i
                        continue
                    except:
                        raise ValueError(f"Variable [{strParenth}] is not defined and can't be referenced")
            i += 1
        strPrint += line[i_match:]
        write(strPrint, flOut)

    if config['buildUseAux']:
        try:
            # unix / linux
            # os.system(f'cp {flOut} {flOutFinal}')
            # windows
            os.system(f'copy {flOut} {flOutFinal}')
        except:
            raise SystemError('Unable to copy aux file.')
        
        try:
            os.remove(flOut)
        except:
            ...

    if config['buildPrintLog']:
        strTime = ''
        if config['buildPrintLogTimestamp']:
            strTime = f'{datetime.now()}\t'
        print(strTime + f'Build done. Written to:\t[{flOutFinal}]')
    return True

def build(flInRaw, flOutRaw):
    try:
        buildFunc(flInRaw, flOutRaw)
    except Exception as ex:
        if config['buildPrintLog']:
            if config['buildPrintLogTraceback']:
                print(f'{traceback.format_exc()}')
            else:
                strTime = ''
                if config['buildPrintLogTimestamp']:
                    strTime = f'{datetime.now()}\t'
                print(strTime + f'{ex}')

def buildPer(flInRaw, flOutRaw):
    # builds periodically when input file changes
    bI = config['buildPerInterval']
    build(flInRaw, flOutRaw)

    if '.' in flInRaw:
        flIn = flInRaw
    else:
        flIn = flInRaw + fExtDef
    
    with open(flIn, 'r') as f:
        fileLast = f.readlines()
    while True:
        time.sleep(bI)
        with open(flIn, 'r') as f:
            file = f.readlines()
            if file != fileLast:
                build(flInRaw, flOutRaw)
            fileLast = file

if __name__ == '__main__':
    print('Change Run Directory')











def stackDictGetEval(filename, dattype='e_lx', encod='utf-8'):
    DeprecationWarning
    return resultGet(filename, dattype, encod)

# def printStackDict(dict, st=None, rev=False):
#     for key in dict:
#         print(f'{key}\t= {dict[key][0]}')
#     if st != None:
#         print(st)
