
import numpy as np
import copy
import matplotlib.pyplot as plt
from praktikal.sysdat import *
from praktikal.numunc import Nu, Stat, getLinFit, ln
from praktikal.conf import config as config_main
config = getConfig(config_main)

plt.rcParams['text.usetex'] = config["pltUseTeX"]
fExtDef = f'.{config["fileExtensionDefault"].lstrip(".")}'
fExtTab = f'.{config["fileExtensionDefTable"].lstrip(".")}'
if fExtTab == None:
    fExtTab = fExtDef
lstResW = ["Results written to file:\t[", "]"]
lstResWCl = ["Cleared file:\t\t\t[", "]"]

lstFFHeader = config["wFileFixDefHeader"]
lstFFAbstract = config["wFileFixDefAbstract"]
lstFFFooter = config["wFileFixDefFooter"]

if config["renMaster"] in (None, "custom"):
    renConf = config["renMasterCustomMode"]
else:
    renConf = sysdatconf["renMaster"][config["renMaster"]]
pltRenParams = {
    'axes.edgecolor':renConf["renColOut"],
    'xtick.color':renConf["renColX"],
    'ytick.color':renConf["renColY"],
    'figure.facecolor':renConf["renColOut"],
    'legend.labelcolor':renConf["renColCont"],
    'legend.facecolor':renConf["renColOut"],
    'legend.edgecolor':renConf["renColOut"]
}

strColors = {
    'r': (240,0,0),
    'g': (0,220,0),
    'b': (0,0,220),
    'c': (0,240,240),
    'm': (240,0,240),
    'y': (240,240,0),
    'k': (0,0,0),
    'w': (240,240,240)
}

def fixEqParentheses(s_):
    s = s_[:]
    s = s.replace('\\left(', '(').replace('(', '\\left(').replace('\\right)', ')').replace(')', '\\right)')
    s = s.replace('\\left[', '[').replace('[', '\\left[').replace('\\right]', ']').replace(']', '\\right]')
    return s

def dataGet(filename, dattype="e_lx", encod="utf-8"):
    # gets various data types:
    #   d:  dictionary
    #           lx: reads LaTeX equations
    #           ps: reads praktikal PostScript stacks
    #   t:  table
    #           py: writes python list
    #           np: writes numpy array
    #   c:  categorised text
    #           lx: reads LaTeX document (equations work only with eqnarray*)
    #   
    if "." in filename:
        filen = filename
    else:
        if dattype[:2] == "t_":
            filen = filename + fExtTab
        else:
            filen = filename + fExtDef
    
    # pathSys = os.path.dirname(os.path.realpath(__file__))
    
    try:
        with open(filen, "r", encoding=encod) as file:
            lines_all = []
            for x in file:
                lines_all.append(str(x).strip("\n"))
            # lines_all = str(file).split("\n")
    except:
        with open(filen, "a", encoding=encod) as file:
            print("File Created")
        return
    
    if dattype == "raw":
        return lines_all
    
    lines = lines_all[:]

    # erasing empty lines and \n symbols
    for i in range(len(lines)):
        # printc(i)
        if dattype[:2] == "t_":
            line = lines[i].split("\t")
        else:
            line = [lines[i]]
        while "" in line:
            line.remove("")
        lines[i] = line
    while [] in lines:
        lines.remove([])
    if len(lines) == 0:
        raise ValueError("No Data Had Been Provided")

    if dattype[:2] == "c_":
        if dattype[2:4] == "lx":
            # line types eqt(equation), fig(figure), cmt(comment), oth(other)
            lines_ctxt = []
            lineType = "oth"
            for x in lines_all:
                xStrip = x.lstrip('\t').lstrip(' ')
                bComment = len(xStrip) > 0 and x.lstrip('\t').lstrip(' ')[0] == '%'
                if "\\pkt{eqse}" in x:
                    if lineType == "eqt":
                        lineType = "oth"
                    else:
                        raise SyntaxError(f"Praktikal Signifier for Equations to End found in line, marked as [{lineType}]")
                if lineType == "eqt" and not bComment and "=" in x:
                    lines_ctxt.append(("eqt", fixEqParentheses(x)))
                    continue
                if "\\pkt{eqsb}" in x:
                    if lineType == "oth":
                        lineType = "eqt"
                    else:
                        raise SyntaxError(f"Praktikal Signifier for Equations to Begin found in line, marked as [{lineType}]")
                
                if "\\pkt{fig}" in x and not bComment:
                    if lineType == "oth":
                        lines_ctxt.append(("fig", x))
                        continue
                    else:
                        raise SyntaxError(f"Praktikal Signifier for Figure found in line, marked as [{lineType}]")
                
                if "\\pkt{tab}" in x and not bComment:
                    if lineType == "oth":
                        lines_ctxt.append(("tab", x))
                        continue
                    else:
                        raise SyntaxError(f"Praktikal Signifier for Table found in line, marked as [{lineType}]")
                    
                if bComment:
                    lines_ctxt.append(("cmt", x))
                    continue
                lines_ctxt.append(("oth", x))
            return lines_ctxt
        
    if dattype[:2] == "e_":
        DeprecationWarning
        # equations
        eqs = {}
        for x in lines:
            # printc(dattype[2:4])
            if dattype[2:4] == "lx":
                boolSkipLine = False
                if "%" in x[0] or not "=" in x[0]:
                    boolSkipLine = True
                if boolSkipLine:
                    continue
                x[0] = x[0].lstrip("\t").replace("\\\\", "\\\\\\ ").replace("\\ ", "").replace(" ", "").replace("&", "").rstrip("\\nonumber").rstrip(" ").rstrip("\\\\")
            
            a = x[0].split("=")
            key = a[0].rstrip("\\\\").rstrip("\t ")
            # key = a[0].rstrip("\\\\").rstrip("\t ")
            if key in eqs.keys():
                raise Exception(f"Duplicate keys in {filen}: [{key}]")
            eqs[key] = a[1].lstrip(" ")
        
        return eqs

    if dattype == "t_dt":
        # table dictionary
        dic = {}
        # determining row or collumn form
        if isFloat(lines[0][0]):
            raise ValueError('Table is without proper variable names in proper places (left side or top)')
        else:
            if len(lines[0]) > 1 and isFloat(lines[0][1]):
                # table is row-form
                lines0 = lines[:]
            else:
                # table is collunm-form
                lines0 = transposeList(lines)
        
        for line in lines0:
            nparr = np.zeros((len(line) - 1))
            for j in range(1, len(line)):
                try:
                    nparr[j - 1] = line[j]
                except:
                    nparr[j - 1] = np.nan
            dic[line[0]] = nparr
        return dic
        

    if dattype == "t_py":
        DeprecationWarning
        return lines

    if dattype == "t_np":
        DeprecationWarning
        nparr = np.zeros((len(lines[0]), len(lines)))
        for i in range(0, len(lines)):
            for j in range(0, len(lines[i])):
                nparr[j][i] = lines[i][j]
        return nparr
    
    raise Exception(TypeError, f"Unsupported Data Type: {dattype}")

def wPrintLogToTerminal(lst, filename, fExtD):
    # if "." in filename:
    #     printc(f"{lst[0]}{filename}{lst[1]}")
    # else:
    #     printc(f"{lst[0]}{filename}{fExtD}{lst[1]}")
    return

def write(ob, filename=None, wmode=""):
    # with open(filename + fExtDef, "w+" , encoding="utf-8") as file0:
    if type(ob) in (tuple, list):
        for ob0 in ob:
            write(ob0, filename, wmode)
        wPrintLogToTerminal(lstResW, filename, fExtDef)
        return
    
    if ob == None:
        if filename == None:
            raise Exception(FileNotFoundError, "Cannot clear non-existent File")
        if "." in filename:
            file0 = open(filename, "w")
        else:
            file0 = open(filename + fExtDef, "w")
        file0.close()
        wPrintLogToTerminal(lstResWCl, filename, fExtDef)
        return
    
    if filename == None:
        file0 = None
    else:
        if "." in filename:
            filen = filename[:]
        else:
            filen = filename + fExtDef
        file0 = open(filen, "a+" , encoding="utf-8")
    
    if type(ob) in [str, Nu, np.ndarray]:
        print(ob, file=file0)
    # if type(ob) in [str, Nu]:
    #     printc(ob, file=file0)
    # if type(ob) == np.ndarray:
    #     printc("d", file=file0)
    elif type(ob) == list:

        for x in ob:
            print(x, file=file0)
        file0.close()
        wPrintLogToTerminal(lstResW, filename, fExtDef)
        return
    
    elif type(ob) == dict:
        # if config["printNuTypeLang"] == "tex":
        #     printc("\\begin{alignat*}{1}", file=file0)
        for key in ob:
            val = ob[key]
            # printc(val)
            if type(val) == tuple:
                val0 = val[0]
                if key[0] == "$":
                    print(val0, file=file0)
                    continue
                if config["printNuTypeLang"] == "tex":
                    st = f"\t{key}"
                    if type(val0) == tuple:
                        # printc("val0", val0[0])
                        for x in val:
                            # printc(key, x[0])
                            st += f"\t&=& {x[0].peek()}"
                    else:
                        st += f"\t&=& {val0.peek()}"
                    # printc(st+" \\nonumber\\\\", file=file0)
                    print(st+" \\\\", file=file0)
                else:
                    print(f"{key}\t= {val[0].peek()}", file=file0)
            if type(val) == str:
                print(f"{key}\t= {val}", file=file0)
        # if config["printNuTypeLang"] == "tex":
        #     printc("\\end{alignat*}", file=file0)


        if filename != None:
            file0.close()
            wPrintLogToTerminal(lstResW, filename, fExtDef)
        return

def plot(figType, dict_vals, inp_x, inp_y, figSize='(6,4)', subplots=((0,0),), xRange=None, yRange=None, xscale='linear', yscale='linear', fl=None, slc=slice(0, None, 1), plotTypes='pkt_default', error=None, fit='', nBins=10, bHistLog=False, bDensity=True, bStackedHist=False, bFillHist=False, leg=False, grid=False, col=None):
    # check if enabled
    if config['pltSkipPlotting']:
        return
    
    if not "." in fl:
        fl += ".pdf"
    
    # colour interp
    def hex_to_rgb(value):
        value = value.lstrip('#')
        lv = len(value)
        return np.array(list(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3)))
    
    def rgb_to_hex(rgb):
        rgb_tup = tuple(int(comp) for comp in rgb)
        return '#%02x%02x%02x' % rgb_tup
    
    # main_rgb_def = hex_to_rgb(renConf["renColPlotMain"])
    # cont_rgb_def = hex_to_rgb(renConf["renColPlotContrast"])
    list_rgb_def = [hex_to_rgb(hex) for hex in renConf["renColPlotList"]]
    if len(list_rgb_def) < 2:
        raise ValueError(f'Setting "renColPlotList" should be of length [2] or more, not [{len(list_rgb_def)}]')
    
    def getColor(i, col=None):
        # main_rgb, cont_rgb, list_rgb_interp = main_rgb_def, cont_rgb_def, list_rgb_def
        list_rgb_interp = list_rgb_def
        # main_rgb = list_rgb_interp[0]
        # cont_rgb = list_rgb_interp[1]
        list_hex_exact = []
        list_interp_final = [j for j in range(numDataSets)]
        if type(col) == tuple:
            if col[0] == 'list':
                _, cols = col
                if np.prod([type(c) == int for c in cols]): # ali so vse barve cela števila
                    M = np.max(cols)
                    if M == 0:
                        list_interp_final =[0 for c in cols]
                    else:
                        list_interp_final = [c / M for c in cols]
                elif np.prod([type(c) in (int, float) for c in cols]): # ali so vse barve vsaj realna števila
                    list_interp_final = [c for c in cols]
                elif np.prod([type(c) == str for c in cols]): # ali so vse barve vsaj nizi
                    for c in cols:
                        list_hex_exact.append(rgb_to_hex(strColors[c]))
        elif col == None:
            list_interp_final = [j / (numDataSets - 1 * (numDataSets > 1)) for j in range(numDataSets)]
        else:
            raise ValueError(f'Invalid color set: [{col}]')
        
        if list_hex_exact == []:
            if numDataSets > 1:
                f_interp = list_interp_final[i]
                # get proper interpolation interval
                idx_interp_interval = int(( f_interp * (len(list_rgb_interp) - 1) ) // 1)
                f_interp_in_interval = ( f_interp * (len(list_rgb_interp) - 1) ) % 1
                # print()
                # print(f_interp)
                # print(idx_interp_interval, f_interp_in_interval)

                # get proper colors
                rgb0 = list_rgb_interp[idx_interp_interval]
                rgb1 = list_rgb_interp[idx_interp_interval + (f_interp_in_interval != 0)]
                # print(rgb0, rgb1)


                # rgb_return = (rgb0 * (1 - f_interp_in_interval) + rgb1 * f_interp_in_interval) // 1
                rgb_return = ((np.sqrt(rgb0 / 256) * (1 - f_interp_in_interval) + np.sqrt(rgb1 / 256) * f_interp_in_interval) ** 2) * 256 // 1
                return rgb_to_hex(rgb_return)
            else:
                return rgb_to_hex(list_rgb_interp[0])
        return list_hex_exact[i]

    if figType == 'lineChart':
        if plotTypes == 'pkt_default':
            plotTypes = 'o'
            # plotTypes = 'scatter'

        inp_x_parent, inp_x_children = inp_x
        inp_y_parent, inp_y_children = inp_y

        numDataSets = len(inp_y_children)
        if len(inp_x_children) != 1 and len(inp_x_children) != numDataSets:
            raise ValueError(f'Plot can have {len(inp_y_children)} sets of y-values dependent on {len(inp_y_children)} or 1 set of x-values, not on {len(inp_x_children)} sets.')
        if type(plotTypes) == list and len(plotTypes) != 1 and len(plotTypes) != numDataSets:
            raise ValueError(f'Plot can have {len(inp_y_children)} sets of y-values plotted with {len(inp_y_children)} or 1 plot type, not with {len(plotTypes)} plot types.')
    elif figType == 'histogram':
        if plotTypes == 'pkt_default':
            plotTypes = 'bar'

        inp_y_children = inp_y
        inp_x_children = None

        numDataSets = len(inp_y_children)
        if type(plotTypes) == list:
            raise NotImplementedError(f'Histogram can only have a single plot type.')
    else:
        raise ValueError(f'Invalid figure type: [{figType}]')
    
    # subplots_len = (1,1)
    # if subplots != ((0,0),):
    #     xIdxExtr, yIdxExtr = [np.inf,-np.inf], [np.inf,-np.inf]
    #     xSetIdx, ySetIdx = set(), set()
    #     for tup in subplots:
    #         xIdx, yIdx = tup
    #         xSetIdx.add(xIdx)
    #         ySetIdx.add(yIdx)
    #         if xIdx < xIdxExtr[0]:
    #             xIdxExtr[0] = xIdx
    #         if xIdx > xIdxExtr[1]:
    #             xIdxExtr[1] = xIdx
    #         if yIdx < yIdxExtr[0]:
    #             yIdxExtr[0] = yIdx
    #         if yIdx > yIdxExtr[1]:
    #             yIdxExtr[1] = yIdx
    #     if not xIdxExtr[0] == 0:
    #         raise ValueError(f'Smallest subplot x-index needs to be [1], not [{xIdxExtr[0] + 1}]')
    #     if not yIdxExtr[0] == 0:
    #         raise ValueError(f'Smallest subplot y-index needs to be [1], not [{xIdxExtr[0] + 1}]')
    #     subplots_len = (xIdxExtr[1]+1, yIdxExtr[1]+1)
    #     for i in range(subplots_len[0]):
    #         if i not in xSetIdx:
    #             raise ValueError(f'All subplot x-indices from [1] to [{subplots_len[0]}] need to be represented - index [{i+1}] not represented.')
    #     for i in range(subplots_len[1]):
    #         if i not in ySetIdx:
    #             raise ValueError(f'All subplot y-indices from [1] to [{subplots_len[1]}] need to be represented - index [{i+1}] not represented.')
    # else:
    #     subplots = numDataSets * subplots[0]
    
    # def getSubplotIdx(i):
    #     print(i, subplots)
    #     xIdx, yIdx = subplots[i]
    #     if subplots_len[0] == 1:
    #         return yIdx
    #     if subplots_len[1] == 1:
    #         return xIdx
    #     return xIdx, yIdx

    with plt.rc_context(pltRenParams):
        # printc(key_x)
        plt.clf()

        sizeX, sizeY = figSize[1:-1].replace(' ','').split(',')
        # fig, axs = plt.subplots(ncols=subplots_len[0], nrows=subplots_len[1])
        plt.figure(figsize=(float(sizeX), float(sizeY)))
        
        # dirty implementation - gets units ipd. from first element
        if figType == 'lineChart':
            try:
                y_full = dict_vals[inp_y_children[0]][0].peek()
            except:
                raise KeyError(f'Dependent variable in plot [{inp_y_children[0]} / {inp_x_children[0]}] is undefined.')
            try:
                x_full = dict_vals[inp_x_children[0]][0].peek()
            except:
                raise KeyError(f'Independent variable in plot [{inp_y_children[0]} / {inp_x_children[0]}] is undefined.')
            
            unit_y = str(y_full.unit)
            unit_y += (unit_y == '')*'\\ /'
            
            unit_x = str(x_full.unit)
            unit_x += (unit_x == '')*'\\ /'
        elif figType == 'histogram':
            try:
                y_full = dict_vals[inp_y_children[0]][0].peek()
            except:
                raise KeyError(f'Dependent variable in plot [{inp_y_children[0]} / {inp_x_children[0]}] is undefined.')
            unit_y = '\\ /'
            
            unit_x = str(y_full.unit)
            unit_x += (unit_x == '')*'\\ /'

        axes = plt.axes()
        axes.set_facecolor(renConf["renColIn"])
        
        usd_if_tex = config["pltUseTeX"] * "$"
        # plt.xlabel(f"{usd_if_tex}{inp_x}\\left[{unit_x[2:]}\\right]{usd_if_tex}", color=renConf["renColX"])
        if figType == 'lineChart':
            plt.xlabel(f"{usd_if_tex}{inp_x_parent}\\left[{unit_x[2:]}\\right]{usd_if_tex}", color=renConf["renColX"])
            plt.ylabel(f"{usd_if_tex}{inp_y_parent}\\left[{unit_y[2:]}\\right]{usd_if_tex}", color=renConf["renColY"])
        elif figType == 'histogram':
            plt.xlabel(f"{usd_if_tex}{inp_x}\\left[{unit_x[2:]}\\right]{usd_if_tex}", color=renConf["renColX"])
            if bDensity:
                plt.ylabel(f"{usd_if_tex}\\rho\\left[{unit_y[2:]}\\right]{usd_if_tex}", color=renConf["renColY"])
            else:
                plt.ylabel(f"{usd_if_tex}N\\left[{unit_y[2:]}\\right]{usd_if_tex}", color=renConf["renColY"])
        
        x = []
        y = []
        if figType == 'lineChart':
            for i in range(len(inp_y_children)):
                inp_x_child = inp_x_children[i * (len(inp_x_children) != 1)]
                inp_y_child = inp_y_children[i]
                try:
                    x_full_child = dict_vals[inp_x_child][0].peek()
                except:
                    raise KeyError(f'Independent variable in plot [{inp_y_child} / {inp_x_child}] is undefined.')
                try:
                    y_full_child = dict_vals[inp_y_child][0].peek()
                except:
                    raise KeyError(f'Dependent variable in plot [{inp_y_child} / {inp_x_child}] is undefined.')
                
                # match lengths
                lenMin = np.min((len(x_full_child), len(y_full_child)))

                x_trim = x_full_child[:lenMin]
                x_trim.fxt()
                y_trim = y_full_child[:lenMin]
                y_trim.fxt()

                x.append(x_trim[slc])
                y.append(y_trim[slc])
        
        elif figType == 'histogram':
            # raise NotImplementedError('TODO: match lengths')
            for i in range(len(inp_y_children)):
                inp_y_child = inp_y_children[i]
                try:
                    y_full_child = dict_vals[inp_y_child][0].peek()
                except:
                    raise KeyError(f'Random variable [{inp_y_child}] in histogram is undefined.')
            #     x_full.append(x_full_child)

            #     if len(x_full_child) < lenMin:
            #         lenMin = len(x_full_child)
                
            # x_new = []
            # for i in range(len(x_full)):
            #     x_full_child = x_full[i]

            #     x_trim = x_full_child[:lenMin]
            #     x_trim.fxt()

            #     x_new.append(x_trim[slc])
            # x = x_new

                # match lengths
                lenMin = len(y_full_child)
            
                y_trim = y_full_child[:lenMin]
                y_trim.fxt()
                
                y.append(y_trim[slc])
        
        if figType == 'lineChart':
            if xRange != None:
                plt.xlim(*xRange)
            if yRange != None:
                plt.ylim(*yRange)
            for i in range(numDataSets):
                x_child = x[i * (len(inp_x_children) != 1)]
                y_child = y[i]
                inp_x_child = inp_x_children[i * (len(inp_x_children) != 1)]
                inp_y_child = inp_y_children[i]
                x_child += 0
                y_child += 0

                # spIdx = getSubplotIdx(i)

                # scatterSize = 10
                # if len(x_child.val) > 128:
                #     scatterSize = 6
                # if len(x_child.val) > 256:
                #     scatterSize = 2
                scatterSize = 16
                if config['pltScaleScatter']:
                    scatterSize = 32 * (1.08 - np.tanh(0.01*len(x_child.val)))

                if type(plotTypes) == str:
                    plotType = plotTypes
                elif type(plotTypes) == list:
                    plotType = plotTypes[i]
                else:
                    raise ValueError(f'Plot type for line chart can be type [str] or [list], not [{type(plotTypes)}]')
                
                # color interp
                renCol=getColor(i, col)

                if fit == 'lin':
                    fit_k, fit_n = getLinFit(x_child, y_child)
                    func_fit = np.poly1d((fit_k.val, fit_n.val))
                if fit == 'const':
                    fit_n = Stat.avg(y_child)
                    func_fit = np.poly1d((0, fit_n.val))
                if fit == 'exp':
                    fit_k, fit_n = getLinFit(x_child, ln(y_child))
                    func_fit = lambda var: np.exp(fit_n.val + fit_k.val * var)
                
                lbl = None
                if leg:
                    lbl = f'${inp_y_child}$'
                if plotType[0] == 'o':
                    if error == 'bar':
                        plt.errorbar(x_child.val, y_child.val, xerr=x_child.unc, yerr=y_child.unc, fmt ='none', ecolor=renCol, elinewidth=1, capsize=2, capthick=0.5, label=lbl)
                        plt.plot(x_child.val, y_child.val, plotType, c=renCol, alpha=1)
                    elif error == 'band':
                        plt.plot(x_child.val, y_child.val - y_child.unc, ':', c=renCol, alpha=1)
                        plt.plot(x_child.val, y_child.val + y_child.unc, ':', c=renCol, alpha=1)
                        plt.fill_between(x_child.val, y_child.val - y_child.unc, y_child.val + y_child.unc, color=renCol, alpha=0.2)
                        plt.plot(x_child.val, y_child.val, plotType, c=renCol, alpha=1, label=lbl)
                    else:
                        # stops double labeling in case of type == 'o--'
                        if plotType == 'o':
                            plt.scatter(x_child.val, y_child.val, c=renCol, alpha=1, s=scatterSize, label=lbl)
                        else:
                            plt.scatter(x_child.val, y_child.val, c=renCol, alpha=1, s=scatterSize)
                        
                    if len(plotType) > 1:
                        plt.plot(x_child.val, y_child.val, plotType[1:], c=renCol, alpha=1, label=lbl)
                else:
                    plt.plot(x_child.val, y_child.val, plotType, c=renCol, alpha=1, label=lbl)

                if fit in ('lin', 'const', 'exp'):
                    # fit lines
                    plt.plot(x_child.val, func_fit(x_child.val), config['pltFitStyle'], color=renCol)
                    # plt.plot(x_child.val, func_fit(x_child.val), "-", color=renConf["renColPlotMain"], label=f"$\\textrm{{cov}} \\left( {inp_x_child}, {inp_y_child}\\right)$")
            plt.xscale(xscale)
            plt.yscale(yscale)
        
        elif figType == 'histogram':
            renCol = []
            lbl = []
            if type(plotTypes) == str:
                plotType = plotTypes
            else:
                raise ValueError(f'Plot type for histogram can be type [str], not [{type(plotTypes)}]')
            if fit == 'pkt_default':
                raise NotImplementedError('Histogram fit is not yet implemented')
            for i in range(numDataSets):
                # colour interp
                # renCol = getColor(i, col)
                renCol.append(getColor(i, col))
                
                if leg:
                    lbl.append(f'${inp_y_children[i]}$')
                else:
                    lbl.append(None)
            plt.hist([y_.val for y_ in y], nBins, density=bDensity, histtype=plotType, stacked=bStackedHist, fill=bFillHist, log=bHistLog, color=renCol, label=lbl)

        if leg:
            # if f_m[1] < 0:
            #     lLoc = "upper right"
            # else:
            #     lLoc = "lower right"
            # plt.legend(loc=lLoc)
            plt.legend()
        
        # print(grid)
        if grid != False:
            plt.grid(True, color=renConf['renColInContrast'], linestyle='-')

        if fl == None:
            # printc(f"Plotted Graph:\t\t\t{key_y} ({key_x})")
            plt.show()
        else:
            plt.tight_layout()
            plt.savefig(f"{(fl)}")
            # printc(f"Plotted Graph:\t\t\t{key_y} ({key_x}) as [{fl+ext}]")
    plt.close()

def isFloat(x):
    # checks if object can become float (is not type(a) == float)
    # ni v solver kajti circular import
    try:
        x = np.float64(x)
        return True
    except:
        return False

def transposeList(lst):
    lstRes = [[]]*len(lst[0])
    for j in range(len(lst[0])):
        lstRes[j] = [lst[0][j]]
    for i in range(1, len(lst)):
        for j in range(len(lst[i])):
            lstRes[j].append(lst[i][j])
    return lstRes

if __name__ == "__main__":
    print("Change Run Directory")