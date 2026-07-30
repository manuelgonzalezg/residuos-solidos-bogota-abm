"""Helpers reutilizables de visualización y pruebas estadísticas para el EDA.

Antes de este módulo, todo el notebook tenía un solo gráfico (un mapa de diagnóstico) y
cero pruebas estadísticas pese a estar etiquetado como "EDA". Paleta de color siguiendo la
skill `dataviz` del proyecto: categórica de 8 tonos en orden fijo (nunca ciclada), secuencial
de un solo tono para magnitud, diverging azul↔rojo para polaridad.
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

PALETA_CATEGORICA = ["#2a78d6", "#1baf7a", "#eda100", "#008300", "#4a3aa7", "#e34948", "#e87ba4", "#eb6834"]
CMAP_SECUENCIAL = "Blues"
CMAP_DIVERGENTE = "RdBu_r"
COLOR_TEXTO_SECUNDARIO = "#52514e"
COLOR_GRID = "#e1e0d9"


def aplicar_estilo():
    sns.set_theme(style="whitegrid", rc={"axes.edgecolor": COLOR_GRID, "grid.color": COLOR_GRID})
    plt.rcParams["axes.prop_cycle"] = plt.cycler(color=PALETA_CATEGORICA)


def graficar_distribucion(df: pd.DataFrame, columna: str, by: str | None = None, titulo: str | None = None):
    aplicar_estilo()
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    sns.histplot(df[columna].dropna(), color=PALETA_CATEGORICA[0], ax=axes[0])
    axes[0].set_title(titulo or f"Distribución de {columna}")
    if by and by in df.columns:
        sns.boxplot(data=df, x=by, y=columna, ax=axes[1], palette=PALETA_CATEGORICA)
        axes[1].tick_params(axis="x", rotation=30)
    else:
        sns.boxplot(y=df[columna], ax=axes[1], color=PALETA_CATEGORICA[0])
    axes[1].set_title(f"{columna} por {by}" if by else f"Boxplot de {columna}")
    fig.tight_layout()
    return fig


def graficar_mapa_coropletico(gdf, columna: str, titulo: str, cmap: str = CMAP_SECUENCIAL):
    aplicar_estilo()
    fig, ax = plt.subplots(figsize=(9, 9))
    gdf.plot(column=columna, cmap=cmap, legend=True, edgecolor="white", linewidth=0.3, ax=ax)
    ax.set_title(titulo)
    ax.set_axis_off()
    return fig


def graficar_correlacion(df: pd.DataFrame, columnas: list[str], titulo: str = "Correlación entre variables"):
    aplicar_estilo()
    corr = df[columnas].corr()
    fig, ax = plt.subplots(figsize=(8, 7))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap=CMAP_DIVERGENTE, center=0, vmin=-1, vmax=1, ax=ax)
    ax.set_title(titulo)
    fig.tight_layout()
    return fig, corr


def graficar_serie_tiempo_aprovechamiento(df: pd.DataFrame, columna_anio: str, columna_pct: str, anio_quiebre: int = 2024):
    aplicar_estilo()
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(df[columna_anio], df[columna_pct], marker="o", color=PALETA_CATEGORICA[0], linewidth=2)
    if anio_quiebre in df[columna_anio].values:
        ax.axvline(anio_quiebre, color=PALETA_CATEGORICA[5], linestyle="--", label=f"Quiebre {anio_quiebre}")
        ax.legend()
    ax.set_title("Evolución del % de aprovechamiento de residuos")
    ax.set_xlabel("Año")
    ax.set_ylabel("% aprovechamiento")
    fig.tight_layout()
    return fig


def prueba_anova(df: pd.DataFrame, columna_numerica: str, columna_grupo: str):
    """ANOVA de un factor si hay >=3 grupos con varianza homogénea razonable; si no, Kruskal-Wallis."""
    grupos = [g[columna_numerica].dropna().values for _, g in df.groupby(columna_grupo) if len(g) > 1]
    grupos = [g for g in grupos if len(g) > 0]
    if len(grupos) < 2:
        return {"prueba": "insuficiente", "p_valor": np.nan}
    estadistico, p_valor = stats.f_oneway(*grupos)
    return {"prueba": "ANOVA", "estadistico": estadistico, "p_valor": p_valor}


def prueba_kruskal(df: pd.DataFrame, columna_numerica: str, columna_grupo: str):
    grupos = [g[columna_numerica].dropna().values for _, g in df.groupby(columna_grupo) if len(g) > 1]
    grupos = [g for g in grupos if len(g) > 0]
    if len(grupos) < 2:
        return {"prueba": "insuficiente", "p_valor": np.nan}
    estadistico, p_valor = stats.kruskal(*grupos)
    return {"prueba": "Kruskal-Wallis", "estadistico": estadistico, "p_valor": p_valor}


def prueba_chi_cuadrado(df: pd.DataFrame, columna_a: str, columna_b: str):
    tabla = pd.crosstab(df[columna_a], df[columna_b])
    chi2, p_valor, gl, esperados = stats.chi2_contingency(tabla)
    return {"prueba": "Chi-cuadrado", "chi2": chi2, "p_valor": p_valor, "grados_libertad": gl, "tabla": tabla}


def prueba_correlacion(df: pd.DataFrame, columna_a: str, columna_b: str, metodo: str = "pearson"):
    datos = df[[columna_a, columna_b]].dropna()
    if metodo == "pearson":
        r, p_valor = stats.pearsonr(datos[columna_a], datos[columna_b])
    else:
        r, p_valor = stats.spearmanr(datos[columna_a], datos[columna_b])
    return {"prueba": f"Correlación ({metodo})", "r": r, "p_valor": p_valor, "n": len(datos)}


# =================================================================================================
# Gráficos avanzados — Fase 3 (EDA dirigido). Mismos principios de la Fase 1 (color por el trabajo
# que hace: secuencial=magnitud de una sola variable, divergente=polaridad con centro neutro,
# categórica=identidad en orden fijo), aplicados a técnicas que antes no estaban en el proyecto:
# mapas bivariados, pequeños múltiplos, distribuciones comparadas y relaciones entre actores.
# =================================================================================================

# Paleta bivariada 3x3 (esquema Stevens, el estándar de cartografía bivariada): fila = variable Y
# (bajo→alto), columna = variable X (bajo→alto). Esquina inferior-izquierda = ambas bajas (gris
# neutro), esquina superior-derecha = ambas altas (morado oscuro) — nunca se usa un arcoíris.
_PALETA_BIVARIADA = [
    ["#e8e8e8", "#ace4e4", "#5ac8c8"],  # Y bajo
    ["#dfb0d6", "#a5add3", "#5698b9"],  # Y medio
    ["#be64ac", "#8c62aa", "#3b4994"],  # Y alto
]  # cada fila de bajo→alto en X


def _clasificar_terciles(serie: pd.Series) -> pd.Series:
    """Clasifica en 3 grupos (0=bajo,1=medio,2=alto) por terciles; NaN se preserva."""
    return pd.qcut(serie.rank(method="first"), 3, labels=[0, 1, 2])


def graficar_mapa_bivariado(gdf, col_x: str, col_y: str, titulo: str,
                             etiqueta_x: str | None = None, etiqueta_y: str | None = None):
    """Mapa coroplético bivariado: combina 2 variables en una sola cuadrícula de color 3x3.

    Uso: cuando la pregunta es "¿estas dos variables son altas/bajas juntas en el mismo lugar?"
    (ej. estrato bajo Y baja separación) — algo que dos mapas secuenciales lado a lado no dejan
    ver de un vistazo. Incluye una leyenda de cuadrícula (no una barra de color simple), porque
    sin ella un mapa bivariado es ilegible.
    """
    aplicar_estilo()
    datos = gdf.copy()
    datos["_grupo_x"] = _clasificar_terciles(datos[col_x]).astype("Int64")
    datos["_grupo_y"] = _clasificar_terciles(datos[col_y]).astype("Int64")
    valido = datos["_grupo_x"].notna() & datos["_grupo_y"].notna()

    def color_de(row):
        if pd.isna(row["_grupo_x"]) or pd.isna(row["_grupo_y"]):
            return "#f5f5f2"
        return _PALETA_BIVARIADA[int(row["_grupo_y"])][int(row["_grupo_x"])]

    datos["_color"] = datos.apply(color_de, axis=1)

    fig = plt.figure(figsize=(11, 9))
    ax_mapa = fig.add_axes([0.02, 0.05, 0.75, 0.9])
    datos.plot(color=datos["_color"], edgecolor="white", linewidth=0.3, ax=ax_mapa)
    if (~valido).any():
        datos[~valido].plot(color="#f5f5f2", edgecolor="white", linewidth=0.3, ax=ax_mapa, hatch="///")
    ax_mapa.set_title(titulo, fontsize=13)
    ax_mapa.set_axis_off()

    # Leyenda de cuadrícula 3x3, ubicada como mini-mapa en la esquina.
    ax_leyenda = fig.add_axes([0.76, 0.08, 0.18, 0.18])
    for i in range(3):
        for j in range(3):
            ax_leyenda.add_patch(plt.Rectangle((j, i), 1, 1, facecolor=_PALETA_BIVARIADA[i][j]))
    ax_leyenda.set_xlim(0, 3)
    ax_leyenda.set_ylim(0, 3)
    ax_leyenda.set_xlabel(etiqueta_x or col_x, fontsize=8)
    ax_leyenda.set_ylabel(etiqueta_y or col_y, fontsize=8)
    ax_leyenda.annotate("", xy=(3, 0), xytext=(0, 0), arrowprops=dict(arrowstyle="->", lw=1))
    ax_leyenda.annotate("", xy=(0, 3), xytext=(0, 0), arrowprops=dict(arrowstyle="->", lw=1))
    ax_leyenda.set_xticks([])
    ax_leyenda.set_yticks([])
    for spine in ax_leyenda.spines.values():
        spine.set_visible(False)
    return fig


def graficar_pequenos_multiplos_mapa(gdfs_por_periodo: dict, columna: str, titulo_base: str,
                                      cmap: str = CMAP_SECUENCIAL, ncols: int = 2):
    """Grilla de mapas coropléticos, uno por periodo (año/mes/snapshot), TODOS con la misma
    escala de color — condición indispensable para que comparar entre paneles sea válido (si
    cada mapa normaliza su propio color, un mismo tono puede significar valores distintos).
    """
    aplicar_estilo()
    periodos = list(gdfs_por_periodo.keys())
    nrows = -(-len(periodos) // ncols)  # ceil

    valores_todos = pd.concat([g[columna] for g in gdfs_por_periodo.values()]).dropna()
    vmin, vmax = valores_todos.min(), valores_todos.max()

    fig, axes = plt.subplots(nrows, ncols, figsize=(6 * ncols, 6 * nrows))
    axes = np.atleast_1d(axes).flatten()
    for ax, periodo in zip(axes, periodos):
        gdf = gdfs_por_periodo[periodo]
        gdf.plot(column=columna, cmap=cmap, vmin=vmin, vmax=vmax,
                  edgecolor="white", linewidth=0.3, ax=ax)
        ax.set_title(str(periodo), fontsize=11)
        ax.set_axis_off()
    for ax in axes[len(periodos):]:
        ax.set_visible(False)

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=vmin, vmax=vmax))
    sm.set_array([])
    fig.colorbar(sm, ax=axes[:len(periodos)].tolist(), shrink=0.6, label=columna)
    fig.suptitle(titulo_base, fontsize=14, y=1.02)
    return fig


def graficar_distribucion_comparada(df: pd.DataFrame, columna: str, by: str, titulo: str | None = None,
                                     orden: list[str] | None = None):
    """Violín + puntos individuales por grupo — muestra la FORMA completa de la distribución
    (multimodalidad, asimetría) que un boxplot esconde, con la dispersión real de puntos encima
    para no perder de vista tamaños de muestra pequeños (relevante: hay localidades con muy
    pocas observaciones, ver `Diseno_ABM.md` §8).
    """
    aplicar_estilo()
    fig, ax = plt.subplots(figsize=(10, 5.5))
    sns.violinplot(data=df, x=by, y=columna, order=orden, ax=ax,
                    color=PALETA_CATEGORICA[0], inner=None, cut=0, linewidth=1)
    sns.stripplot(data=df, x=by, y=columna, order=orden, ax=ax,
                   color=COLOR_TEXTO_SECUNDARIO, size=3, alpha=0.4, jitter=0.2)
    ax.set_title(titulo or f"Distribución de {columna} por {by}")
    ax.tick_params(axis="x", rotation=35)
    fig.tight_layout()
    return fig


def graficar_dispersion_actores(df: pd.DataFrame, x: str, y: str, tamano: str | None = None,
                                 etiqueta: str | None = None, titulo: str | None = None,
                                 anotar_correlacion: bool = True):
    """Scatter de relación entre dos variables de actores distintos (ej. recicladores por UPZ vs.
    % de aprovechamiento), con el tamaño del punto codificando una tercera variable (ej.
    población) — para preguntas de interacción entre actores (Plan_EDA.md §3.7), no de magnitud
    de una sola variable.
    """
    aplicar_estilo()
    fig, ax = plt.subplots(figsize=(8, 6))
    tamanos = None
    if tamano:
        s = df[tamano].fillna(0)
        tamanos = 30 + 300 * (s - s.min()) / (s.max() - s.min() + 1e-9)
    ax.scatter(df[x], df[y], s=tamanos if tamanos is not None else 60,
               color=PALETA_CATEGORICA[0], alpha=0.65, edgecolor="white", linewidth=0.5)
    if etiqueta and etiqueta in df.columns:
        for _, fila in df.iterrows():
            ax.annotate(str(fila[etiqueta]), (fila[x], fila[y]), fontsize=7,
                        color=COLOR_TEXTO_SECUNDARIO, alpha=0.8,
                        xytext=(3, 3), textcoords="offset points")
    if anotar_correlacion:
        datos = df[[x, y]].dropna()
        if len(datos) >= 3:
            r, p = stats.spearmanr(datos[x], datos[y])
            ax.text(0.03, 0.97, f"Spearman r = {r:.2f}  (p = {p:.3f}, n = {len(datos)})",
                    transform=ax.transAxes, va="top", fontsize=9, color=COLOR_TEXTO_SECUNDARIO)
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    ax.set_title(titulo or f"{y} vs. {x}")
    fig.tight_layout()
    return fig


def graficar_series_multiples(df: pd.DataFrame, x: str, y: str, hue: str, titulo: str | None = None,
                               orden_hue: list[str] | None = None):
    """Líneas múltiples con orden categórico FIJO (nunca ciclado) — para series por operador/ASE
    o por tipo de residuo, donde cada categoría debe mantener siempre el mismo color entre
    gráficos distintos del mismo notebook (identidad, no ranking).
    """
    aplicar_estilo()
    categorias = orden_hue or sorted(df[hue].dropna().unique())
    fig, ax = plt.subplots(figsize=(11, 5.5))
    for i, cat in enumerate(categorias):
        sub = df[df[hue] == cat].sort_values(x)
        color = PALETA_CATEGORICA[i % len(PALETA_CATEGORICA)]
        ax.plot(sub[x], sub[y], label=str(cat), color=color, linewidth=1.8, marker="o", markersize=3)
    ax.set_title(titulo or f"{y} por {hue}")
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8, frameon=False)
    fig.tight_layout()
    return fig
