**Primer dokumenta se nahaja v mapi demo.**

Podatke lahko uvozimo iz `.txt` dokumenta, v katerem se v zgornji vrstici oziroma levem stolpcu imena spremenljivk, pod oziroma desno od njih pa številčne vrednosti v eni izmed standardnih oblik zapisa realnih števil. Podatki morajo biti urejeni, da **velikost stolpcev pada** od leve proti desni oziroma **velikost vrstic pada** od zgoraj navzdol.

Podatke kot spremenljivko uvozimo s simbolom `\$`, za katerim napišemo ime datoteke (če je končnica `.txt`, končnice ni treba pisati), za tem pa ime spremenljivke (v tabeli) v oglatih oklepajih. Za datoteko `tabela.txt`, v kateri se nahaja stolpec ali vrstica z oznako `a`, bi uvožena spremenljivka `b` izgledala kot
```tex
b &=& (\$tabela[a] \pm 0.1) \cdot 10^{3} \\
```