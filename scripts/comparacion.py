# comparacion.py – Comparación entre grafo de caracteres y grafo de Carroll
import os, numpy as np, pandas as pd, matplotlib.pyplot as plt, networkx as nx
from collections import defaultdict
from scipy.stats import pearsonr

plt.rcParams['axes.facecolor'] = '#FAFAFA'
plt.rcParams['figure.facecolor'] = 'white'
colores_caracter = 'lightsalmon'
colores_carroll  = 'mediumaquamarine'

def path(fichero=''):
    return os.path.join("paquetes", fichero)

print("Cargando datos...")
nombres = [path(i) for i in os.listdir("paquetes/")]

with open(nombres[-1], "r", encoding='utf-8') as file:
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
diccionario = pd.DataFrame(valores, columns=['tradicional','simplificado','pinyin','significado'])
diccionario['simplificado'] = diccionario['simplificado'].astype(str)

with open(nombres[0], "r", encoding='gbk') as file:
    content = file.readlines()
    content = [i.split('\n')[0] for i in content]
frec_list = []
for i in content[3:]:
    j = i.split('\t')
    frec_list.append(j)
frec_df = pd.DataFrame(frec_list, columns=content[2].split('\t'))
frec_df['Word'] = frec_df['Word'].astype(str)
frec_df['WCount'] = pd.to_numeric(frec_df['WCount'], errors='coerce').fillna(1).astype(int)
frecuencia = dict(zip(frec_df['Word'], frec_df['WCount']))

# ------------------------------------------------------------
# Grafo de caracteres (2‑caracteres, no dirigido, pesos)
# ------------------------------------------------------------
print("Construyendo grafo de caracteres...")
caracteres2 = diccionario[diccionario['simplificado'].apply(len)==2]

def grafo_caracteres(df_palabras, pesos=True):
    G = nx.Graph()
    pesos_dict = defaultdict(float)
    for _, row in df_palabras.iterrows():
        palabra = row['simplificado']
        chars = list(palabra)
        freq = frecuencia.get(palabra,1) if pesos else 1
        for i in range(len(chars)-1):
            a, b = chars[i], chars[i+1]
            if a <= b:
                pesos_dict[(a,b)] += freq
            else:
                pesos_dict[(b,a)] += freq
    for (u,v), w in pesos_dict.items():
        G.add_edge(u, v, weight=w)
    return G

G_car = grafo_caracteres(caracteres2, pesos=True)
print(f"Grafo caracteres: {G_car.number_of_nodes()} nodos, {G_car.number_of_edges()} aristas")

# ------------------------------------------------------------
# Grafo de Carroll (top 10k palabras)
# ------------------------------------------------------------
print("Construyendo grafo de Carroll...")
top_words = set(frec_df.nlargest(10000,'WCount')['Word'])
palabras_2 = diccionario[diccionario['simplificado'].apply(len)==2]
mask = palabras_2['simplificado'].isin(top_words)
palabras_2_top = palabras_2[mask]

def grafo_carroll(df):
    G = nx.Graph()
    for _, row in df.iterrows():
        w = row['simplificado']
        G.add_node(w, frecuencia=frecuencia.get(w,1))
    for pos in [0,1]:
        grupos = defaultdict(list)
        for w in G.nodes():
            clave = w[:pos] + '*' + w[pos+1:]
            grupos[clave].append(w)
        for lista in grupos.values():
            n = len(lista)
            if n<2: continue
            for i in range(n):
                wi=lista[i]; fi=frecuencia.get(wi,1)
                for j in range(i+1,n):
                    wj=lista[j]
                    if G.has_edge(wi,wj): continue
                    fj=frecuencia.get(wj,1)
                    G.add_edge(wi,wj, weight=min(fi,fj))
    return G

G_carroll = grafo_carroll(palabras_2_top)
print(f"Grafo Carroll (top 10k): {G_carroll.number_of_nodes()} nodos, {G_carroll.number_of_edges()} aristas")

csv_car = 'resultados_WDkS.csv'
csv_carroll = 'resultados_WDkS_carroll.csv'

if not os.path.exists(csv_car):
    raise FileNotFoundError(f"Falta {csv_car}")
if not os.path.exists(csv_carroll):
    raise FileNotFoundError(f"Falta {csv_carroll}")

curva_car = pd.read_csv(csv_car).sort_values('fraccion')
curva_carroll = pd.read_csv(csv_carroll).sort_values('fraccion')

def peso_total_grafo(G):
    return sum(d['weight'] for _,_,d in G.edges(data=True))

peso_total_car = peso_total_grafo(G_car)
peso_total_carroll = peso_total_grafo(G_carroll)

if 'cobertura_pct' not in curva_car.columns:
    curva_car['cobertura_pct'] = 100 * curva_car['weight'] / peso_total_car
if 'cobertura_pct' not in curva_carroll.columns:
    curva_carroll['cobertura_pct'] = 100 * curva_carroll['weight'] / peso_total_carroll

fig, (ax1, ax2) = plt.subplots(1,2,figsize=(14,6))
ax1.plot(curva_car['fraccion']*100, curva_car['cobertura_pct'],
         color=colores_caracter, lw=2.5, label='Caracteres')
ax1.plot(curva_carroll['fraccion']*100, curva_carroll['cobertura_pct'],
         color=colores_carroll, lw=2.5, label='Carroll')
ax1.set_xlabel('% de nodos seleccionados')
ax1.set_ylabel('Cobertura de peso (%)')
ax1.set_title('WDkS: Cobertura vs fracción')
ax1.legend(); ax1.grid(True, alpha=0.3)

ax2.plot(curva_car['k'], 100-curva_car['cobertura_pct'],
         color=colores_caracter, lw=2.5, label='Caracteres')
ax2.plot(curva_carroll['k'], 100-curva_carroll['cobertura_pct'],
         color=colores_carroll, lw=2.5, label='Carroll')
ax2.set_xlabel('k (número de nodos seleccionados)')
ax2.set_ylabel('% no cubierto (100-P)')
ax2.set_title('WDkS: Complemento')
ax2.legend(); ax2.grid(True, alpha=0.3)
ax2.set_xscale('log'); ax2.set_yscale('log')

plt.tight_layout()
plt.savefig('comparacion_wdks.png', dpi=200)
plt.show()

print("\n✅ Comparación WDkS completada.")