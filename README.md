**Primer dokumenta se nahaja v mapi demo.**

Mapa praktikal se mora nahajati v
...\Python\Python310\Lib\site-packages\praktikal

Za obdelavo dokumenta ustvarimo novo mapo (kjerkoli), v njej pa .py datoteko z 2 vrsticama:
```py
from praktikal.solver import buildPer
buildPer("ime_vhodne_datoteke", "ime_izhodne_datoteke")
```

V isti mapi moramo še ustvariti datoteko `ime_vhodne_datoteke.tex`, ki služi kot vhodna datoteka, katero Praktikal bere. Ko poženemo `.py` datoteko, Praktikal ustvari ali prepiše izhodno datoteko `ime_vhodne_datoteke.tex`. Če v `.py` datoteki uporabimo funkcijo `buildPer`, Praktikal znova obdela vhodno datoteko, ko v njej zazna spremembo. S funkcijo `build` pa Praktikal vhodno datoteko obdela enkrat ter preneha delovati.

Če niso posebej označene, Praktikal vrstice iz vhodne v izhodno datoteko preprosto prepiše. Vse posebne oznake so oblike `\pkt{ime_oznake}`.

Začetek in konec enačb, katere naj Praktikal prebere označimo z `\pkt{eqsb}` in `\pkt{eqse}`, z vsako v svoji vrstici. To okolje naj vsebuje samo enačbe. Te naj se nahajajo znotraj okolja `eqnarray*`, katerem so na levi strani imena spremenljivk, na desni pa izraz. Ločuje naj ju `&=&`. Če je izraz meritev, desno od imena spremenljivke v oglate oklepaje zapišemo enoto. Z izrazom lahko tudi uvozimo več meritev, ki jih sočasno obdelamo (glej `README_uvoz.txt`). Definirane funkcije najdemo v `README_funkcije.txt`. Kot simbole Praktikal razume črke angleške in grške abecede, oboje pa lahko indeksiramo. Naj bo `x` črka. Indeksiramo jo `x_{niz}` (zaviti oklepaji so nujni, na to opozori tudi Praktikal).

V besedilu se lahko sklicujemo na spremenljivko z oznako `\pkt{ref}{ime_spremenljivke}`. Če Praktikal v besedilu naleti na tako oznako, besedilo prepiše, oznako pa zamenja z izračunano vrednostjo spremenljivke `ime_spremenljivke`.

Praktikal je zmožen tudi pisati tabele ter risati grafe in histograme. Dokumentacijo najdemo v `README_prikaz_podatkov.txt`.

Predsledke in tabulatorje Praktikal ignorira.