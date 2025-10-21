# pomožna koda, ki datoteke .csv prepiše v format .txt, ki ga lahko bere praktikal
import numpy as np

korak = 100
b_zapis_v_1_datoteko = True

koren_imena_datoteke = 'tab_long'
koncnice_datoteke1 = ('_kalib','_jeklo','_Al','_med')
# koncnice_datoteke1 = ('_Al','_med')
koncnice_datoteke2 = ('1', '2', '3')
imena_spremenljivk = ('t', 'U')

vrsta_datoteke_vh = 'csv'
vrsta_datoteke_izh = 'txt'

lst_koncnice = []
for koncnica1 in koncnice_datoteke1:
    for koncnica2 in koncnice_datoteke2:
        lst_koncnice.append(koncnica1 + koncnica2)

lst_file_lines = []
open(f'tab.{vrsta_datoteke_izh}', 'w').close()
for koncnica in lst_koncnice:
    filename = f'{koren_imena_datoteke}{koncnica}'
    filename_inp = f'{filename}.{vrsta_datoteke_vh}'
    filename_out = f'{filename}.{vrsta_datoteke_izh}'
    lines = []
    try:
        with open(filename_inp, "r") as file:
            for line in file:
                if str(line).lstrip('-').lstrip('+')[0].isdigit():
                    lst = []
                    for str_num in line.split(','):
                        lst.append(float(str_num))
                    # krajšanje, če je premalo imen
                    lst = lst[:len(imena_spremenljivk)]

                    # operacije z elementi
                    # neki
                    
                    st_line = ''
                    for num in lst:
                        st_line += f'{num}\t'
                    lines.append(st_line)
                    # lines.append(line.replace(',', '\t'))
    except:
        print(f"File not found: [{filename_inp}], pretending it doesn't exist")
        continue
    
    # naiven pristop - običajno je boljše povprečenje
    lines = lines[::korak]

    # pisanje v datoteko / datoteke
    if b_zapis_v_1_datoteko:
        lst_file_lines.append(lines)
    else:
        open(filename_out, 'w').close()
        with open(filename_out, 'w') as f:
            header = ''
            for ime in imena_spremenljivk:
                header += f'{ime}\t'
            f.write(header + '\n')
            for line in lines:
                f.write(line + '\n')


if b_zapis_v_1_datoteko:
    len_max = max(len(lines) for lines in lst_file_lines)
    fname = 'tab.txt'

    lines_print = ['' for _ in range(len_max + 1)]
    for i in range(len(lst_file_lines)):
        lines = lst_file_lines[i]

        header = ''
        for str_var in imena_spremenljivk:
            header += f'{str_var}_{{{lst_koncnice[i].replace("_", "")}}}\t'

        lines_print[0] += header
        for j in range(len_max):
            try:
                lines_print[j + 1] += lines[j]
            except:
                lines_print[j + 1] += '\t' * len(lines[0].split('\t'))
    
    open(fname, 'w').close()
    with open(fname, 'w') as f:
        for line in lines_print:
            f.write(line.rstrip('\t') + '\n')