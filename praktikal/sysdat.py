
# DON'T EDIT THIS FILE

































































































































def updateDictDeep(dictRef, dictUpdate):
    # podslovarje posodobi rekurzivno, namesto da jih zamenja
    # trivialni podslovar {} obravnava kot vrednost, ne kot podslovar
    import copy
    dictNew = copy.deepcopy(dictRef)
    # for key_ref, val_ref in dictRef.items():
    for key in set(dictRef.keys()) | set(dictUpdate.keys()):
        if key in dictUpdate.keys():
            val_update = dictUpdate[key]
            if key in dictRef.keys(): # v obeh slovarjih
                val_ref = dictRef[key]
                if type(val_ref) == dict and type(val_update) == dict and val_update != {}:
                    val_new = updateDictDeep(val_ref, val_update) # podslovar posodobi s podslovarjem drugega slovarja
                else:
                    val_new = val_update
            else: # samo v dictUpdate
                val_new = val_update
        else: # samo v dictRef
            val_new = dictRef[key]
        dictNew[key] = val_new
    return dictNew

def getConfig(config_main):
    try:
        from conf import config as config_folder
        return updateDictDeep(config_main, config_folder)
    except:
        return config_main





sysdatconf = {
    # SI units
    'units_base': {
        'kmol': None,
        'cd': None,
        'A': None,
        'K': None,
        'kg': None,
        'm': None,
        's': None,
    },

    'units_composite': {
        'N': {
            'kg': 1,
            'm': 1,
            's': -2
        },
        'J': {
            'kg': 1,
            'm': 2,
            's': -2
        },
        'W': {
            'kg': 1,
            'm': 2,
            's': -3
        }
    },

    # 'unit_prefixes': {
    #         3: 'k',
    #         6: 'M',
    #         9: 'G',
    #         12: 'T',
    # }
    
    # matplotlib config
    "renMaster": {
        "dark": {
            "renColCont": "#FFFFFF",
            "renColIn": "#1E1E1E",
            "renColInContrast": "#404040",
            "renColOut": "#252526",
            "renColX": "#FFFFFF",
            "renColY": "#FFFFFF",
            # "renColX": "#40CEAF",
            # "renColY": "#DB734A",
            "renColPlotList": [
                "#68CDFE",
                "#FFE400",
            ],
            "renSizeErrBarCapRel": 4
        },
        # TODO: renColPlotContrast pr vseh k niso dark
        "light": {
            "renColCont": "#000000",
            "renColIn": "#FFFFFF",
            "renColInContrast": "#D0D0D0",
            "renColOut": "#F3F3F3",
            "renColX": "#000000",
            "renColY": "#000000",
            "renColPlotList": [
                "#FF4C4C",
                "#FF8000",
                "#E5E500",
                "#16E516",
                "#28CCCC",
                "#329CFF",
                "#7272FF",
            ],
            "renSizeErrBarCapRel": 4
        },
        "light_alt1": {
            "renColCont": "#000000",
            "renColIn": "#FFFFFF",
            "renColInContrast": "#404040",
            "renColOut": "#F3F3F3",
            "renColX": "#098658",
            "renColY": "#B700DB",
            "renColPlotMain": "#0000FF",
            "renColPlotContrast": "#999DA0",
            "renSizeErrBarCapRel": 4
        },
        "b_mode": {
            "renColCont": "#303030",
            "renColIn": "#FFD6E9",
            "renColInContrast": "#F3C4D6",
            "renColOut": "#FFB3C6",
            "renColX": "#7F0072",
            "renColY": "#7F0072",
            "renColPlotMain": "#993366",
            "renColPlotContrast": "#4682B4",
            "renSizeErrBarCapRel": 4
        }
    }

}
