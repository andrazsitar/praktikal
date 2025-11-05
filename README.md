**Primeri dokumenta se nahajajo v mapah arhetip (osnoven delujoč dokument) in demo (primeri funkcij praktikala ter primer poročila).**

Mapa praktikal se mora nahajati v mapi z ostalimi paketi (kot npr. numpy, matplotlib, ...).
V operacijskem sistemu Windows naslov najdemo z ukazom "python -m site --user-site" in dobimo naslov, podoben ...\Python\Python314\Lib\site-packages\

V operacijskem sistemu linux pa mapo najdemo z ukazom "whereis python*", kjer * predstavlja ustrezno verzijo. V tej mapi bi se morala nahajati mapa site-packages oz. dist-packages. Alternativen ukaz je 'python3 -c "import sys; print('\n'.join(sys.path))"'. V obeh primerih je naslov podoben naslovu
/usr/lib/python3/dist-packages/ ali /usr/lib/python3/site-packages/

Za obdelavo dokumenta ustvarimo novo mapo (kjerkoli), v njej pa .py datoteko z 2 vrsticama:
```py
from praktikal.solver import buildPer
buildPer('ime_vhodne_datoteke', 'ime_izhodne_datoteke')
```

V isti mapi moramo še ustvariti datoteko `ime_vhodne_datoteke.tex`, ki služi kot vhodna datoteka, katero Praktikal bere. Ko poženemo `.py` datoteko, Praktikal ustvari ali prepiše izhodno datoteko `ime_izhodne_datoteke.tex`. Če v `.py` datoteki uporabimo funkcijo `buildPer`, Praktikal znova obdela vhodno datoteko, ko v njej zazna spremembo. S funkcijo `build` pa Praktikal vhodno datoteko obdela enkrat ter preneha delovati.

Če niso posebej označene, Praktikal vrstice iz vhodne v izhodno datoteko preprosto prepiše. Vse posebne oznake so oblike `\pkt{ime_oznake}`.

Začetek in konec enačb, katere naj Praktikal prebere, označimo z `\pkt{eqsb}` in `\pkt{eqse}`, z vsako v svoji vrstici. Tako okolje naj vsebuje samo enačbe. Te naj se nahajajo znotraj okolja `eqnarray*`, katerem so na levi strani imena spremenljivk, na desni pa izraz. Ločuje naj ju `&=&`. Če je izraz meritev, desno od imena spremenljivke v oglate oklepaje zapišemo enoto. Z izrazom lahko tudi uvozimo ali generiramo več meritev, ki jih sočasno obdelamo (glej `README_seznami.md`). Definirane funkcije najdemo v `README_funkcije.md`. Kot simbole Praktikal razume črke angleške in grške abecede (nekateri simboli grške abecede služijo kot funkcije, teh ne moremo uporabljati), oboje pa lahko indeksiramo. Naj bo `x` črka. Indeksiramo jo `x_{niz}` (zaviti oklepaji so nujni, na to opozori tudi Praktikal). Črki lahko sledi znak `'` ali `^*` oz. `^{*}`. Črko lahko tudi spremenimo z enem izmed okolij `\mathcal`, `\mathfrak`, `\hat`, `\widehat`, `\tilde`, `\widetilde`, `\acute` in `\grave`.

V besedilu se lahko sklicujemo na spremenljivko z oznako `\pkt{ref}{ime_spremenljivke}`. Če Praktikal v besedilu naleti na tako oznako, besedilo prepiše, oznako pa zamenja z izračunano vrednostjo spremenljivke `ime_spremenljivke`.

Praktikal je zmožen tudi pisati tabele ter risati grafe in histograme. Dokumentacijo najdemo v `README_prikaz_podatkov.md`.

Predsledke in tabulatorje Praktikal ignorira.

V sistemski mapi Praktikala se nahaja dokument nastavitev `conf.py`. Če v mapi, v kateri se nahaja `ime_vhodne_datoteke.tex`, ustvarimo novo datoteko nastavitev `conf.py` z le nekaterimi nastavitvami, Praktikal prednostno upošteva nastavitve z lokalne mape, če pa te niso definirane, pa uporabi nastavitve s sistemske mape (iz tiste datoteke kopiramo nastavitve).