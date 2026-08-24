import math
import numpy as np
import matplotlib.pyplot as plt

input = np.linspace(0,100, 101) # criando um vetor de 0 a 100, com 101 elementos (incremento de 1)

saida = []
for value in input:
    saida.append(math.sin(value)) # append vai adicionando ao final da lista (poderia ter feito apenas saida = np.sin(input))

fig, ax = plt.subplots()
ax.grid(True)
ax.plot(input, saida)
plt.show()


