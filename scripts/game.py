# Juego de Carroll, estudio de la conexión formando palabras, cambiando solo un carácter por paso
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
from collections import defaultdict

# Configuración de estilo (verde para Carroll)
colores = {
    'fondo': '#F8F9FA',
    'grid': '#DEE2E6',
    'texto': '#212529',
    'curva1': '#2C9E6E',   # Verde principal - WDkS
    'curva2': '#28A745',   # Verde claro - punto óptimo
    'curva3': '#20C997',   # Turquesa - greedy
    'curva4': '#6C757D',   # Gris - aleatorio
    'linea_ref': '#ADB5BD',
}

plt.rcParams['axes.facecolor'] = '#FAFAFA'
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 11
plt.rcParams['axes.labelsize'] = 10

def path(fichero=''):
    return os.path.join("paquetes", fichero)

os.system('clear')
nombres = [path(i) for i in os.listdir("paquetes/")]

# ------------------------------------------------------------
# Cargar diccionario y frecuencias
# ------------------------------------------------------------
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

with open(nombres[0], "r", encoding='gbk') as file:
    content = file.readlines()
    content = [i.split('\n')[0] for i in content]
frecuencia = []
for i in content[3:]:         
    j = i.split('\t')
    frecuencia.append(j)

frecuencia = pd.DataFrame(frecuencia, columns=content[2].split('\t'))
frecuencia['Word'] = frecuencia['Word'].astype(str)
frecuencia['WCount'] = pd.to_numeric(frecuencia['WCount'], errors='coerce').fillna(1).astype(int)
frecuencia = dict(zip(frecuencia['Word'], frecuencia['WCount']))

diccionario = pd.DataFrame(valores)
diccionario.columns = ['tradicional', 'simplificado', 'pinyin', 'significado']
diccionario['simplificado'] = diccionario['simplificado'].astype(str)
diccionario['tradicional'] = diccionario['tradicional'].astype(str)

longitudes = [len(i) for i in diccionario['simplificado']]
larga = max(longitudes)

palabras = [diccionario[diccionario['simplificado'].apply(len) == i] for i in range(2, larga+1)]
print(f'\nSobre las palabras: \nvalor máximo: {larga}')
for i in diccionario['simplificado']:
    if len(i) == 19:
        print(f'palabra más larga: {i}')
    if len(i) == 17:
        print(f'palabra 17: {i}')

print(f'\nCaracteres x cantidad')
for i in range(len(palabras)):
    print(f'{i+2}-> {len(palabras[i])}')

# ------------------------------------------------------------
# Función para construir grafo de Carroll (2 caracteres)
# ------------------------------------------------------------
def grafo(palabras_df):
    G = nx.Graph()
    for _, row in palabras_df.iterrows():
        w = row['simplificado']
        freq = frecuencia.get(w, 1)
        G.add_node(w, frecuencia=freq)

    primero = defaultdict(list)
    for w in G.nodes():
        clave = '*' + w[1]
        primero[clave].append(w)
    segundo = defaultdict(list)
    for w in G.nodes():
        clave = w[0] + '*'
        segundo[clave].append(w)

    for grupos in [primero, segundo]:
        for lista in grupos.values():
            n = len(lista)
            if n < 2:
                continue
            for i in range(n):
                wi = lista[i]
                fi = frecuencia.get(wi, 1)
                for j in range(i+1, n):
                    wj = lista[j]
                    if G.has_edge(wi, wj):
                        continue
                    fj = frecuencia.get(wj, 1)
                    peso = min(fi, fj)
                    G.add_edge(wi, wj, weight=peso)
    return G

# Grafo completo (solo informativo)
juego_completo = grafo(palabras[0])
print(f"\ncarroll(2) completo: {juego_completo.number_of_nodes()} nodos, {juego_completo.number_of_edges()} aristas")

grados = dict(juego_completo.degree())
medio = sum(grados.values()) / len(grados)
print(f"grado medio: {medio:.1f} \ntop5 nodos por grado:")
top = sorted(grados.items(), key=lambda x: x[1], reverse=True)[:5]
for nodo, grado in top:
    print(f"->  {nodo}: grado {grado}")

# ------------------------------------------------------------
# Grafo para análisis (top 10k palabras más frecuentes)
# ------------------------------------------------------------
usadas = set(pd.DataFrame(list(frecuencia.items()), columns=['Word','Freq'])
                .nlargest(10000, 'Freq')['Word'])
mask = palabras[0]['simplificado'].isin(usadas)
usadas_df = palabras[0][mask]

juego = grafo(usadas_df)
print(f"\nTop 10k para 2 caracteres:\nnodos: {juego.number_of_nodes()}, aristas: {juego.number_of_edges()}")

# ------------------------------------------------------------
# Estadísticas del grafo
# ------------------------------------------------------------
def estadisticas_grafo(G, nombre):
    cc = list(nx.connected_components(G))
    giant = max(cc, key=len)
    G_giant = G.subgraph(giant).copy()
    print(f"\n--- {nombre} ---")
    print(f"Componente gigante: {len(giant)} nodos ({100*len(giant)/G.number_of_nodes():.1f}%)")

    grados = dict(G.degree())
    grado_medio = np.mean(list(grados.values()))
    print(f"Grado medio: {grado_medio:.2f} | Grado máximo: {max(grados.values())}")

    clust = nx.clustering(G)
    clustering_medio = nx.average_clustering(G)
    print(f"Clustering medio: {clustering_medio:.4f}")

    print("Calculando betweenness (puede tardar un poco)...")
    k_sample = min(1000, len(G_giant))
    betweenness = nx.betweenness_centrality(G_giant, k=k_sample, weight='weight', seed=42)
    full_betweenness = {node: betweenness.get(node, 0.0) for node in G.nodes()}

    try:
        ecc = nx.eccentricity(G_giant)
        radio = min(ecc.values())
        diametro = max(ecc.values())
        jordan = [n for n, e in ecc.items() if e == radio]
        print(f"Radio: {radio} | Diámetro: {diametro}")
        print(f"Centro de Jordan (primeros 5): {jordan[:5]}")
    except Exception as e:
        print("No se pudo calcular excentricidad:", e)
        ecc = {}

    df_metrics = pd.DataFrame(index=list(G.nodes()))
    df_metrics['grado'] = df_metrics.index.map(grados)
    df_metrics['clustering'] = df_metrics.index.map(clust)
    df_metrics['betweenness'] = df_metrics.index.map(full_betweenness)
    df_metrics['excentricidad'] = np.nan
    for n, e in ecc.items():
        df_metrics.loc[n, 'excentricidad'] = e

    print("\nTop 10 por grado:")
    print(df_metrics.nlargest(10, 'grado')[['grado', 'clustering', 'betweenness']])
    print("\nTop 10 por betweenness:")
    print(df_metrics.nlargest(10, 'betweenness')[['betweenness', 'grado', 'clustering']])

    return df_metrics

nombre_grafo = "Carroll_2char"
df = estadisticas_grafo(juego, nombre_grafo)
df.to_csv(f"{nombre_grafo}_metricas.csv", encoding='utf-8-sig')
print(f"\nMétricas guardadas en {nombre_grafo}_metricas.csv")

# ------------------------------------------------------------
# Gráficos de estadísticas
# ------------------------------------------------------------
fig, axes = plt.subplots(1, 3, figsize=(15, 4))
axes[0].hist(df['grado'], bins=30, edgecolor='black', alpha=0.7, color='steelblue')
axes[0].set_title(f'Distribución de grado\n{nombre_grafo}')
axes[0].grid(True, alpha=0.3)

bt_pos = df['betweenness'][df['betweenness'] > 0]
if len(bt_pos) > 0:
    axes[1].hist(np.log10(bt_pos), bins=30, edgecolor='black', alpha=0.7, color='seagreen')
    axes[1].set_title(f'Betweenness (log10)\n{nombre_grafo}')
    axes[1].set_xlabel('log10(betweenness)')

mask = (df['grado'] > 0) & (df['betweenness'] > 0)
axes[2].scatter(df.loc[mask, 'grado'], df.loc[mask, 'betweenness'],
                alpha=0.5, s=8, color='darkorange')
axes[2].set_xscale('log'); axes[2].set_yscale('log')
axes[2].set_title(f'Grado vs Betweenness\n{nombre_grafo}')
axes[2].grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(f'{nombre_grafo}_estadisticas.png', dpi=150)
plt.show()

plt.figure(figsize=(6, 4))
plt.hist(df['clustering'].dropna(), bins=30, edgecolor='black', alpha=0.7, color='mediumpurple')
plt.title(f'Distribución de Clustering\n{nombre_grafo}')
plt.xlabel('Clustering coefficient')
plt.grid(True, alpha=0.3)
plt.savefig(f'{nombre_grafo}_clustering.png', dpi=150)
plt.show()

# ============================================================
# WDkS para el grafo de Carroll
# ============================================================
print("\n===== Preparando WDkS para Carroll =====")
nodes = list(juego.nodes())
n = len(nodes)
node_to_idx = {node: i for i, node in enumerate(nodes)}
idx_to_node = {i: node for i, node in enumerate(nodes)}

W = np.zeros((n, n))
for u, v, data in juego.edges(data=True):
    i, j = node_to_idx[u], node_to_idx[v]
    weight = data.get('weight', 1.0)
    W[i, j] = weight
    W[j, i] = weight

print(f"  nodos: {n}, aristas: {juego.number_of_edges()}")
print(f"  peso total: {W.sum() / 2:.0f}")

# Función calcular_wdks (n_h AUMENTADO a 200 para curvas suaves)
def calcular_wdks(W, output_csv, n_h=200):
    n = W.shape[0]
    total_weight = W.sum() / 2.0
    J = W / 4.0
    h_local = J.sum(axis=1)

    h_min = -1.5 * np.max(np.abs(h_local))
    h_max = 1.5 * np.max(np.abs(h_local))
    h_vals = np.linspace(h_min, h_max, n_h)

    resultados = []
    for idx_h, h in enumerate(h_vals):
        if idx_h % 20 == 0:
            print(f"  Barriendo h: {idx_h+1}/{n_h} (h={h:.2f})")

        G_cut = nx.DiGraph()
        G_cut.add_node('s')
        G_cut.add_node('t')
        for i in range(n):
            bi = h_local[i] + h
            if bi > 0:
                G_cut.add_edge('s', i, capacity=bi)
            elif bi < 0:
                G_cut.add_edge(i, 't', capacity=-bi)

        for i in range(n):
            for j in range(i+1, n):
                if J[i, j] > 0:
                    G_cut.add_edge(i, j, capacity=J[i, j])
                    G_cut.add_edge(j, i, capacity=J[i, j])

        cut_value, (S, T) = nx.minimum_cut(G_cut, 's', 't')
        S_nodes = set(S) - {'s'}
        selected = len(S_nodes)
        fraccion = selected / n

        peso = 0.0
        for i in S_nodes:
            for j in S_nodes:
                if i < j:
                    peso += W[i, j]

        resultados.append((selected, fraccion, peso))

    df = pd.DataFrame(resultados, columns=['k', 'fraccion', 'weight'])
    df = df.sort_values('fraccion')
    grouped = {}
    for _, row in df.iterrows():
        f = round(row['fraccion'], 6)
        if f not in grouped or row['weight'] > grouped[f]['weight']:
            grouped[f] = row.to_dict()
    clean_df = pd.DataFrame(grouped.values()).sort_values('fraccion')
    clean_df[['k', 'fraccion', 'weight']].to_csv(output_csv, index=False)
    print(f"  Curva WDkS guardada en {output_csv} ({len(clean_df)} puntos)")
    return output_csv

csv_file = 'resultados_WDkS_carroll.csv'
if os.path.exists(csv_file):
    print(f"\nCargando curva WDkS desde {csv_file}")
    curva = pd.read_csv(csv_file).sort_values('fraccion').reset_index(drop=True)
else:
    print(f"\n{csv_file} no encontrado. Calculando curva WDkS (n_h=200)...")
    calcular_wdks(W, csv_file, n_h=200)
    curva = pd.read_csv(csv_file).sort_values('fraccion').reset_index(drop=True)

peso_total = W.sum() / 2
if 'cobertura_pct' not in curva.columns:
    curva['cobertura_pct'] = 100 * curva['weight'] / peso_total

# ------------------------------------------------------------
# Cálculo de puntos clave
# ------------------------------------------------------------
x_percent = curva['fraccion'].values * 100
y_covered = curva['cobertura_pct'].values
distancias = np.abs(y_covered - x_percent) / np.sqrt(2)
idx_codo = np.argmax(distancias)
codo = curva.iloc[idx_codo]
idx_80 = np.argmin(np.abs(curva['cobertura_pct'] - 80))
punto_80 = curva.iloc[idx_80]
idx_90 = np.argmin(np.abs(curva['cobertura_pct'] - 90))
punto_90 = curva.iloc[idx_90]

print("Resultados WDkS Carroll:")
print(f"codo: {codo['k']:.0f} palabras ({codo['fraccion']*100:.1f}%) → {codo['cobertura_pct']:.1f}% cobertura")
print(f"80% idioma: {punto_80['k']:.0f} palabras ({punto_80['fraccion']*100:.1f}%)")
print(f"90% idioma: {punto_90['k']:.0f} palabras ({punto_90['fraccion']*100:.1f}%)")

k_values = curva['k'].values
not_covered = 100 - y_covered
k_prop = np.linspace(0, n, 500)
proportional_not_covered = 100 - (k_prop / n) * 100

max_k = min(2000, n)
print(f"Calculando estrategias de comparación (k≤{max_k})...")

def peso_subgrafo(W, indices):
    return sum(W[i, j] for i in indices for j in indices if i < j)

grados = W.sum(axis=1)
orden_grado = np.argsort(grados)[::-1]
peso_acum_grado = [peso_subgrafo(W, orden_grado[:i+1]) for i in range(max_k)]
cob_grado = 100 * np.array([0] + peso_acum_grado) / peso_total
not_cob_grado = 100 - cob_grado

np.random.seed(42)
aleat_mejor = []
for rep in range(5):
    orden = np.random.permutation(n)
    pesos = [peso_subgrafo(W, orden[:i+1]) for i in range(max_k)]
    aleat_mejor.append([0] + pesos)
cob_aleat = 100 * np.mean(aleat_mejor, axis=0) / peso_total
not_cob_aleat = 100 - cob_aleat

k_wdks = (x_percent / 100) * n
not_covered_wdks = 100 - y_covered

# ============================================================
# FUNCIÓN PARA CREAR FIGURA (solo log X, no múltiples variantes)
# ============================================================
def crear_figura_carroll(xscale, yscale, sufijo):
    fig, axes = plt.subplots(2, 2, figsize=(14,10), facecolor=colores['fondo'])
    plt.subplots_adjust(hspace=0.3, wspace=0.3)

    ax = axes[0,0]
    ax.plot(k_values, not_covered, color=colores['curva1'], lw=2.5, marker='o', ms=4, label='WDkS')
    ax.plot(k_prop, proportional_not_covered, '--', color=colores['linea_ref'], lw=1.5, label='Proporcional')
    ax.scatter(codo['k'], 100-codo['cobertura_pct'], s=80, c=colores['curva2'],
               edgecolors='white', zorder=3, label='Codo óptimo')
    ax.set_xlabel('Número de palabras (k)')
    ax.set_ylabel('% no cubierto (100-P)')
    ax.set_title(f'Carroll: Eficiencia ({sufijo})')
    ax.set_xlim(1, n); ax.set_ylim(0.1, 100)
    ax.set_xscale(xscale); ax.set_yscale(yscale)
    ax.legend(); ax.grid(True, alpha=0.3, color=colores['grid'])

    ax = axes[0,1]
    ax.plot(curva['k'], curva['weight'], color=colores['curva2'], lw=2.5, marker='s', ms=3, label='Peso acumulado')
    ax.axhline(curva['weight'].max(), color=colores['linea_ref'], lw=1.5, label='Máximo')
    ax.set_xlabel('k'); ax.set_ylabel('Peso acumulado')
    ax.set_title('Saturación del peso')
    ax.legend(); ax.grid(True, alpha=0.3, color=colores['grid'])

    ax = axes[1,0]
    dx = np.diff(x_percent); dy = np.diff(y_covered)
    cambios = dx > 0.01
    if np.sum(cambios) > 0:
        x_ef = x_percent[1:][cambios]
        ef = np.clip(dy[cambios]/dx[cambios], 0, 100)
        ax.plot(x_ef, ef, color=colores['curva3'], lw=2.5, label='Ganancia marginal')
    ax.axhline(1, color=colores['linea_ref'], lw=1.5, label='Umbral 1%')
    ax.set_xlabel('% palabras'); ax.set_ylabel('Eficiencia marginal')
    ax.set_title('Ganancia marginal')
    ax.set_xlim(0,30); ax.legend(); ax.grid(True, alpha=0.3, color=colores['grid'])

    ax = axes[1,1]
    k_greedy = np.arange(1, max_k+1)
    ax.plot(k_greedy, not_cob_grado[1:], '--', color=colores['curva4'], lw=2, label='Greedy')
    ax.plot(k_greedy, not_cob_aleat[1:], ':', color=colores['curva2'], lw=2, label='Aleatorio')
    mask = k_wdks > 0
    ax.plot(k_wdks[mask], not_covered_wdks[mask], color=colores['curva1'], lw=2.5, label='WDkS')
    ax.set_xlabel('k'); ax.set_ylabel('% no cubierto')
    ax.set_title(f'Comparación de estrategias ({sufijo})')
    ax.set_xlim(1, max_k); ax.set_ylim(0.1, 100)
    ax.set_xscale(xscale); ax.set_yscale(yscale)
    ax.legend(); ax.grid(True, alpha=0.3, color=colores['grid'])

    plt.tight_layout()
    return fig

# ============================================================
# GENERAR SOLO UNA FIGURA (log X) - ya no se generan 3 variantes
# ============================================================
print("Generando figura WDkS (Carroll)...")
fig = crear_figura_carroll('log', 'linear', 'log X')
fig.savefig('carroll_wdks.png', dpi=200, bbox_inches='tight')
plt.close(fig)

print("Carroll WDkS completado.\n")