**Primer dokumenta se nahaja v mapi demo.**

Podatke lahko uvozimo iz besedilnega dokumenta, v katerem se v zgornji vrstici oziroma levem stolpcu imena spremenljivk, pod oziroma desno od njih pa številčne vrednosti v eni izmed standardnih oblik zapisa realnih števil. Podatki morajo biti urejeni, da **velikost stolpcev pada** od leve proti desni oziroma **velikost vrstic pada** od zgoraj navzdol.

Podatke kot spremenljivko uvozimo s simbolom `\$`, za katerim napišemo ime datoteke (če je končnica `.txt`, končnice ni treba pisati), za tem pa ime spremenljivke (v datoteki) v oglatih oklepajih. Za datoteko `podatki.txt`, v kateri se nahaja stolpec ali vrstica z oznako `a`, bi uvožena spremenljivka `b` izgledala kot
```tex
b &=& (\$ podatki[a] \pm 0.1) \cdot 10^{3} \\
```

Praktikal samodejno zazna, če so podatki v datoteki podani v obliki stolpcev ali vrstic.

V praktikalu lahko tudi generiramo urejene sezname končnih podmnožic celih števil. V kodi sta definirana seznama prvih 64 naravnih števil in seznam celih števil od 10 do 20
```tex
n &=& \mathbb{N}^{64} \\
z &=& \mathbb{Z}_{10}^{20} \\
```
