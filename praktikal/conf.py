
config = {
    # files general
    'fileExtensionDefault': '.tex',
    'fileExtensionDefTable': '.txt',

    # render style
    'renMaster': 'light',
        # options are: 'custom'; 'dark'; 'light'
    'renMasterCustomMode': {
        'renColCont': '#000000',
        'renColIn': '#000000',
        'renColOut': '#000000',
        "renColPlotContrastAlt": "#000000",
        'renColX': '#000000',
        'renColY': '#000000',
        'renColPlotMain': '#000000',
        'renColPlotContrast': '#000000',
        'renSizeErrBarCapRel': 4
    },

    # build function
    'buildPrintLog': True,
    'buildPrintLogTraceback': True,
    'buildPrintLogTimestamp': True,
    'buildUseAux': True,
    'buildPerInterval': 0.2, # časovni interval [s] preverjanja, če se je dokument spremenil
    'buildKeepComments': False, # ne prepiše komentiranih vrstic
    'buildKeepCalculatedEquations': False, # pri enačbah zapiše izračunane vrednosti
    'buildKeepDataImports': False, # zapiše podatke, ko so uvoženi
    'buildKeepDataGenerators': False, # zapiše podatke, ko so generirani, npr. z ukazom \mathbb{N}^{9}
    'buildKeepCommentedEquations': False,
    'buildKeepFileStyle': False, # ne upošteva v 'renMaster' definiranega načina prikaza

    # Nu() print config
    'printNuSigFigsDependentOnUnc': True, # število decimalnih mest nazivne vrednosti je odvisno od negotovosti
    'printNuSigFigs': 2, # število decimalnih mest pri negotovosti
    'printNuDimLim': 2, # število prikazanih meritev v izračunu
    'printNuExpThreshold': 3, # prag za eksponentni zapis števila
    'printNuExpStep': 3, # korak pri eksponentnem zapisu, običajno 1 ali 3
    'printNuRemoveLeading0': False, # odstranitev ničle pri številih 0,XYZ
    'printNuSymbolDec': ',\\!', # decimalni simbol
    'printNuThresholdSeperator3Digit': 5, # prag števila števk za rabo simbola med troštevkovnimi nizi
    'printNuSymbolSeperator3Digit': '\\>', # simbol med troštevkovnimi nizi
    'printNuSymbolSeperatorUnit': '\\>', # simbol predsledka med numerično vrednostjo in enoto
    'printNuSymbolNaN': '\\nexists',
    'printNuFloatToleranceDigits' : 6, # odstopanja, manjša od te tolerance bodo popravljena; mora biti manjše od numerične napake
    'printNuCompositeUnits': {
        # '\Omega': {
        #         'kg': 1,
        #         'm': 2,
        #         's': -3,
        #         'A': -2,
        # },
        # 'T': {
        #         'kg': 1,
        #         's': -2,
        #         'A': -1,
        # },
        # 'F': {
        #         'kg': -1,
        #         'm': -2,
        #         's': 4,
        #         'A': 2
        # },
        # 'H': {
        #         'kg': 1,
        #         'm': 2,
        #         's': -2,
        #         'A': -2
        # },
        # 'V': {
        #         'kg': 1,
        #         'm': 2,
        #         's': -3,
        #         'A': -1,
        #     },
        # 'Vs': {   # če Praktikal napiše neustrezno enoto
        #         'kg': 1,
        #         'm': 2,
        #         's': -2,
        #         'A': -1,
        #     },
        # 'Nm': {   # če Praktikal napiše neustrezno enoto
        #     'kg': 1,
        #     'm': 2,
        #     's': -2
        # },
        # 'N': {}, # onemogočenje enote
        # 'J': {}, # onemogočenje enote
        # 'W': {}, # onemogočenje enote
        # 'eV': {
		# 	None: 1.602177e-19,
        #     'kg': 1,
        #     'm': 2,
        #     's': -2
        # },
        # '{^\circ}C': {
        #     'K': 1,
        # },
    },
    'printNuCompositeUnitIfExactMatch': False,

    # LaTeX interpreter config
    'latexInterpFuncAngle': 's.avg',
    'latexInterpFuncOverline': 's.avg',
    'latexInterpFuncSigma': {1: 's.sdv', 2:'s.sdvW'},
    'latexInterpFuncOplus': 'v.cnc',
    'latexInterpSymbolDitto': '-||-',

    # matplotlib config
    'pltUseTeX': True,
    'pltSkipPlotting': False,
    'pltFitStyle': '--',
    'pltScaleScatter': False, # če je veliko meritev, zmanjša odčitke

    #DEBUG
    'debugRememberStack': True,
    'debugPrintStack': False,
    'debugPrintUnitAsDict': False,
    'debugWriteLineCategory': False,







































    #DEPRECATED:
    # file read
    'resultGetFixReadFile': False, # not implemented

    # file write
    'wEqsKeepOther': True,
    'wEqsKeepSrc': False, # bugged
    'wFileFix': False,
    'wFileFixDefHeader':[
        '\\documentclass[12pt,a4paper]{article}',
        '\\usepackage{xcolor} \\pagecolor[rgb]{0.12,0.12,0.12} \\color[rgb]{1,1,1}',
        '\\usepackage{amsmath}',
        '\\begin{document}',
        '\\begin{center}'
    ],
    'wFileFixDefAbstract':[
        '\\end{center}',
        '\\begin{eqnarray}'
    ],
    'wFileFixDefFooter':[
        '\\end{eqnarray}',
        '\\end{document}'
    ],
}
