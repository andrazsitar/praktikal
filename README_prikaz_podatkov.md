**Primeri dokumenta se nahajajo v mapah arhetip (osnoven delujoč dokument) in demo (primeri funkcij praktikala ter primer poročila).**

# Tabele:
Tabelo ustvarimo z oznako (v svoji vrstici) `\pkt{tab}{niz_spremenljivk}`. Namesto `niz_spremenljivk` moramo napisati imena vseh spremenljivk, katere hočemo prikazati v tabeli, ločimo jih pa z `\&`. Celoten niz naj se nahaja znotraj enojnih `$`-oklepajev.

Če v zaporednih vrsticah zapišemo več tabel, bodo zlepljene. To preprečimo z vmesno prazno vrstico ali pa simbolom `\\` na koncu vrstice.

# Figure:
Figuro ustvarimo z oznako (v svoji vrstici) `\pkt{fig}{parametri}`. Parametre (če jih je več) ločujemo s podpičjem (`;`), prvi mora pa biti niz spremenljivk, ki naj se nahaja znotraj enojnih `$`-oklepajev. Če parameter to dopušča, argumenta parametra ločimo z vejico (`,`). Parametri so
- Niz spremenljivk.

	Odvisnost `y` od `x`prikažemo z `$ y / x $`.

	Če je od `x` odvisnih več vrednosti `y`, to prikažemo z `$ y \{ y_{1} \& y_{2} \& y_{3} \} / x $`, kjer je `y` skupno ime spremenljivk, ki ga vidimo na osi ter v naslovu.
	
	Odvisnost več vrednosti `y` od več vrednosti `x` podobno prikažemo z `$ y \{ y_{1} \& y_{2} \& y_{3} \} / x \{ x_{1} \& x_{2} \& x_{3} \} $`, kjer sta `y` in `x` skupni imeni ustreznih spremenljivk.

- `color = vrednosti`

	Nastavitev barve ima običajno smisel le v primeru več grafov na isti sliki. Tedaj morajo biti vrednosti podane v n-terici, npr. `color = (a,b,c,...)`. Število barv v n-terici se mora ujemati s številom grafov. Praktikal na podlagi teh vrednosti interpolira med barvami, definiranimi v nastavitvah `renColPlotList`.

	Barve lahko podamo s seznamom naravnih števil, kjer Praktikal interpolira med najmanjšo in največjo vrednostjo. Privzeta vrednost teh števil je indeks grafa.
	
	Barve lahko podamo tudi s števili s plavajočo vejico med 0 in 1.
	
	Lahko uporabimo tudi svoje barve, ki jih definiramo z nizi z enako sintakso, kot jo uporablja Matplotlib.pyplot, npr `r`, `g`, `b`, ...

- `figsize = (x,y)`

	Celi števili `x` in `y` sta velikost grafa.

- `title = ime`

	`ime` je ime slike, predsledke zapišemo z vejico (`,`). Oznaka `-||-` označuje, da Praktikal le nadaljuje že obstoječe ime slike (to oznako lahko spremenimo v nastavitvah).

- `leg = bool`

	Če je resničnostna vrednost `bool` resnična, Praktikal nariše legendo.

- `grid = bool`

	Če je resničnostna vrednost `bool` resnična, Praktikal nariše mrežo.

## Grafi:
Niz spremenljivk sestavljajo odvisne spremenljivke na levi in neodvisne spremenljivke na desni strani simbola /. Če je spremenljivka ena, preprosto zapišemo njeno ime. Če jih je več, moramo definirati skupno ime vseh spremenljivk, te pa zbrati znotraj zavitih oklepajev \{ in \}, ločenih z \&. Primer tega so spremenljivke y_i v odvisnosti od x:
```tex
\pkt{fig}{$y \{ y_1 \& y_2 \& y_3 \} / x $}
```
Če je neodvisnih spremenljivk več, jih mora biti enako kot odvisnih.

Parametri so
- `type = vrsta`

	`vrsta` je vrsta grafa. Praktikal uporablja imena vrst grafov iz `matplotlib.pyplot.plot(fmt=vrsta)`. V primeru slike z več grafi, lahko vrsto podamo z n-terico, podobno, kot lahko storimo z barvami pri parametru `color`.

- `error = vrsta`

	Če je vrednost `bar`, Praktikal okoli izmerkov nariše interval negotovosti. Če je vrednost `band`, Praktikal okoli izmerkov z barvo zapolni interval negotovosti.

- `fit = vrsta`

	Če je vrednost `lin`, Praktikal nariše regresijsko premico, če je vrednost `const`, pa konstantno funkcijo.

- `xscale, yscale = vrsta`

	Če je vrednost `linear`, je v tej spremenljivki graf narisan v linearni skali, če je `log`, pa v logaritemski skali.

- `xlim, ylim = (min,max)`

	Omeji vrednosti spremenljivke na interval. Sintaksa števil s plavajočo vejico je identična sintaksi v Python-u.

- `slc = rez`

	Riše le vrednosti, ki jih definira rez. Sintaksa je identična sintaksi v Python-u.

## Histogrami:
Niz spremenljivk sestavljajo spremenljivke na levi in porazdelitev na desni strani simbola \sim (zaenkrat porazdelitve še ne služijo ničemer, zato kot vrsto spremenljivke lahko napišemo karkoli). Če je spremenljivka ena, preprosto zapišemo njeno ime. Če jih je več, jih moramo zapisati znotraj zavitih oklepajev `\{` in `\}`, ločenih z `\&`. Primer tega je histogram y_i:
```tex
\pkt{fig}{$ \{ y_1 \& y_2 \& y_3 \} \sim y' $}
```

Količina, po kateri so v oznaki porazdeljene količine y_i, torej y', je popolnoma simbolične narave, namreč služi le poimenovanju količine na abcisi historgrama. Ta količina nosi enote količin y_i.

Parametri so
- `type = vrsta`

	`vrsta` je vrsta histograma. Praktikal uporablja imena grafov iz `matplotlib.pyplot.hist(histtype=vrsta)`.

- `fill = bool`

	Če je resničnostna vrednost `bool` resnična, Praktikal zapolni površino pod stolpci.

- `density = bool`

	Če je resničnostna vrednost `bool` resnična, Praktikal nariše histogram verjetnostne gostote, sicer pa histogram števila dogodkov.

- `stacked = bool`

	Če je resničnostna vrednost `bool` resnična, Praktikal v primeru več spremenljivk zlaga stolpce drug na drugega.

- `nBins = int`

	Določimo število stolpcev v histogramu.