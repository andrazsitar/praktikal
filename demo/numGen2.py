import numpy as np

file0 = open('tab3.txt', "w")
for i in range(2 ** 18):
        s = ''
        for j in range(8):
                s += f'{(2 ** 16) * np.random.random()}'
        print(s, file=file0)
        