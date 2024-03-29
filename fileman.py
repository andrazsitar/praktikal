
import numpy as np
import matplotlib.pyplot as plt
import os
from praktikal.sysdat import *
from praktikal.numunc import Nu, getLinFit
from praktikal.conf import config

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
                if "\\pkt{eqse}" in x:
                    if lineType == "eqt":
                        lineType = "oth"
                    else:
                        raise SyntaxError(f"Praktikal Signifier for Equations End found in line, marked as [{lineType}]")
                if lineType == "eqt" and not "%" in x and "=" in x:
                    lines_ctxt.append(("eqt", fixEqParentheses(x)))
                    continue
                if "\\pkt{eqsb}" in x:
                    if lineType == "oth":
                        lineType = "eqt"
                    else:
                        raise SyntaxError(f"Praktikal Signifier for Equations Begin found in line, marked as [{lineType}]")
                
                if "\\pkt{fig}" in x and not "%" in x:
                    if lineType == "oth":
                        lines_ctxt.append(("fig", x))
                        continue
                    else:
                        raise SyntaxError(f"Praktikal Signifier for Figure found in line, marked as [{lineType}]")
                
                if "\\pkt{tab}" in x and not "%" in x:
                    if lineType == "oth":
                        lines_ctxt.append(("tab", x))
                        continue
                    else:
                        raise SyntaxError(f"Praktikal Signifier for Table found in line, marked as [{lineType}]")
                    
                if "%" in x:
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
                x[0] = x[0].lstrip("\t").replace("\\\\", "\\\\\\ ").replace("\\ ", "").replace(" ", "").replace("&", "").rstrip("\\nonumber").rstrip("\\\\")
            
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

def plot(figType, dict_vals, inp_x, inp_y, figSize='(6,4)', fl=None, slc=slice(0, None, 1), plotType='pkt_default', eBar=False, fit='', nBins=10, bDensity=True, bStackedHist=False, bFillHist=False, leg=False, grid=False):
    # check if enabled
    if config['pltSkipPlotting']:
        return
    
    # colour interp
    def hex_to_rgb(value):
        value = value.lstrip('#')
        lv = len(value)
        return np.array(list(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3)))

    def rgb_to_hex(rgb):
        rgb_tup = (int(rgb[0]), int(rgb[1]), int(rgb[2]))
        return '#%02x%02x%02x' % rgb_tup
    
    main_rgb = hex_to_rgb(renConf["renColPlotMain"])
    cont_rgb = hex_to_rgb(renConf["renColPlotContrast"])
    
    if not "." in fl:
        fl += ".pdf"

    if figType == 'lineChart':
        if plotType == 'pkt_default':
            plotType = 'scatter'

        inp_x_parent, inp_x_children = inp_x
        inp_y_parent, inp_y_children = inp_y

        numDataSets = len(inp_y_children)
        if len(inp_x_children) != 1 and len(inp_x_children) != numDataSets:
            raise ValueError(f'Plot can have {len(inp_y_children)} sets of y-values dependent on {len(inp_y_children)} or 1 set of x-values, not on {len(inp_x_children)} sets')
    elif figType == 'histogram':
        if plotType == 'pkt_default':
            plotType = 'bar'

        inp_x_children = inp_x
        inp_y_children = None

        numDataSets = len(inp_x_children)
    else:
        raise ValueError(f'Invalid figure type: [{figType}]')

    with plt.rc_context(pltRenParams):
        # printc(key_x)
        plt.clf()

        sizeX, sizeY = figSize[1:-1].replace(' ','').split(',')
        plt.figure(figsize=(float(sizeX), float(sizeY)))
        
        # dirty implementation - gets units ipd. from first element
        if True:
            try:
                x_full = dict_vals[inp_x_children[0]][0].peek()
            except:
                raise KeyError(f'Independent variable in plot [{inp_y_children[0]} / {inp_x_children[0]}] is undefined.')
            
            unit_x = str(x_full.unit)
            unit_x += (unit_x == '')*'\\ /'
        
        if figType == 'lineChart':
            try:
                y_full = dict_vals[inp_y_children[0]][0].peek()
            except:
                raise KeyError(f'Dependent variable in plot [{inp_y_children[0]} / {inp_x_children[0]}] is undefined.')
            
            unit_y = str(y_full.unit)
            unit_y += (unit_y == '')*'\\ /'
        elif figType == 'histogram':
            unit_y = '\\ /'

        ax = plt.axes()
        ax.set_facecolor(renConf["renColIn"])
        
        usd_if_tex = ''
        if config["pltUseTeX"]:
            usd_if_tex = "$"
        # plt.xlabel(f"{usd_if_tex}{inp_x}\\left[{unit_x[2:]}\\right]{usd_if_tex}", color=renConf["renColX"])
        if figType == 'lineChart':
            plt.xlabel(f"{usd_if_tex}{inp_x_parent}\\left[{unit_x[2:]}\\right]{usd_if_tex}", color=renConf["renColX"])
            plt.ylabel(f"{usd_if_tex}{inp_y_parent}\\left[{unit_y[2:]}\\right]{usd_if_tex}", color=renConf["renColY"])
        elif figType == 'histogram':
            # plt.xlabel(f"{usd_if_tex}{inp_x_parent}\\left[{unit_x[2:]}\\right]{usd_if_tex}", color=renConf["renColX"])
            plt.xlabel(f"{usd_if_tex}{inp_x[0]}\\left[{unit_x[2:]}\\right]{usd_if_tex}", color=renConf["renColX"])
            if bDensity:
                plt.ylabel(f"{usd_if_tex}\\rho\\left[{unit_y[2:]}\\right]{usd_if_tex}", color=renConf["renColY"])
            else:
                plt.ylabel(f"{usd_if_tex}N\\left[{unit_y[2:]}\\right]{usd_if_tex}", color=renConf["renColY"])
        
        x_full = []
        y_full = []
        lenMin = np.infty
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
                x_full.append(x_full_child)
                y_full.append(y_full_child)

                if len(x_full_child) < lenMin:
                    lenMin = len(x_full_child)
                if len(y_full_child) < lenMin:
                    lenMin = len(y_full_child)
                
            x_new = []
            y_new = []
            for i in range(len(x_full)):
                x_full_child = x_full[i]
                y_full_child = y_full[i]

                x_trim = x_full_child[:lenMin]
                x_trim.fxt()
                y_trim = y_full_child[:lenMin]
                y_trim.fxt()

                x_new.append(x_trim[slc])
                y_new.append(y_trim[slc])
            x = x_new
            y = y_new
        
        elif figType == 'histogram':
            for i in range(len(inp_x_children)):
                inp_x_child = inp_x_children[i]
                try:
                    x_full_child = dict_vals[inp_x_child][0].peek()
                except:
                    raise KeyError(f'Random variable [{inp_x_child}] in histogram is undefined.')
                x_full.append(x_full_child)

                if len(x_full_child) < lenMin:
                    lenMin = len(x_full_child)
                
            x_new = []
            for i in range(len(x_full)):
                x_full_child = x_full[i]

                x_trim = x_full_child[:lenMin]
                x_trim.fxt()

                x_new.append(x_trim[slc])
            x = x_new
        
        if figType == 'lineChart':
            for i in range(numDataSets):
                x_child = x[i * (len(inp_x_children) != 1)]
                y_child = y[i]
                inp_x_child = inp_x_children[i * (len(inp_x_children) != 1)]
                inp_y_child = inp_y_children[i]
                x_child += 0
                y_child += 0

                # scatterSize = 10
                # if len(x_child.val) > 128:
                #     scatterSize = 6
                # if len(x_child.val) > 256:
                #     scatterSize = 2
                scatterSize = 32 * (1.08 - np.tanh(0.01*len(x_child.val)))
                
                # colour interp
                if numDataSets > 1:
                    renCol = rgb_to_hex((main_rgb * (1 - (i / (numDataSets - 1))) + cont_rgb * (i / (numDataSets - 1))) // 1)
                else:
                    renCol = rgb_to_hex(main_rgb)

                if fit == 'lin':
                    fit_k, fit_n = getLinFit(x_child, y_child)
                    func_lin_fit = np.poly1d((fit_k.val, fit_n.val))
                
                lbl = None
                if leg:
                    lbl = f'${inp_y_child}$'
                if plotType[:1] == 'o':
                    if eBar:
                        plt.errorbar(x_child.val, y_child.val, xerr=x_child.unc, yerr=y_child.unc, fmt ='none', ecolor=renCol, capsize=2, capthick=0.5, label=lbl)
                        # printc(f"Plot label: $\\frac{{d {key_y}}}{{d {key_x}}} = {f_m[1]}$")
                    else:
                        # stops double labeling in case of type == 'o--'
                        if plotType == 'o':
                            plt.scatter(x_child.val, y_child.val, c=renCol, alpha=0.6, s=scatterSize, label=lbl)
                        else:
                            plt.scatter(x_child.val, y_child.val, c=renCol, alpha=0.6, s=scatterSize)
                        
                    if len(plotType) > 1:
                        plt.plot(x_child.val, y_child.val, plotType[1:], c=renCol, alpha=0.6, label=lbl)
                else:
                    plt.plot(x_child.val, y_child.val, plotType, c=renCol, alpha=0.6, label=lbl)

                if fit == 'lin':
                    # fit lines
                    plt.plot(x_child.val, func_lin_fit(x_child.val), "--", color=renCol)
                    # plt.plot(x_child.val, func_lin_fit(x_child.val), "-", color=renConf["renColPlotMain"], label=f"$\\textrm{{cov}} \\left( {inp_x_child}, {inp_y_child}\\right)$")
        
        elif figType == 'histogram':
            renCol = []
            lbl = []
            if fit == 'pkt_default':
                raise NotImplementedError('Histogram fit is not yet implemented')
            for i in range(numDataSets):
                # colour interp
                if numDataSets > 1:
                    renCol.append(rgb_to_hex((main_rgb * (1 - (i / (numDataSets - 1))) + cont_rgb * (i / (numDataSets - 1))) // 1))
                else:
                    renCol.append(rgb_to_hex(main_rgb))
                
                if leg:
                    lbl.append(f'${inp_x_children[i]}$')
                else:
                    lbl.append(None)
            plt.hist([x_.val for x_ in x], nBins, density=bDensity, histtype=plotType, stacked=bStackedHist, fill=bFillHist, color=renCol, label=lbl)

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