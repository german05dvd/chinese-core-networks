import os
import numpy as np
import networkx as nx
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from collections import defaultdict

# ============================================
# CONFIGURACIÓN DE ESTILO (más limpio)
# ============================================
colores = {
    'fondo': '#FFFFFF',
    'grid': '#E5E5E5',
    'texto': '#1A1A1A',
    'curva1': '#1F77B4',   # Azul - WDkS
    'curva2': '#2C9E6E',   # Verde - punto óptimo
    'curva3': '#FF7F0E',   # Naranja - greedy
    'curva4': '#9467BD',   # Morado - aleatorio
    'linea_ref': '#BBBBBB',
}

plt.rcParams['axes.facecolor'] = '#FFFFFF'
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 11
plt.rcParams['axes.labelsize'] = 10

os.system('clear' if os.name == 'posix' else 'cls')

def path(fichero=''):
    return os.path.join(f"paquetes/{fichero}")

print("cargando datos")
nombres = [path(i) for i in os.listdir("paquetes/")]
print(nombres)

# ------------------------------------------------------------
# Cargar diccionario CEDICT (último archivo en orden alfabético)
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
diccionario = pd.DataFrame(valores)
diccionario.columns = ['tradicional', 'simplificado', 'pinyin', 'significado']

# ------------------------------------------------------------
# Cargar frecuencias de CARACTERES (penúltimo archivo)
# ------------------------------------------------------------
with open(nombres[-2], "r", encoding='gbk') as file:
    content = file.readlines()
    content = [i.split('\n')[0] for i in content]
valores = []
for i in content[3:]:
    j = i.split('\t')
    valores.append(j)
caracteres = pd.DataFrame(valores)
caracteres.columns = content[2].split('\t')

# ------------------------------------------------------------
# Cargar frecuencias de PALABRAS (primer archivo - SUBTLEX)
# ------------------------------------------------------------
with open(nombres[0], "r", encoding='gbk') as file:
    content = file.readlines()
    content = [i.split('\n')[0] for i in content]
valores, longitudes2 = [], []
for i in content[3:]:
    j = i.split('\t')
    longitudes2.append(len(j[0]))
    valores.append(j)
palabras = pd.DataFrame(valores)
palabras.columns = content[2].split('\t')

print("construyendo grafo")
palabras['Word'] = palabras['Word'].astype(str)
palabras['WCount'] = pd.to_numeric(palabras['WCount'], errors='coerce').fillna(0).astype(int)
frecuencia = dict(zip(palabras['Word'], palabras['WCount']))
diccionario['simplificado'] = diccionario['simplificado'].astype(str)

caracteres2 = diccionario[diccionario['simplificado'].apply(len) == 2]

def grafo(palabras_df, pesos=True, direccionado=True):
    if direccionado:
        G = nx.DiGraph()
    else:
        G = nx.Graph()
    pesos_dict = defaultdict(float)
    for _, row in palabras_df.iterrows():
        palabra = row['simplificado']
        chars = list(palabra)
        freq = frecuencia.get(palabra, 1) if pesos else 1
        for i in range(len(chars)-1):
            a, b = chars[i], chars[i+1]
            if direccionado:
                pesos_dict[(a, b)] += freq
            else:
                if a <= b:
                    pesos_dict[(a, b)] += freq
                else:
                    pesos_dict[(b, a)] += freq
    for (u, v), w in pesos_dict.items():
        G.add_edge(u, v, weight=w)
    return G

grafo2 = grafo(caracteres2, pesos=True, direccionado=False)
G = grafo2.to_undirected()

nodes = list(G.nodes())
n = len(nodes)
node_to_idx = {node: i for i, node in enumerate(nodes)}
idx_to_node = {i: node for i, node in enumerate(nodes)}

print(f"\ngrafo preparado:")
print(f"  nodos: {n}")
print(f"  aristas: {G.number_of_edges()}")

W = np.zeros((n, n))
for u, v, data in G.edges(data=True):
    i, j = node_to_idx[u], node_to_idx[v]
    weight = data.get('weight', 1.0)
    W[i, j] = weight
    W[j, i] = weight

print(f"  matriz w shape: {W.shape}")
print(f"  peso total: {W.sum() / 2:.0f}")

# ============================================
# ESTADÍSTICAS DE CENTRALIDAD PARA G2
# ============================================
print("\n--- Calculando métricas de centralidad para G2 ---")
grados_dict = dict(G.degree())
grado_medio = np.mean(list(grados_dict.values()))
print(f"Grado medio: {grado_medio:.2f}")

# Betweenness (usar k-sample para acelerar)
print("Calculando betweenness...")
k_sample = min(2000, len(G))
betweenness = nx.betweenness_centrality(G, k=k_sample, weight='weight', seed=42)

# Clustering
print("Calculando clustering...")
clustering = nx.clustering(G)

# Guardar métricas
df_metrics = pd.DataFrame({
    'nodo': list(G.nodes()),
    'grado': [grados_dict[n] for n in G.nodes()],
    'betweenness': [betweenness.get(n, 0) for n in G.nodes()],
    'clustering': [clustering.get(n, 0) for n in G.nodes()]
})
df_metrics.to_csv('estadisticas_g2.csv', index=False, encoding='utf-8-sig')
print("Métricas guardadas en estadisticas_g2.csv")

# ============================================
# GRÁFICOS DE ESTADÍSTICAS G2
# ============================================
fig, axes = plt.subplots(1, 3, figsize=(14, 4))

# Distribución de grado
axes[0].hist(df_metrics['grado'], bins=40, edgecolor='black', alpha=0.7, color='#FF6B35')
axes[0].set_title('Distribución de Grado Total\n$G_2$', fontsize=11)
axes[0].set_xlabel('Grado')
axes[0].set_ylabel('Frecuencia')
axes[0].grid(True, alpha=0.3)

# Distribución de betweenness (log)
bt_pos = df_metrics['betweenness'][df_metrics['betweenness'] > 0]
axes[1].hist(np.log10(bt_pos), bins=35, edgecolor='black', alpha=0.7, color='#2C9E6E')
axes[1].set_title('Distribución de Betweenness\n$G_2$', fontsize=11)
axes[1].set_xlabel('log$_{10}$(Betweenness)')
axes[1].set_ylabel('Frecuencia')
axes[1].grid(True, alpha=0.3)

# Grado vs Betweenness
mask = (df_metrics['grado'] > 0) & (df_metrics['betweenness'] > 0)
axes[2].scatter(df_metrics.loc[mask, 'grado'], df_metrics.loc[mask, 'betweenness'],
                alpha=0.4, s=6, color='#1F77B4')
axes[2].set_xscale('log')
axes[2].set_yscale('log')
axes[2].set_title('Grado vs Betweenness\n$G_2$', fontsize=11)
axes[2].set_xlabel('Grado total')
axes[2].set_ylabel('Betweenness')
axes[2].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('estadisticas_g2.png', dpi=200, bbox_inches='tight')
plt.show()
print("Figura estadisticas_g2.png guardada.")

# ------------------------------------------------------------
# Función para calcular la curva WDkS (n_h AUMENTADO para suavidad)
# ------------------------------------------------------------
def calcular_wdks(W, output_csv, n_h=200):  # <-- AUMENTADO de 50 a 200
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
        k = len(S_nodes)
        fraccion = k / n
        peso = sum(W[i, j] for i in S_nodes for j in S_nodes if i < j)
        resultados.append((k, fraccion, peso))

    # Envolvente convexa (máximo peso para cada fracción)
    df = pd.DataFrame(resultados, columns=['k', 'fraccion', 'weight'])
    df = df.sort_values('fraccion')
    grouped = {}
    for _, row in df.iterrows():
        f = round(row['fraccion'], 5)
        if f not in grouped or row['weight'] > grouped[f]['weight']:
            grouped[f] = row.to_dict()
    clean = pd.DataFrame(grouped.values()).sort_values('fraccion')
    clean[['k', 'fraccion', 'weight']].to_csv(output_csv, index=False)
    print(f"  Curva WDkS guardada en {output_csv} ({len(clean)} puntos)")

# ------------------------------------------------------------
csv_file = 'resultados_WDkS.csv'
if os.path.exists(csv_file):
    print(f"\ncargando curva wdks desde {csv_file}")
else:
    print(f"\n{csv_file} no encontrado. Calculando (n_h=200, puede tardar ≈5-10 min)...")
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
idx_90 = np.argmin(np.abs(curva['cobertura_pct'] - 90))
punto_80 = curva.iloc[idx_80]
punto_90 = curva.iloc[idx_90]

print("resultados")
print(f"codo: {codo['k']:.0f} caracteres ({codo['fraccion']*100:.1f}%) → {codo['cobertura_pct']:.1f}% cobertura")
print(f"80% idioma: {punto_80['k']:.0f} caracteres ({punto_80['fraccion']*100:.1f}%)")
print(f"90% idioma: {punto_90['k']:.0f} caracteres ({punto_90['fraccion']*100:.1f}%)")

# ------------------------------------------------------------
# Preparar datos para gráficas
# ------------------------------------------------------------
k_values = curva['k'].values
not_covered = 100 - y_covered

k_prop = np.linspace(0, n, 500)
proportional_covered = (k_prop / n) * 100
proportional_not_covered = 100 - proportional_covered

# ------------------------------------------------------------
# Estrategias de comparación
# ------------------------------------------------------------
max_k = min(2000, n)
print(f"\nCalculando estrategias de comparación con {max_k} iteraciones...")

def calcular_peso_subgrafo(W, indices):
    return sum(W[i, j] for i in indices for j in indices if i < j)

grados = W.sum(axis=1)
orden_grado = np.argsort(grados)[::-1]
peso_acum_grado = [calcular_peso_subgrafo(W, orden_grado[:i+1]) for i in range(max_k)]
cob_grado = 100 * np.array([0] + peso_acum_grado) / peso_total
not_cob_grado = 100 - cob_grado

np.random.seed(42)
aleat_mejor = []
for rep in range(5):
    orden = np.random.permutation(n)
    pesos = [calcular_peso_subgrafo(W, orden[:i+1]) for i in range(max_k)]
    aleat_mejor.append([0] + pesos)
cob_aleat = 100 * np.mean(aleat_mejor, axis=0) / peso_total
not_cob_aleat = 100 - cob_aleat

k_wdks = (x_percent / 100) * n
not_covered_wdks = 100 - y_covered

# ============================================
# FIGURA ÚNICA CON 4 PANELES (log X solamente)
# ============================================
fig, axes = plt.subplots(2, 2, figsize=(12, 9), facecolor='white')
plt.subplots_adjust(hspace=0.35, wspace=0.3)

# Panel 1: Eficiencia (log X)
ax1 = axes[0, 0]
ax1.plot(k_values, not_covered, color=colores['curva1'], linewidth=2,
         marker='o', markersize=3, label='WDkS (óptimo)', zorder=2)
ax1.plot(k_prop, proportional_not_covered, '--', color=colores['linea_ref'],
         alpha=0.6, linewidth=1.5, label='Proporcional', zorder=1)
ax1.scatter(codo['k'], 100 - codo['cobertura_pct'], s=100, c=colores['curva2'],
            edgecolors='white', linewidth=1.5, zorder=3, label=f'Codo ($k^*\\approx${codo["k"]:.0f})')
ax1.set_xlabel('Número de caracteres ($k$)', fontsize=10)
ax1.set_ylabel('% Idioma NO cubierto ($100-P$)', fontsize=10)
ax1.set_title('Eficiencia de selección óptima', fontsize=11, fontweight='bold')
ax1.set_xlim(1, n)
ax1.set_ylim(0.1, 100)
ax1.set_xscale('log')
ax1.legend(loc='upper right', frameon=True, fontsize=9)
ax1.grid(True, alpha=0.3, linestyle='--', linewidth=0.7)
ax1.set_facecolor('white')

# Panel 2: Saturación
ax2 = axes[0, 1]
ax2.plot(curva['k'], curva['weight']/1e6, color=colores['curva2'],
         linewidth=2.5, marker='s', markersize=2.5, label='Peso acumulado')
ax2.axhline(y=curva['weight'].max()/1e6, color=colores['linea_ref'],
            linestyle='--', alpha=0.7, linewidth=1.5, label='Máximo')
ax2.set_xlabel('Número de caracteres ($k$)', fontsize=10)
ax2.set_ylabel('Peso acumulado ($\\times 10^6$)', fontsize=10)
ax2.set_title('Saturación del vocabulario', fontsize=11, fontweight='bold')
ax2.legend(loc='best', frameon=True, fontsize=9)
ax2.grid(True, alpha=0.3, linestyle='--', linewidth=0.7)
ax2.set_facecolor('white')

# Panel 3: Ganancia marginal
ax3 = axes[1, 0]
dx = np.diff(x_percent)
dy = np.diff(y_covered)
cambios = dx > 0.01
if np.sum(cambios) > 0:
    x_ef = x_percent[1:][cambios]
    ef = dy[cambios] / dx[cambios]
    ef = np.clip(ef, 0, 100)
    if len(ef) > 0:
        ax3.plot(x_ef, ef, color=colores['curva3'], linewidth=2.5, label='Ganancia marginal')
ax3.axhline(y=1, color=colores['linea_ref'], linestyle='--', alpha=0.7, linewidth=1.5, label='Umbral (1%)')
ax3.set_xlabel('% Caracteres aprendidos', fontsize=10)
ax3.set_ylabel('Eficiencia marginal', fontsize=10)
ax3.set_title('Ganancia por carácter adicional', fontsize=11, fontweight='bold')
ax3.set_xlim(0, 30)
ax3.legend(loc='upper right', frameon=True, fontsize=9)
ax3.grid(True, alpha=0.3, linestyle='--', linewidth=0.7)
ax3.set_facecolor('white')

# Panel 4: Comparación de estrategias (log X)
ax4 = axes[1, 1]
k_greedy = np.arange(1, max_k + 1)
ax4.plot(k_greedy, not_cob_grado[1:], '--', color=colores['curva3'],
         linewidth=2, label='Greedy (por grado)', alpha=0.9)
ax4.plot(k_greedy, not_cob_aleat[1:], ':', color=colores['curva4'],
         linewidth=2, label='Aleatorio (promedio)', alpha=0.9)
mask = k_wdks > 0
ax4.plot(k_wdks[mask], not_covered_wdks[mask], color=colores['curva1'],
         linewidth=2.5, label='WDkS (óptimo)')
ax4.set_xlabel('Número de caracteres seleccionados ($k$)', fontsize=10)
ax4.set_ylabel('% Idioma NO cubierto', fontsize=10)
ax4.set_title('Comparación de estrategias', fontsize=11, fontweight='bold')
ax4.set_xlim(1, max_k)
ax4.set_ylim(0.1, 100)
ax4.set_xscale('log')
ax4.legend(loc='upper right', frameon=True, fontsize=9)
ax4.grid(True, alpha=0.3, linestyle='--', linewidth=0.7)
ax4.set_facecolor('white')

plt.tight_layout()
plt.savefig('figura_principal_wdks.png', dpi=250, bbox_inches='tight', facecolor='white')
plt.show()
print("\n✅ Figura principal guardada: figura_principal_wdks.png")

# ============================================
# FIGURA COMPARATIVA G2 vs CARROLL (solo si existe curva de Carroll)
# ============================================
csv_carroll = 'resultados_WDkS_carroll.csv'
if os.path.exists(csv_carroll):
    curva_carroll = pd.read_csv(csv_carroll).sort_values('fraccion').reset_index(drop=True)
    
    # Necesitamos peso_total de Carroll - asumimos que está calculado o lo leemos
    # Por ahora, asumimos que la columna cobertura_pct ya existe o la calculamos
    # Si no existe, necesitaríamos el peso total del grafo Carroll
    
    fig, ax = plt.subplots(1, 1, figsize=(8, 5), facecolor='white')
    
    ax.plot(curva['fraccion']*100, curva['cobertura_pct'],
            color=colores['curva1'], lw=2.5, label='$G_2$ (caracteres)')
    ax.plot(curva_carroll['fraccion']*100, curva_carroll['cobertura_pct'],
            color=colores['curva2'], lw=2.5, label='$G_{\\mathrm{Carroll}}$ (palabras)')
    
    ax.set_xlabel('% de nodos seleccionados', fontsize=11)
    ax.set_ylabel('Cobertura de peso (%)', fontsize=11)
    ax.set_title('WDkS: $G_2$ vs $G_{\\mathrm{Carroll}}$', fontsize=12, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    
    plt.tight_layout()
    plt.savefig('comparacion_g2_carroll.png', dpi=250, bbox_inches='tight')
    plt.show()
    print("Figura comparativa guardada: comparacion_g2_carroll.png")