import os
import numpy as np
import pandas as pd
#os.system('clear')
import matplotlib
import matplotlib.pyplot as plt


def path(fichero=''):
    return os.path.join(f"paquetes/{fichero}")
nombres = [path(i) for i in os.listdir("paquetes/")]

# structure:  tradicional -> simplificado -> [pinyin] -> /traducción1/traducción2/
# example:    你好 你好 [ni3 hao3] /Hello!/Hi!/How are you?/
with open(nombres[-1], "r", encoding='utf-8')as file:
    content = file.readlines()
    content = [i.split('\n')[0] for i in content]
valores = []
for i in content:
    if i[0] != '#':
        j = i.split('[')
        t = j[0].split(' ')
        p = j[1].split(']')
        s = p[1].split('/')[1]
        valores.append([t[0], t[1], p[0], s])
content.clear()
import pandas as pd
diccionario = pd.DataFrame(valores)
diccionario.columns = ['tradicional', 'simplificado', 'pinyin', 'significado']

with open(nombres[0], "r", encoding='gbk')as file:
    content = file.readlines()
    content = [i.split('\n')[0] for i in content]
valores, longitudes2 = [], []
for i in content[3:]:
    j = i.split('\t')
    longitudes2.append(len(j[0]))
    valores.append(j)
import pandas as pd
palabras = pd.DataFrame(valores)
columnas = content[2].split('\t')
palabras.columns = columnas
content.clear()


diccionario['simplificado'] = diccionario['simplificado'].astype(str)
longitudes1 = diccionario['simplificado'].apply(len)

max_len = max(longitudes1.max(), max(longitudes2))
bins = range(1, max_len + 2)

counts1, bins1 = np.histogram(longitudes1, bins=bins)
counts2, bins2 = np.histogram(longitudes2, bins=bins)
bin_centers = (bins1[:-1] + bins1[1:]) / 2
width = 0.45

plt.figure(figsize=(12, 8))
plt.title('Distribución de palabras por número de caracteres')

plt.bar(bin_centers - width/2, counts1, width=width,
        color='lightsalmon', edgecolor='coral', linewidth=1.5, label='diccionario', alpha = 0.8)
plt.bar(bin_centers + width/2, counts2, width=width,
        color='mediumaquamarine', edgecolor='darkgreen', linewidth=1.5, label='frecuencia', alpha = 0.8)
plt.yscale('log')

media1 = np.mean(longitudes1)
media2 = np.mean(longitudes2)

plt.axvline(x=media1, color='mediumpurple', linestyle='--', linewidth=2, 
            label=f'media dic. = {media1:.2f}')
plt.axvline(x=media2-0.1, color='purple', linestyle='--', linewidth=2, 
            label=f'media frec. = {media2-0.1:.2f}')

plt.xlabel('Número de caracteres')
plt.ylabel('Frecuencia de palabras (escala log)')
plt.grid(color='lavender', alpha=0.4)
plt.xticks(range(1, max_len + 1))
plt.legend()
plt.savefig('histograma.png')
plt.show()
