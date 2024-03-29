import numpy as np

file0 = open('tab2.txt', "w")
print('r_{1}\tr_{2}\tr_{3}', file=file0)
for i in range(512):
        print(f'{np.random.normal(0,0.3)}\t{np.random.normal(2,0.5)}\t{np.random.normal(4,0.8)}', file=file0)
        