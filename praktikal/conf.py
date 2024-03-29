
config = {
    # files general
    'fileExtensionDefault': '.tex',
    'fileExtensionDefTable': '.txt',

    # render style
    'renMaster': 'dark',
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
    'buildPerInterval': 1,
    'buildKeepComments': False,
    'buildKeepDataImports': False,
    'buildKeepFileStyle': False,

    # Nu() print config
    'printNuSigFigsDependentOnUnc': True,
    'printNuSigFigs': 1,
    'printNuDimLim': 2,
    'printNuExpThreshold': 3,
    'printNuExpStep': 3,
    'printNuRemoveLeading0': False,
    'printNuSymbolDec': ',',
    'printNuSymbolNaN': '\\nexists',
    'printNuFloatToleranceDigits' : 6,
    'printNuCompositeUnits': {
        '\Omega': {
                'kg': 1,
                'm': 2,
                's': -3,
                'A': -2,
        },
        # 'F': {
        #         'kg': -1,
        #         'm': -2,
        #         's': 4,
        #         'A': 2
        # },
        'V': {
                'kg': 1,
                'm': 2,
                's': -3,
                'A': -1,
            },
        # 'Vs': {
        #         'kg': 1,
        #         'm': 2,
        #         's': -2,
        #         'A': -1,
        #     },
        # 'Nm': {
        #     'kg': 1,
        #     'm': 2,
        #     's': -2
        # },
        # 'J': {},
        # 'W': {},
    },
    'printNuCompositeUnitIfExactMatch': False,

    # LaTeX interpreter config
    'latexInterpFuncAngle': 's.avg',
    'latexInterpFuncOverline': 's.avg',
    'latexInterpFuncSigma': 's.sdv',
    'latexInterpFuncOplus': 'v.cnc',
    'latexInterpSymbolDitto': '-||-',

    # matplotlib config
    'pltUseTeX': True,
    'pltSkipPlotting': False,

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
