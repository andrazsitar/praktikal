**Primer dokumenta se nahaja v mapi demo.**

Tabele:
Tabelo ustvarimo z oznako (v svoji vrstici) `\pkt{tab}{niz_spremenljivk}`. Namesto `niz_spremenljivk` moramo napisati imena vseh spremenljivk, katere hočemo prikazati v tabeli, ločimo jih pa z `\&`. Celoten niz naj se nahaja znotraj enojnih `$`-oklepajev.

# Figure:
Figuro ustvarimo z oznako (v svoji vrstici) `\pkt{fig}{parametri}`. Parametre (če jih je več) ločujemo s podpičjem (`;`), prvi mora pa biti niz spremenljivk, ki naj se nahaja znotraj enojnih `$`-oklepajev. Če parameter to dopušča, argumenta parametra ločimo z vejico (`,`). Parametri so
- `figsize = (x,y)`

	Celi števili `x` in `y` sta velikost grafa.

- `title = ime`

	`ime` je ime slike, predsledke zapišemo z vejico (`,`). Oznaka `-||-` označuje, da Praktikal le nadaljuje že obstoječe ime slike (to oznako lahko spremenimo v configu).

- `leg = bool`

	Če je resničnostna vrednost `bool` resnična, Praktikal nariše legendo 

- `grid = bool`

	Če je resničnostna vrednost `bool` resnična, Praktikal nariše mrežo 

## Grafi:
Niz spremenljivk sestavljajo odvisne spremenljivke na levi in neodvisne spremenljivke na desni strani simbola /. Če je spremenljivka ena, preprosto zapišemo njeno ime. Če jih je več, moramo definirati skupno ime vseh spremenljivk, te pa zbrati znotraj zavitih oklepajev \{ in \}, ločenih z \&. Primer tega so spremenljivke y_i v odvisnosti od x:
```tex
\pkt{fig}{$y \{ y_1 \& y_2 \& y_3 \} / x $}
```
Če je neodvisnih spremenljivk več, jih mora biti enako kot odvisnih.

Parametri so
- `type = vrsta`

	`vrsta` je vrsta grafa. Praktikal uporablja imena grafov iz `matplotlib.pyplot.plot(fmt=vrsta)`.

- `eBar = bool`

	Če je resničnostna vrednost `bool` resnična, Praktikal okoli vrednosti nariše interval negotovosti.

- `fit = bool`

	Če je resničnostna vrednost `bool` resnična, Praktikal nariše regresijsko premico.

## Histogrami:
Niz spremenljivk sestavljajo spremenljivke na levi in porazdelitev na desni strani simbola \sim (zaenkrat porazdelitve še ne služijo ničemer, zato kot vrsto spremenljivke lahko napišemo karkoli). Če je spremenljivka ena, preprosto zapišemo njeno ime. Če jih je več, jih moramo zapisati znotraj zavitih oklepajev `\{` in `\}`, ločenih z `\&`. Primer tega je histogram y_i:
```tex
\pkt{fig}{$ \{ y_1 \& y_2 \& y_3 \} \sim ? $}
```

Parametri so
- `type = vrsta`

	`vrsta` je vrsta histograma. Praktikal uporablja imena grafov iz `matplotlib.pyplot.hist(histtype=vrsta)`.

- `fill = bool`

	Če je resničnostna vrednost `bool` resnična, Praktikal zapolni površino pod stolpci.

- `density = bool`

	Če je resničnostna vrednost `bool` resnična, Praktikal nariše histogram verjetnostne gostote, sicer pa histogram števila dogodkov.

- `stacked = bool`

	Če je resničnostna vrednost `bool` resnična, Praktikal v primeru več spremenljivk zlaga stolpce drug na drugega.