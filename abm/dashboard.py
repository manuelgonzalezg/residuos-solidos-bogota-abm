"""Dashboard interactivo del ABM (Mesa + Solara) — panel de control en tiempo real.

Uso: desde la terminal, parado en la carpeta del proyecto ("EDA + ABM Residuos Bogota"):

    SOLARA_THEME_VARIANT=dark ../.venv/Scripts/solara run abm/dashboard.py

(En PowerShell: `$env:SOLARA_THEME_VARIANT="dark"; ../.venv/Scripts/solara run abm/dashboard.py`)

Abre una pestaña de navegador nueva (por defecto en http://localhost:8765). Los controles
Play/Step/Reset avanzan la simulación día a día — cada vez que avanza, todos los paneles se
redibujan solos (vía `update_counter`).

Rediseño 2026-07-13 ("centro de mando"): capa completa de diseño visual — tema oscuro, paleta
validada (ver skill `dataviz`, `references/palette.md`), tarjetas KPI reales (no tabla markdown),
mini-gráficos de tendencia, y un layout propio por pestañas en vez del `ComponentsView` por
defecto de Mesa (que agregaba una pestaña fantasma "Page 0" y apilaba todo en una sola columna
larga). Se probaron camiones ILUSTRATIVOS animados sobre las macrorutas reales, pero se retiraron
por decisión del usuario: sin dato real de GPS de flota ni de calles/rutas (ver
`Reglas_Negocio_v2_y_Modelado_Agentes.md` §4quater), mejor omitirlos que animar algo ilustrativo.
La resolución espacial real y verificable del modelo sigue siendo la UPZ (112 zonas), no la calle.

Rediseño 2026-07-13 (ronda 2, "panel de control estratégico"): reorganización en 4 pestañas por
audiencia — Resumen ejecutivo (todos), Escenarios y política (gobierno, con controles de
intervención dinámicos), Rigor y validación (comité de tesis, real-vs-simulado + sensibilidad de
parámetros), Cómo funciona el sistema (público general). Cualquier variable mostrada debe ser
trazable a dato real Y dinámica (responder a la simulación) — por eso el "incentivo económico"
(tarifa CRA, estática, no conectada causalmente a ningún mecanismo) se mantiene solo como panel
descriptivo en la pestaña de público general, no como control de escenario.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib as mpl
import numpy as np
import pandas as pd
import solara
import solara.lab
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.figure import Figure
from mesa.visualization.solara_viz import ModelController, ModelCreator, ShowSteps
from mesa.visualization.utils import force_update, update_counter
from shapely.geometry import Point as _ShapelyPoint

from abm import config_abm
from abm.agentes_hogar import HogarAgente
from abm.agentes_reciclador import PoblacionRecicladoresUPZ
from abm.modelo import ModeloResiduosBogota
from src import carga_datos
from src import config as config_datos

# =================================================================================================
# Paleta validada (skill "dataviz", references/palette.md) — tema oscuro
# =================================================================================================

SURFACE = "#1a1a19"        # superficie de gráfico, modo oscuro
PAGINA = "#0d0d0d"         # plano de página, modo oscuro
INK_PRIMARIO = "#ffffff"
INK_SECUNDARIO = "#c3c2b7"
INK_MUTED = "#898781"
GRILLA = "#2c2c2a"
LINEA_BASE = "#383835"
FONDO_SIN_DATO = "#2c2c2a"

AZUL = "#3987e5"      # categórico slot 1 (oscuro)
AQUA = "#199e70"      # categórico slot 2 (oscuro)
AMARILLO = "#c98500"
VIOLETA = "#9085e9"
ROJO = "#e66767"
MAGENTA = "#d55181"
NARANJA = "#d95926"

BUENO = "#0ca30c"
ADVERTENCIA = "#fab219"
CRITICO = "#d03b3b"

# Secuencial de un solo tono (azul), claro→oscuro — magnitud de % de aprovechamiento.
CMAP_APROVECHAMIENTO = LinearSegmentedColormap.from_list(
    "secuencial_azul", ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]
)
# Segundo tono secuencial (aqua) para no confundir visualmente con el mapa anterior —
# infraestructura real (SIGAB), misma lógica de "un solo tono, claro a oscuro".
CMAP_INFRAESTRUCTURA = LinearSegmentedColormap.from_list(
    "secuencial_aqua", ["#d7f3e7", "#8ad9bd", "#3fc496", "#1baf7a", "#0d7d54"]
)
# Divergente azul↔rojo con punto medio gris neutro — incentivo económico (subsidio vs. contribución).
CMAP_INCENTIVO = LinearSegmentedColormap.from_list(
    "divergente_azul_rojo", ["#104281", "#3987e5", "#f0efec", "#e66767", "#7a2020"]
)

mpl.rcParams["text.color"] = INK_PRIMARIO
mpl.rcParams["axes.edgecolor"] = LINEA_BASE
mpl.rcParams["axes.labelcolor"] = INK_SECUNDARIO
mpl.rcParams["xtick.color"] = INK_SECUNDARIO
mpl.rcParams["ytick.color"] = INK_SECUNDARIO


def _figura_oscura(figsize) -> tuple[Figure, "mpl.axes.Axes"]:
    """Figura matplotlib con el tema oscuro de la paleta aplicado (superficie, ejes, grilla)."""
    fig = Figure(figsize=figsize, facecolor=SURFACE)
    ax = fig.add_subplot()
    ax.set_facecolor(SURFACE)
    for spine in ax.spines.values():
        spine.set_color(LINEA_BASE)
    ax.tick_params(colors=INK_SECUNDARIO, labelsize=8)
    ax.grid(color=GRILLA, linewidth=0.6, alpha=0.7)
    ax.set_axisbelow(True)
    return fig, ax


def _mapa_oscuro(figsize) -> tuple[Figure, "mpl.axes.Axes"]:
    fig = Figure(figsize=figsize, facecolor=SURFACE)
    ax = fig.add_subplot()
    ax.set_facecolor(SURFACE)
    ax.set_axis_off()
    return fig, ax


def _colorear_colorbar(cbar_ax: "mpl.axes.Axes") -> None:
    """`cbar_ax` es la Axes que geopandas crea para la leyenda de color (`fig.axes[-1]`
    cuando se pasa `legend=True`) — no un objeto `Colorbar`, así que se estiliza como
    cualquier Axes normal (ticks, spines, label del eje y)."""
    cbar_ax.yaxis.set_tick_params(color=INK_SECUNDARIO, labelsize=7)
    for etiqueta in cbar_ax.get_yticklabels():
        etiqueta.set_color(INK_SECUNDARIO)
    cbar_ax.yaxis.label.set_color(INK_SECUNDARIO)
    for spine in cbar_ax.spines.values():
        spine.set_color(LINEA_BASE)


# =================================================================================================
# Datos base cargados UNA sola vez (no cambian entre pasos de la simulación)
# =================================================================================================

_GDF_UPZ_BASE = carga_datos.cargar_upz_limites()
_GDF_UPZ_BASE["CODIGO_UPZ"] = pd.to_numeric(_GDF_UPZ_BASE["CODIGO_UPZ"], errors="coerce")

# Margen (grados) alrededor de los límites reales de las 112 UPZ urbanas — cualquier capa
# superpuesta (hogares, puntos críticos) se filtra y se recorta a esta caja, para que ningún
# outlier geográfico pueda encoger el mapa visible (bug real encontrado y corregido 2026-07-13:
# los camiones ilustrativos que antes se mostraban aquí incluían, sin este filtro, zonas de
# Sumapaz y la extensión rural sur de Usme, muy fuera del área densa de las 112 UPZ — se
# retiraron los camiones del todo en la ronda siguiente, por decisión del usuario: sin dato real
# de flota, mejor omitirlos que animarlos de forma ilustrativa).
_MARGEN_BOGOTA_GRADOS = 0.02
_BOUNDS_BOGOTA = _GDF_UPZ_BASE.total_bounds  # [xmin, ymin, xmax, ymax]


def _dentro_de_bogota_urbano(x: float, y: float) -> bool:
    xmin, ymin, xmax, ymax = _BOUNDS_BOGOTA
    return (xmin - _MARGEN_BOGOTA_GRADOS) <= x <= (xmax + _MARGEN_BOGOTA_GRADOS) and \
           (ymin - _MARGEN_BOGOTA_GRADOS) <= y <= (ymax + _MARGEN_BOGOTA_GRADOS)


def _fijar_limites_bogota(ax) -> None:
    """Bloquea los ejes al encuadre real de las 112 UPZ urbanas. Sin esto, un solo punto fuera
    de rango en cualquier capa superpuesta hace que matplotlib autoescale para incluirlo,
    encogiendo la Bogotá urbana real a una esquina diminuta del lienzo."""
    xmin, ymin, xmax, ymax = _BOUNDS_BOGOTA
    ax.set_xlim(xmin - _MARGEN_BOGOTA_GRADOS, xmax + _MARGEN_BOGOTA_GRADOS)
    ax.set_ylim(ymin - _MARGEN_BOGOTA_GRADOS, ymax + _MARGEN_BOGOTA_GRADOS)


def _construir_puntos_criticos_reales() -> np.ndarray:
    """Puntos críticos REALES de acumulación de basura (SIGAB, snapshot dic-2024) — lat/lon
    reales, no simbólicos. Responde directamente a "ver cómo se acumula esa basura" con dato
    100% verificable (ver `Auditoria_Completa_Datos_Limpieza_EDA.md` §2.5)."""
    try:
        datos = carga_datos.cargar_sigab_snapshot("sigab_2024_diciembre")
        puntos = datos.get("puntos_criticos")
        if puntos is None:
            return np.empty((0, 2))
        lon = pd.to_numeric(puntos["LONGITUD"], errors="coerce")
        lat = pd.to_numeric(puntos["LATITUD"], errors="coerce")
        validos = lon.notna() & lat.notna()
        coords = np.column_stack([lon[validos].to_numpy(), lat[validos].to_numpy()])
        dentro = np.array([_dentro_de_bogota_urbano(x, y) for x, y in coords])
        return coords[dentro]
    except Exception:
        return np.empty((0, 2))


_PUNTOS_CRITICOS_REALES = _construir_puntos_criticos_reales()

# --- Hogares simbólicos por estrato (para el mapa) ---
# NO es GPS real de hogares individuales (no existe esa fuente) — son puntos generados
# aleatoriamente DENTRO del polígono real de cada UPZ, en una cantidad proporcional a la
# composición real de estrato de esa UPZ (`pct_estrato_bajo/medio/alto`, dato real de
# `df_modelo`). Semilla fija para que el patrón sea reproducible entre renders.
_PUNTOS_POR_UPZ_HOGARES = 10
_COLOR_ESTRATO = {"bajo": AMARILLO, "medio": VIOLETA, "alto": MAGENTA}


def _puntos_aleatorios_en_poligono(poligono, n: int, rng: np.random.Generator) -> list[tuple[float, float]]:
    if n <= 0:
        return []
    try:
        minx, miny, maxx, maxy = poligono.bounds
    except Exception:
        return []
    puntos, intentos = [], 0
    while len(puntos) < n and intentos < n * 50:
        x, y = rng.uniform(minx, maxx), rng.uniform(miny, maxy)
        intentos += 1
        if poligono.contains(_ShapelyPoint(x, y)):
            puntos.append((x, y))
    return puntos


def _construir_puntos_hogares_por_estrato() -> dict[str, np.ndarray]:
    """Lee la composición de estrato directamente de `df_modelo.csv` (año 2024) — no depende de
    construir un modelo (la composición de estrato es un dato estático real, no algo que cambie
    con la simulación), evitando así un orden de inicialización frágil dentro del módulo."""
    try:
        df_modelo = pd.read_csv(config_datos.DATA_PROCESSED / "df_modelo.csv")
        columna_anio = df_modelo.columns[1]
        df_modelo = df_modelo.rename(columns={columna_anio: "ANIO"})
        df_anio = df_modelo[df_modelo["ANIO"] == 2024]
    except Exception:
        return {"bajo": np.empty((0, 2)), "medio": np.empty((0, 2)), "alto": np.empty((0, 2))}
    gdf = _GDF_UPZ_BASE.merge(df_anio, left_on="CODIGO_UPZ", right_on="UPZ", how="inner")
    rng = np.random.default_rng(42)
    acumulado = {"bajo": [], "medio": [], "alto": []}
    for fila in gdf.itertuples():
        total = _PUNTOS_POR_UPZ_HOGARES
        for clave, pct in [
            ("bajo", fila.pct_estrato_bajo), ("medio", fila.pct_estrato_medio), ("alto", fila.pct_estrato_alto),
        ]:
            n = round((pct or 0.0) / 100.0 * total)
            acumulado[clave].extend(_puntos_aleatorios_en_poligono(fila.geometry, n, rng))
    return {k: (np.array(v) if v else np.empty((0, 2))) for k, v in acumulado.items()}


_PUNTOS_HOGARES_POR_ESTRATO = _construir_puntos_hogares_por_estrato()

# --- Pool de posiciones simbólicas por UPZ, para el scatter de "comportamiento en vivo" (ronda 6) ---
# Mismo criterio que arriba (no hay GPS real de hogares individuales): la POSICIÓN es simbólica y
# fija; lo nuevo es que el COLOR de cada punto, en `PanelComportamientoAgentes`, se recalcula en
# cada render con el estado REAL y dinámico de `prob_separa_actual` de los agentes de esa UPZ —
# no es una capa estática como la de arriba.
_PUNTOS_POR_UPZ_COMPORTAMIENTO = 12


def _construir_puntos_comportamiento_por_upz() -> dict[int, np.ndarray]:
    rng = np.random.default_rng(43)
    resultado: dict[int, np.ndarray] = {}
    for fila in _GDF_UPZ_BASE.itertuples():
        codigo = fila.CODIGO_UPZ
        if pd.isna(codigo):
            continue
        puntos = _puntos_aleatorios_en_poligono(fila.geometry, _PUNTOS_POR_UPZ_COMPORTAMIENTO, rng)
        resultado[int(codigo)] = np.array(puntos) if puntos else np.empty((0, 2))
    return resultado


_PUNTOS_COMPORTAMIENTO_POR_UPZ = _construir_puntos_comportamiento_por_upz()

# Serie real oficial (Residuos generados bogota.xlsx), reconciliada en
# Investigacion_Salto_Aprovechamiento.md — misma fuente que abm/calibracion.py.
_SERIE_REAL_APROVECHAMIENTO = {
    2018: 15.38, 2019: 15.70, 2020: 17.28, 2021: 19.18, 2022: 18.27, 2023: 18.56,
}

# Trayectoria simulada ENCADENADA 2018-2024, calibrada solo contra los 6 puntos reales de arriba
# (RMSE≈1.1961pp), a resolución completa (365 días/año, 3% de muestreo) — corrida una sola vez
# offline con `abm/calibracion.py::correr_serie_anios`, ver
# `data/processed/23_confirmacion_calibracion_2018_2024.csv` e
# `Investigacion_Salto_Aprovechamiento.md` §7. NO se recalcula en vivo.
# Recalibrado 2026-07-13 tras corregir 2 bugs reales del mecanismo de actitud (ver
# `abm/config_abm.py`) que dejaban el mecanismo de imitación/free-riding muerto desde el día 1.
# Recalibrado de nuevo 2026-07-14 (ronda 5): `prob_separa` cambió de fuente (ECA2021/localidad →
# EM2021/UPZ, ver Justificacion_Metodologica_Comite.md §5bis) — serie refrescada con los 4
# parámetros finales de esa ronda (brecha=0.63, decay=0.02, umbral=0.07, recuperación=0.02).
_SERIE_SIMULADA_2018_2024 = {
    2018: 18.08, 2019: 17.87, 2020: 17.86, 2021: 17.76, 2022: 18.26, 2023: 18.25, 2024: 18.32,
}
_CONTRAFACTUAL_ABM_2024_PCT = _SERIE_SIMULADA_2018_2024[2024]
_OFICIAL_UAESP_2024_PCT = 43.88


def _agregar_por_localidad(resumen: pd.DataFrame) -> pd.DataFrame:
    """Agrega el resumen por UPZ a nivel localidad — la resolución REAL del comportamiento de
    separación (ver `Justificacion_Metodologica_Comite.md`: `prob_separa_base` solo es un dato
    real a nivel localidad, 20 unidades; UPZ lo hereda, no lo mide). Suma toneladas (magnitud
    aditiva real) y recalcula el % como Σaprovechado/Σgenerado — no como promedio de los % por
    UPZ, que pesaría igual una UPZ grande que una diminuta."""
    agregado = resumen.groupby(["codigo_localidad", "nombre_localidad"], as_index=False).agg(
        generado_acumulado_ton=("generado_acumulado_ton", "sum"),
        aprovechado_acumulado_ton=("aprovechado_acumulado_ton", "sum"),
        rechazo_acumulado_ton=("rechazo_acumulado_ton", "sum"),
        hogares_reales=("hogares_reales", "sum"),
    )
    agregado["pct_aprovechamiento"] = np.where(
        agregado["generado_acumulado_ton"] > 0,
        agregado["aprovechado_acumulado_ton"] / agregado["generado_acumulado_ton"] * 100.0,
        0.0,
    )
    return agregado


def _resumen_con_geometria(model, vista: str = "UPZ") -> "gpd.GeoDataFrame":
    resumen = model.resumen_por_upz()
    gdf_upz = _GDF_UPZ_BASE.merge(resumen, left_on="CODIGO_UPZ", right_on="UPZ", how="left")
    if vista != "Localidad":
        return gdf_upz

    agregado = _agregar_por_localidad(resumen)
    gdf_localidad = (
        gdf_upz[["codigo_localidad", "geometry"]]
        .dropna(subset=["codigo_localidad"])
        .dissolve(by="codigo_localidad")
        .reset_index()
        .merge(agregado, on="codigo_localidad", how="left")
    )
    return gdf_localidad


# =================================================================================================
# Tarjetas KPI (stat tiles) — reemplazan la tabla markdown original
# =================================================================================================

@solara.component
def TarjetaKPI(etiqueta: str, valor: str, contexto: str = "", color_valor: str = INK_PRIMARIO, icono: str = ""):
    with solara.Card(style=f"background-color:{SURFACE}; min-width:170px; flex:1;"):
        solara.Text(
            (f"{icono} " if icono else "") + etiqueta.upper(),
            style=f"color:{INK_MUTED}; font-size:0.68rem; letter-spacing:0.04em; font-weight:600;",
        )
        solara.HTML(
            tag="div", unsafe_innerHTML=valor,
            style=f"color:{color_valor}; font-size:1.9rem; font-weight:700; line-height:1.15; margin:2px 0;",
        )
        if contexto:
            solara.Text(contexto, style=f"color:{INK_SECUNDARIO}; font-size:0.72rem;")


@solara.component
def FilaKPIs(model):
    update_counter.get()
    df = model.datacollector.get_model_vars_dataframe()
    if df.empty:
        pct_hoy = generado_hoy = aprovechado_hoy = capacidad_usada = pct_acumulado = 0.0
    else:
        ultima = df.iloc[-1]
        pct_hoy = ultima["pct_aprovechamiento_dia"]
        pct_acumulado = ultima["pct_aprovechamiento_acumulado_ciudad"]
        generado_hoy = ultima["generado_dia_ton"]
        aprovechado_hoy = ultima["aprovechado_dia_ton"]
        capacidad_usada = ultima["capacidad_formal_usada_pct"]

    brecha = _OFICIAL_UAESP_2024_PCT - _CONTRAFACTUAL_ABM_2024_PCT
    n_hogares = len(model.agents_by_type[HogarAgente])
    faltan = max(config_abm.DIAS_POR_ANIO - model.dia_actual, 0)

    solara.Text(
        f"AÑO {model.anio} — ACUMULADO A LA FECHA (día {model.dia_actual} de {config_abm.DIAS_POR_ANIO}"
        + (", año completo" if faltan == 0 else f", faltan {faltan} días") + ")",
        style=f"color:{INK_MUTED}; font-size:0.7rem; letter-spacing:0.05em; font-weight:700;",
    )
    resumen = model.resumen_por_upz()
    poblacion_total = resumen["hogares_reales"].sum() if "hogares_reales" in resumen.columns else 0.0

    with solara.Row(style="flex-wrap:wrap; gap:10px; margin-bottom:2px;"):
        TarjetaKPI(
            "Hogares reales", f"{poblacion_total:,.0f}",
            f"Año {model.anio} — DANE, proyección UPZ", INK_PRIMARIO, icono="🏠",
        )
        TarjetaKPI(
            "% aprovechamiento acumulado", f"{pct_acumulado:.1f}%",
            "Σ aprovechado / Σ generado desde el día 1", AZUL, icono="♻️",
        )
        TarjetaKPI(
            "Contrafactual ABM 2024", f"{_CONTRAFACTUAL_ABM_2024_PCT:.1f}%",
            "Corrida encadenada 2018-2023, sin reforma", AQUA, icono="📈",
        )
        TarjetaKPI(
            "Brecha vs. oficial 2024", f"+{brecha:.1f}pp",
            f"Oficial UAESP = {_OFICIAL_UAESP_2024_PCT:.1f}% (no comparable)", CRITICO, icono="⚠️",
        )
        TarjetaKPI(
            "Meta real 2023", f"{config_datos.APROVECHAMIENTO_GROUND_TRUTH_PCT:.1f}%",
            "Último año con cifra oficial consistente", INK_PRIMARIO, icono="🎯",
        )

    solara.Text(
        "FLUJO DE HOY (no acumulado)",
        style=f"color:{INK_MUTED}; font-size:0.65rem; letter-spacing:0.05em; font-weight:700; margin-top:6px;",
    )
    with solara.Row(style="flex-wrap:wrap; gap:8px;"):
        TarjetaKPI("Generado hoy", f"{generado_hoy:,.0f} ton", "Solo el día actual", INK_SECUNDARIO, icono="🗑️")
        TarjetaKPI("Aprovechado hoy", f"{aprovechado_hoy:,.0f} ton", "Solo el día actual", AQUA, icono="📦")
        TarjetaKPI("% de hoy", f"{pct_hoy:.1f}%", "Solo el día actual", INK_SECUNDARIO, icono="📊")
        TarjetaKPI("Capacidad formal usada", f"{capacidad_usada:.1f}%",
                    f"de {model.capacidad_formal_total_dia_ton:,.0f} ton/día reales (5 ASE)",
                    ADVERTENCIA if capacidad_usada > 70 else INK_SECUNDARIO, icono="🚛")
        TarjetaKPI("Hogares simulados", f"{n_hogares:,}",
                    f"Muestra real {config_abm.FRACCION_MUESTREO_HOGARES:.0%} de la población", INK_SECUNDARIO, icono="👥")


# =================================================================================================
# Mapa principal — coropletico real de aprovechamiento acumulado por UPZ
# =================================================================================================

@solara.component
def MapaPrincipal(model, mostrar_hogares=True, mostrar_criticos=True, vista="UPZ", columna="% Aprovechamiento"):
    update_counter.get()
    gdf = _resumen_con_geometria(model, vista=vista)

    fig, ax = _mapa_oscuro((9.5, 9.8))
    if columna == "Generación":
        # Leyenda DISCRETA por rangos (no continua) — más cercana al estilo de referencia, con
        # los rangos calculados de los cuantiles REALES del día (no números fijos inventados).
        valores = gdf["generado_acumulado_ton"].dropna()
        bordes = np.unique(np.quantile(valores, [0, 0.2, 0.4, 0.6, 0.8, 1.0])) if len(valores) else np.array([0.0, 1.0])
        if len(bordes) < 2:
            bordes = np.array([0.0, max(1.0, float(valores.max()) if len(valores) else 1.0)])
        cmap_discreto = mpl.colors.ListedColormap(CMAP_APROVECHAMIENTO(np.linspace(0.15, 0.95, len(bordes) - 1)))
        norma = mpl.colors.BoundaryNorm(bordes, cmap_discreto.N)
        gdf.plot(
            column="generado_acumulado_ton", cmap=cmap_discreto, norm=norma,
            edgecolor=LINEA_BASE, linewidth=0.4 if vista == "UPZ" else 0.9, legend=True, ax=ax,
            missing_kwds={"color": FONDO_SIN_DATO},
            legend_kwds={"label": f"Generación acumulada, ton ({vista})", "shrink": 0.55},
        )
        titulo_columna = "generación acumulada (ton)"
    else:
        gdf.plot(
            column="pct_aprovechamiento", cmap=CMAP_APROVECHAMIENTO, vmin=0, vmax=100,
            edgecolor=LINEA_BASE, linewidth=0.4 if vista == "UPZ" else 0.9, legend=True, ax=ax,
            missing_kwds={"color": FONDO_SIN_DATO},
            legend_kwds={"label": f"% aprovechamiento acumulado ({vista})", "shrink": 0.55},
        )
        titulo_columna = "% de aprovechamiento acumulado"
    _colorear_colorbar(fig.axes[-1])

    # --- Capa: hogares simbólicos por estrato (composición real, posiciones ilustrativas) ---
    if mostrar_hogares:
        for clave, etiqueta in [("bajo", "Estrato bajo"), ("medio", "Estrato medio"), ("alto", "Estrato alto")]:
            pts = _PUNTOS_HOGARES_POR_ESTRATO.get(clave, np.empty((0, 2)))
            if len(pts):
                ax.scatter(pts[:, 0], pts[:, 1], s=5, color=_COLOR_ESTRATO[clave], alpha=0.75,
                            linewidths=0, zorder=3, label=f"Hogares — {etiqueta} (simbólico, composición real)")

    # --- Capa: puntos críticos REALES (SIGAB dic-2024) ---
    if mostrar_criticos and len(_PUNTOS_CRITICOS_REALES):
        ax.scatter(_PUNTOS_CRITICOS_REALES[:, 0], _PUNTOS_CRITICOS_REALES[:, 1],
                    marker="x", s=22, color=CRITICO, linewidths=1.1, zorder=4,
                    label=f"Puntos críticos REALES (SIGAB dic-2024, n={len(_PUNTOS_CRITICOS_REALES)})")

    dia = model.dia_actual
    _fijar_limites_bogota(ax)
    leyenda = ax.legend(loc="lower left", fontsize=6.5, frameon=True, facecolor=SURFACE, edgecolor=LINEA_BASE, markerscale=1.6)
    for texto in leyenda.get_texts():
        texto.set_color(INK_SECUNDARIO)

    ax.set_title(f"Bogotá — {titulo_columna} por {vista} · día {dia}", fontsize=12, color=INK_PRIMARIO)
    fig.tight_layout()
    solara.FigureMatplotlib(fig, format="png")
    if vista == "UPZ" and columna != "Generación":
        solara.Text(
            "Desde 2026-07-14 (EM2021 a nivel UPZ), el comportamiento de separación es un dato "
            "real medido en 112 de 112 UPZ — ya no se hereda de la localidad. La vista por "
            "\"Localidad\" sigue disponible como nivel de agregación (útil para comparar contra "
            "participación comunitaria/vivienda/informalidad, que sí siguen siendo reales solo a "
            "localidad, ver Justificacion_Metodologica_Comite.md §5bis).",
            style=f"color:{INK_MUTED}; font-size:0.7rem; font-style:italic; margin-top:2px;",
        )


@solara.component
def PanelComportamientoAgentes(model):
    """Scatter del estado REAL de decaimiento de cada `HogarAgente` (ronda 6) — a diferencia de
    la capa de hogares por estrato de arriba (estática, solo composición), aquí el COLOR se
    recalcula en cada render con `prob_separa_actual` real de los agentes vivos de la simulación:
    verde = en su base (no ha decaído), rojo = en el piso (decayó al máximo), amarillo = entre
    medio. La POSICIÓN sigue siendo simbólica (no hay GPS real de hogares) — ver
    `_PUNTOS_COMPORTAMIENTO_POR_UPZ`."""
    update_counter.get()

    epsilon = 1e-6
    conteo_por_upz: dict[int, dict[str, int]] = {}
    for hogar in model.agents_by_type[HogarAgente]:
        if hogar.prob_separa_actual >= hogar.prob_separa_base - epsilon:
            estado = "verde"
        elif hogar.prob_separa_actual <= hogar.piso_escalado + epsilon:
            estado = "rojo"
        else:
            estado = "amarillo"
        conteos = conteo_por_upz.setdefault(hogar.codigo_upz, {"verde": 0, "amarillo": 0, "rojo": 0})
        conteos[estado] += 1

    color_de = {"verde": BUENO, "amarillo": ADVERTENCIA, "rojo": CRITICO}
    etiqueta_de = {
        "verde": "En su base (no ha decaído)", "amarillo": "Decayendo",
        "rojo": "En el piso (decayó al máximo)",
    }
    puntos_por_color: dict[str, list[np.ndarray]] = {"verde": [], "amarillo": [], "rojo": []}
    totales = {"verde": 0, "amarillo": 0, "rojo": 0}

    for codigo_upz, conteos in conteo_por_upz.items():
        posiciones = _PUNTOS_COMPORTAMIENTO_POR_UPZ.get(codigo_upz)
        if posiciones is None or len(posiciones) == 0:
            continue
        total_agentes_upz = sum(conteos.values())
        n_slots = len(posiciones)
        rng_local = np.random.default_rng(codigo_upz)
        orden = rng_local.permutation(n_slots)

        asignados = 0
        idx = 0
        for i, estado in enumerate(("verde", "amarillo", "rojo")):
            if i < 2:
                n = round(conteos[estado] / total_agentes_upz * n_slots) if total_agentes_upz else 0
                n = min(n, n_slots - asignados)
            else:
                n = n_slots - asignados  # el último estado se queda con lo que sobre (suma exacta)
            seleccion = posiciones[orden[idx: idx + n]]
            if len(seleccion):
                puntos_por_color[estado].append(seleccion)
            idx += n
            asignados += n
        for estado, conteo in conteos.items():
            totales[estado] += conteo

    fig, ax = _mapa_oscuro((9, 9.2))
    for estado in ("rojo", "amarillo", "verde"):
        partes = puntos_por_color[estado]
        if partes:
            pts = np.concatenate(partes, axis=0)
            ax.scatter(
                pts[:, 0], pts[:, 1], s=9, color=color_de[estado], alpha=0.8, linewidths=0,
                zorder=3, label=f"{etiqueta_de[estado]} — {totales[estado]:,} hogares reales",
            )

    _fijar_limites_bogota(ax)
    leyenda = ax.legend(loc="lower left", fontsize=7, frameon=True, facecolor=SURFACE, edgecolor=LINEA_BASE, markerscale=1.8)
    for t in leyenda.get_texts():
        t.set_color(INK_SECUNDARIO)
    ax.set_title(f"Comportamiento real de los agentes · día {model.dia_actual}", fontsize=12, color=INK_PRIMARIO)
    fig.tight_layout()
    solara.FigureMatplotlib(fig, format="png")
    solara.Text(
        "La POSICIÓN de cada punto es simbólica (no hay GPS real de hogares) — el COLOR es el "
        "estado real y dinámico de `prob_separa_actual` de los agentes reales de esa UPZ, "
        "recalculado cada vez que avanza la simulación (mecanismo de imitación/free-riding, "
        "actualizado cada 7 días).",
        style=f"color:{INK_MUTED}; font-size:0.7rem; font-style:italic; margin-top:2px;",
    )


@solara.component
def _NodoFlujo(titulo: str, valor_ton: float, color: str, ancho: str = "230px"):
    with solara.Card(style=f"background-color:{SURFACE}; border-left:3px solid {color}; min-width:{ancho};"):
        solara.Text(titulo, style=f"color:{INK_MUTED}; font-size:0.7rem; letter-spacing:0.02em;")
        solara.Text(f"{valor_ton:,.0f} ton", style=f"color:{color}; font-size:1.25rem; font-weight:700;")


@solara.component
def PanelFlujoAgentes(model):
    """Diagrama del flujo REAL de material (ronda 6): Generación → Separación en la fuente →
    reparto entre recicladores informales y sistema formal (mecanismo #2: compiten sin
    coordinación) → Aprovechado/Rechazo. El reparto informal-vs-formal es un dato real que ya se
    acumula en cada agente (`PoblacionRecicladoresUPZ.material_recolectado_acumulado`,
    `OperadorUAESP.material_recolectado_acumulado`) pero nunca se había mostrado en ningún panel.

    También expone, por primera vez, la diferencia entre lo que los hogares SEPARAN
    (`HogarAgente.material_separado_acumulado`) y lo que efectivamente se RECLAMA el mismo día
    (recicladores + sistema formal) — el pool de un día no reservado se pierde al día siguiente
    (`EntornoUPZ.reiniciar_paso_diario`), así que esta diferencia es fuga real de material
    separado que la competencia sin coordinación no alcanzó a recoger a tiempo.
    """
    update_counter.get()
    resumen = model.resumen_por_upz()
    generado = resumen["generado_acumulado_ton"].sum()
    aprovechado = resumen["aprovechado_acumulado_ton"].sum()
    rechazo = resumen["rechazo_acumulado_ton"].sum()

    separado_en_fuente = sum(h.material_separado_acumulado for h in model.agents_by_type[HogarAgente])
    recolectado_informal = sum(a.material_recolectado_acumulado for a in model.agents_by_type[PoblacionRecicladoresUPZ])
    recolectado_formal = sum(op.material_recolectado_acumulado for op in model.operadores_ase)
    sin_reclamar = max(separado_en_fuente - (recolectado_informal + recolectado_formal), 0.0)

    with solara.Column(style="gap:6px; align-items:center;"):
        _NodoFlujo("Generación acumulada", generado, INK_SECUNDARIO, "280px")
        solara.Text("↓", style=f"color:{INK_MUTED}; font-size:1.3rem;")
        _NodoFlujo("Separado en la fuente por los hogares", separado_en_fuente, VIOLETA, "280px")
        solara.Text(
            "↓  compiten sin coordinación por el pool — mecanismo #2",
            style=f"color:{INK_MUTED}; font-size:0.7rem;",
        )
        with solara.Row(style="gap:14px; justify-content:center; flex-wrap:wrap;"):
            _NodoFlujo("♻️ Recicladores informales", recolectado_informal, AQUA)
            _NodoFlujo("🏛️ Sistema formal (5 ASE)", recolectado_formal, AMARILLO)
        solara.Text("↓", style=f"color:{INK_MUTED}; font-size:1.3rem;")
        with solara.Row(style="gap:14px; justify-content:center; flex-wrap:wrap;"):
            _NodoFlujo("✅ Aprovechado", aprovechado, BUENO)
            _NodoFlujo("🚮 Rechazo → Doña Juana", rechazo, CRITICO)
        solara.Text(
            f"De lo separado por los hogares, {sin_reclamar:,.0f} ton no se reclamaron el mismo "
            "día (ni por recicladores ni por el sistema formal) — el pool no reclamado se pierde "
            "al cerrar el día y termina contado como rechazo. Es fuga real de la competencia sin "
            "coordinación, no un error de conteo.",
            style=f"color:{INK_MUTED}; font-size:0.72rem; font-style:italic; max-width:640px; text-align:center; margin-top:4px;",
        )


# =================================================================================================
# Mini-gráficos de tendencia (sparklines) — sin ejes pesados, un tono, foco en la forma
# =================================================================================================

@solara.component
def MiniGrafico(df: pd.DataFrame, columna: str, titulo: str, color: str, unidad: str = ""):
    fig, ax = _figura_oscura((3.6, 2.0))
    if not df.empty:
        ax.plot(df.index, df[columna], color=color, linewidth=1.6)
        ax.fill_between(df.index, df[columna], color=color, alpha=0.12)
        ultimo = df[columna].iloc[-1]
        ax.set_title(f"{titulo} · {ultimo:,.1f}{unidad}", fontsize=9, color=INK_PRIMARIO, loc="left")
    else:
        ax.set_title(titulo, fontsize=9, color=INK_PRIMARIO, loc="left")
    ax.set_xlabel("día", fontsize=7, color=INK_MUTED)
    ax.tick_params(labelsize=6)
    fig.tight_layout()
    solara.FigureMatplotlib(fig, format="png")


@solara.component
def FilaMiniGraficos(model):
    update_counter.get()
    df = model.datacollector.get_model_vars_dataframe()
    with solara.Row(style="flex-wrap:wrap; gap:8px;"):
        MiniGrafico(df, "generado_dia_ton", "Generado", INK_SECUNDARIO, " ton")
        MiniGrafico(df, "aprovechado_dia_ton", "Aprovechado", AQUA, " ton")
        MiniGrafico(df, "rechazo_dia_ton", "Rechazo → Doña Juana", ROJO, " ton")
        MiniGrafico(df, "capacidad_formal_usada_pct", "Capacidad formal usada", AMARILLO, "%")


# =================================================================================================
# Balance de masa y % acumulado — versión oscura de los gráficos originales
# =================================================================================================

@solara.component
def SeriesTemporalesBalance(model):
    update_counter.get()
    df = model.datacollector.get_model_vars_dataframe()

    fig, ax = _figura_oscura((9, 3.6))
    if not df.empty:
        ax.plot(df.index, df["generado_dia_ton"], label="Generado", color=INK_SECUNDARIO, linewidth=1.5)
        ax.plot(df.index, df["aprovechado_dia_ton"], label="Aprovechado", color=AQUA, linewidth=1.5)
        ax.plot(df.index, df["rechazo_dia_ton"], label="Rechazo (a Doña Juana)", color=ROJO, linewidth=1.5)
        leyenda = ax.legend(loc="upper left", fontsize=8, frameon=False)
        for t in leyenda.get_texts():
            t.set_color(INK_SECUNDARIO)
    ax.set_xlabel("Día de simulación")
    ax.set_ylabel("Toneladas")
    ax.set_title("Balance de masa diario: generado = aprovechado + rechazo", color=INK_PRIMARIO)
    fig.tight_layout()
    solara.FigureMatplotlib(fig, format="png")


@solara.component
def SerieAprovechamientoPct(model):
    update_counter.get()
    df = model.datacollector.get_model_vars_dataframe()

    fig, ax = _figura_oscura((9, 3.2))
    if not df.empty:
        ax.plot(df.index, df["pct_aprovechamiento_dia"], color=AZUL, linewidth=1.8, label="Simulado (día actual)")
        ax.axhline(
            config_datos.APROVECHAMIENTO_GROUND_TRUTH_PCT, color=ROJO, linestyle="--", linewidth=1,
            label=f"Meta real 2023 = {config_datos.APROVECHAMIENTO_GROUND_TRUTH_PCT}%",
        )
        real_del_anio = _SERIE_REAL_APROVECHAMIENTO.get(model.anio)
        if real_del_anio is not None:
            ax.axhline(
                real_del_anio, color=AQUA, linestyle=":", linewidth=1.3,
                label=f"Cifra real de {model.anio} = {real_del_anio}%",
            )
        leyenda = ax.legend(loc="upper left", fontsize=7, frameon=False)
        for t in leyenda.get_texts():
            t.set_color(INK_SECUNDARIO)
    ax.set_xlabel("Día de simulación")
    ax.set_ylabel("% aprovechamiento")
    ax.set_title("% de aprovechamiento acumulado — ciudad completa", color=INK_PRIMARIO)
    fig.tight_layout()
    solara.FigureMatplotlib(fig, format="png")


# =================================================================================================
# Contrafactual histórico — versión decluttered (menos tipos de marcador, misma información)
# =================================================================================================

@solara.component
def GraficoContrafactual(model):
    update_counter.get()
    df = model.datacollector.get_model_vars_dataframe()

    fig, ax = _figura_oscura((9, 4))

    anios_reales = sorted(_SERIE_REAL_APROVECHAMIENTO.keys())
    valores_reales = [_SERIE_REAL_APROVECHAMIENTO[a] for a in anios_reales]
    ax.plot(anios_reales, valores_reales, "o-", color=AQUA, linewidth=2, markersize=5, label="Real oficial (2018-2023)")

    anios_sim = sorted(_SERIE_SIMULADA_2018_2024.keys())
    valores_sim = [_SERIE_SIMULADA_2018_2024[a] for a in anios_sim]
    ax.plot(anios_sim, valores_sim, "--", color=AZUL, linewidth=1.8, label="ABM encadenado (sin mecanismo de reforma)")

    ax.plot([2024], [_OFICIAL_UAESP_2024_PCT], marker="X", color=CRITICO, markersize=12, linestyle="none",
             label=f"Oficial UAESP 2024 (post-reforma) = {_OFICIAL_UAESP_2024_PCT}% — no comparable")

    if not df.empty and model.anio == 2024:
        ax.plot([model.anio], [df["pct_aprovechamiento_acumulado_ciudad"].iloc[-1]], marker="D", color=VIOLETA, markersize=8,
                 linestyle="none", label=f"Dashboard en vivo, acumulado (día {model.dia_actual}, sin memoria histórica)")

    ax.annotate(
        f"brecha ≈ {_OFICIAL_UAESP_2024_PCT - _CONTRAFACTUAL_ABM_2024_PCT:.1f}pp",
        xy=(2024, (_CONTRAFACTUAL_ABM_2024_PCT + _OFICIAL_UAESP_2024_PCT) / 2),
        xytext=(2022.3, 33), color=CRITICO, fontsize=9,
        arrowprops=dict(arrowstyle="->", color=CRITICO, lw=1),
    )

    ax.set_xlabel("Año")
    ax.set_ylabel("% aprovechamiento")
    ax.set_title("Contrafactual: ¿qué habría dado 2024 sin el quiebre de metodología?", color=INK_PRIMARIO)
    leyenda = ax.legend(loc="upper left", fontsize=8, frameon=False)
    for t in leyenda.get_texts():
        t.set_color(INK_SECUNDARIO)
    fig.tight_layout()
    solara.FigureMatplotlib(fig, format="png")


# =================================================================================================
# Mapas de mecanismos reales (infraestructura, incentivo) + ranking
# =================================================================================================

@solara.component
def MapaInfraestructuraReal(model):
    update_counter.get()
    gdf = _resumen_con_geometria(model)

    fig, ax = _mapa_oscuro((7, 8))
    gdf.plot(
        column="infraestructura_index", cmap=CMAP_INFRAESTRUCTURA, vmin=0, vmax=1,
        edgecolor=LINEA_BASE, linewidth=0.4, legend=True, ax=ax,
        missing_kwds={"color": FONDO_SIN_DATO},
        legend_kwds={"label": "Índice de infraestructura (real)", "shrink": 0.55},
    )
    _colorear_colorbar(fig.axes[-1])
    _fijar_limites_bogota(ax)
    ax.set_title("Infraestructura REAL por UPZ\n(puntos críticos SIGAB, 4 cortes 2020-2026)", fontsize=11, color=INK_PRIMARIO)
    fig.tight_layout()
    solara.FigureMatplotlib(fig, format="png")


@solara.component
def MapaIncentivoEconomico(model):
    update_counter.get()
    gdf = _resumen_con_geometria(model)

    fig, ax = _mapa_oscuro((7, 8))
    norma = TwoSlopeNorm(vmin=-0.7, vcenter=0.0, vmax=0.6)
    gdf.plot(
        column="factor_incentivo", cmap=CMAP_INCENTIVO, norm=norma,
        edgecolor=LINEA_BASE, linewidth=0.4, legend=True, ax=ax,
        missing_kwds={"color": FONDO_SIN_DATO},
        legend_kwds={"label": "Factor subsidio(-)/contribución(+)", "shrink": 0.55},
    )
    _colorear_colorbar(fig.axes[-1])
    _fijar_limites_bogota(ax)
    ax.set_title("Incentivo económico REAL por UPZ\n(tarifa CRA + composición de estrato, dic-2025)", fontsize=11, color=INK_PRIMARIO)
    fig.tight_layout()
    solara.FigureMatplotlib(fig, format="png")


@solara.component
def RankingUPZ(model, vista="UPZ"):
    """Ranking de las 5 mejores y 5 peores (UPZ o localidad) en % de aprovechamiento acumulado —
    barras horizontales (ronda 6, reemplaza la lista de texto monoespaciado anterior, mismo dato)."""
    update_counter.get()
    resumen_upz = model.resumen_por_upz()

    if vista == "Localidad":
        resumen = _agregar_por_localidad(resumen_upz).sort_values("pct_aprovechamiento", ascending=False)
        etiqueta_de = lambda r: r.nombre_localidad  # noqa: E731
        titulo = "Aprovechamiento por localidad (%) — mejores y peores 5"
    else:
        resumen = resumen_upz.sort_values("pct_aprovechamiento", ascending=False)
        etiqueta_de = lambda r: f"UPZ {int(r.UPZ)} · {r.nombre_localidad}"  # noqa: E731
        titulo = "Aprovechamiento por UPZ (%) — mejores y peores 5"

    mejores, peores = resumen.head(5), resumen.tail(5)
    combinado = pd.concat([mejores, peores])
    etiquetas = [etiqueta_de(r) for r in combinado.itertuples()]
    colores = [BUENO] * len(mejores) + [CRITICO] * len(peores)

    fig, ax = _figura_oscura((7.6, 4.6))
    y_pos = np.arange(len(combinado))[::-1]
    ax.barh(y_pos, combinado["pct_aprovechamiento"], color=colores, height=0.6)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(etiquetas, fontsize=8)
    ax.set_xlabel("% aprovechamiento acumulado")
    ax.set_title(titulo, fontsize=10, color=INK_PRIMARIO)
    ax.axhline(len(peores) - 0.5, color=LINEA_BASE, linewidth=1, linestyle="--")
    fig.tight_layout()
    solara.FigureMatplotlib(fig, format="png")

    if vista == "UPZ":
        solara.Text(
            "Desde 2026-07-14 (EM2021 a nivel UPZ), el comportamiento de separación es un dato "
            "real medido en 112 de 112 UPZ — ya no se hereda de la localidad (ver "
            "Justificacion_Metodologica_Comite.md §5bis).",
            style=f"color:{INK_MUTED}; font-size:0.7rem; font-style:italic;",
        )


_COLORES_MATERIAL = [AZUL, AQUA, AMARILLO, VIOLETA, ROJO, MAGENTA, NARANJA]


@solara.component
def PanelComposicionReal():
    """Composición real de referencia (`04_composicion_residuos.csv`, promedio de Bogotá) — el
    ABM NO simula composición por tipo de material día a día (no es una variable del modelo);
    esto es dato real ESTÁTICO, mostrado como contexto, no como salida de la simulación.
    Donut chart (ronda 6): variable categórica/nominal (tipo de material) → un color por
    categoría, no un degradado de un solo tono (ver skill `dataviz`, anti-patrón de "value-ramp
    en categóricas")."""
    try:
        df = pd.read_csv(config_datos.DATA_PROCESSED / "04_composicion_residuos.csv", encoding="utf-8-sig")
    except Exception:
        solara.Text("No se pudo cargar la composición real de referencia.", style=f"color:{INK_MUTED};")
        return

    columna_anio = df.columns[0]
    ultimo_anio = df[columna_anio].max()
    fila = df[df[columna_anio] == ultimo_anio].iloc[0]
    columnas_material = [c for c in df.columns if c not in (columna_anio, "Total", "Error_Total")]
    serie_completa = fila[columnas_material].astype(float).sort_values(ascending=False)

    top = serie_completa.head(len(_COLORES_MATERIAL))
    resto = serie_completa.iloc[len(_COLORES_MATERIAL):].sum()
    colores = list(_COLORES_MATERIAL[: len(top)])
    if resto > 1e-9:
        top = pd.concat([top, pd.Series({"Otros": resto})])
        colores.append(INK_MUTED)

    fig = Figure(figsize=(7.2, 4.2), facecolor=SURFACE)
    ax = fig.add_subplot()
    ax.set_facecolor(SURFACE)
    wedges, _, autotextos = ax.pie(
        top.values * 100, colors=colores, startangle=90,
        wedgeprops=dict(width=0.42, edgecolor=SURFACE, linewidth=2),
        autopct=lambda p: f"{p:.1f}%" if p >= 3 else "", pctdistance=0.80,
        textprops={"color": INK_PRIMARIO, "fontsize": 8, "fontweight": "bold"},
    )
    ax.set_title(
        f"Composición real de referencia — {int(ultimo_anio)} (no simulada día a día)",
        fontsize=10, color=INK_PRIMARIO,
    )
    leyenda = ax.legend(
        wedges, [f"{nombre} — {valor * 100:.1f}%" for nombre, valor in top.items()],
        loc="center left", bbox_to_anchor=(1.0, 0.5), fontsize=8.5, frameon=False,
    )
    for t in leyenda.get_texts():
        t.set_color(INK_SECUNDARIO)
    fig.tight_layout()
    solara.FigureMatplotlib(fig, format="png")


@solara.component
def GraficoGeneracionPorEstrato(model):
    """Generación acumulada de residuos por categoría de estrato, en vivo (ronda 6) — NUEVO.
    Se calcula desde `resumen_por_upz()`, que ya trae `pct_estrato_bajo/medio/alto` (real,
    manzana→UPZ, ver Justificacion_Metodologica_Comite.md §1) y `generado_acumulado_ton` (real,
    salida de la simulación): `generado_estrato = Σ_UPZ generado_UPZ × pct_estrato_UPZ / 100`."""
    update_counter.get()
    resumen = model.resumen_por_upz()
    generado = resumen["generado_acumulado_ton"]
    pct_bajo = resumen["pct_estrato_bajo"].fillna(0)
    pct_medio = resumen["pct_estrato_medio"].fillna(0)
    pct_alto = resumen["pct_estrato_alto"].fillna(0)
    # Verificado (2026-07-14): pct_estrato_bajo/medio/alto NO suman 100% en ninguna UPZ (dato real
    # de manzana→UPZ, promedio ~83%, min 25.6%) — hay manzanas sin estrato asignado en la fuente.
    # En vez de esconder ese hueco (lo que subcontaría ~11% de lo generado si solo se sumaran las
    # 3 categorías), se muestra explícitamente como "Sin estrato asignado", igual que el "Otros"
    # del donut de composición — no se inventa a qué estrato pertenece ese residuo.
    pct_sin_estrato = (100.0 - (pct_bajo + pct_medio + pct_alto)).clip(lower=0)
    por_estrato = {
        "Baja": (generado * pct_bajo / 100.0).sum(),
        "Media": (generado * pct_medio / 100.0).sum(),
        "Alta": (generado * pct_alto / 100.0).sum(),
        "Sin estrato\nasignado": (generado * pct_sin_estrato / 100.0).sum(),
    }
    colores = [AZUL, AZUL, AZUL, INK_MUTED]

    fig, ax = _figura_oscura((6.6, 3.6))
    ax.bar(list(por_estrato.keys()), list(por_estrato.values()), color=colores, width=0.55)
    ax.set_ylabel("Toneladas acumuladas")
    ax.set_title("Generación acumulada por categoría de estrato", fontsize=10, color=INK_PRIMARIO)
    ax.tick_params(labelsize=8)
    fig.tight_layout()
    solara.FigureMatplotlib(fig, format="png")
    solara.Text(
        "\"Sin estrato asignado\" son manzanas reales sin estrato en la fuente DANE (~11-17% del "
        "total, según el año) — se muestra explícito en vez de omitirlo, para no subcontar la "
        "generación real.",
        style=f"color:{INK_MUTED}; font-size:0.68rem; font-style:italic; margin-top:2px;",
    )


# =================================================================================================
# Escenarios y política (audiencia: gobierno / tomadores de decisión)
# =================================================================================================

@solara.component
def PanelEscenarioComparacion(model):
    """Compara la línea base real (multiplicadores=1.0, cacheada offline) contra el resultado
    ACUMULADO del escenario que esté corriendo ahora mismo en el dashboard — así el usuario ve el
    efecto de mover los sliders "🏛️ Escenario: ..." sin tener que correr dos simulaciones a la
    vez. Solo tiene sentido leerlo después de correr un año completo con el escenario deseado
    (con menos de un año corrido, el acumulado del escenario está a mitad de camino, no es
    comparable 1:1 contra la línea base de 365 días)."""
    update_counter.get()
    resumen = model.resumen_por_upz()
    generado = resumen["generado_acumulado_ton"].sum()
    aprovechado = resumen["aprovechado_acumulado_ton"].sum()
    pct_escenario = (aprovechado / generado * 100.0) if generado > 0 else 0.0
    costo_fiscal_escenario = aprovechado * config_abm.VIAT_PESOS_POR_TONELADA

    delta_pct = pct_escenario - _LINEA_BASE_REAL["pct_aprovechamiento"]
    delta_costo = costo_fiscal_escenario - _LINEA_BASE_REAL["costo_fiscal_viat_cop"]
    color_delta = BUENO if delta_pct > 0.05 else (CRITICO if delta_pct < -0.05 else INK_SECUNDARIO)

    escenario_es_base = (
        abs(getattr(model, "multiplicador_infraestructura", 1.0) - 1.0) < 1e-9
        and abs(getattr(model, "multiplicador_capacidad_formal", 1.0) - 1.0) < 1e-9
    )

    with solara.Row(style="flex-wrap:wrap; gap:10px;"):
        TarjetaKPI(
            "Línea base real (hoy, sin intervención)", f"{_LINEA_BASE_REAL['pct_aprovechamiento']:.1f}%",
            "Multiplicadores = 1.0× — dato real de 2024", INK_PRIMARIO,
        )
        TarjetaKPI(
            "Escenario actual (día " + str(model.dia_actual) + ")", f"{pct_escenario:.1f}%",
            "Sliders 🏛️ del sidebar, acumulado a la fecha" if not escenario_es_base else "Sin cambios en los sliders — igual a la línea base",
            AZUL,
        )
        TarjetaKPI(
            "Δ vs. línea base", f"{delta_pct:+.2f}pp",
            "Corre el año completo para una comparación 1:1" if model.dia_actual < config_abm.DIAS_POR_ANIO else "Comparación año completo vs. año completo",
            color_delta,
        )
        TarjetaKPI(
            "Costo fiscal del incentivo (VIAT)", f"${costo_fiscal_escenario:,.0f}",
            f"Δ ${delta_costo:+,.0f} vs. línea base — {config_abm.VIAT_PESOS_POR_TONELADA:,.0f} $/ton × toneladas aprovechadas",
            INK_PRIMARIO,
        )
    solara.Text(
        "El costo fiscal SÍ es dinámico (cambia con cuánto se recupera en la simulación) — a "
        "diferencia del mapa de \"incentivo económico\" de la pestaña de público general, que es "
        "una tarifa real pero ESTÁTICA (no responde a los escenarios). VIAT = Valor del Incentivo "
        "al Aprovechamiento y Tratamiento, tarifa oficial CRA/Ciudad Limpia.",
        style=f"color:{INK_MUTED}; font-size:0.72rem; margin-top:6px;",
    )


@solara.component
def GraficoBalanceEscenario(model):
    """Barras generado/aprovechado/rechazo acumulado: línea base vs. escenario actual."""
    update_counter.get()
    resumen = model.resumen_por_upz()
    generado = resumen["generado_acumulado_ton"].sum()
    aprovechado = resumen["aprovechado_acumulado_ton"].sum()
    rechazo = resumen["rechazo_acumulado_ton"].sum()

    categorias = ["Generado", "Aprovechado", "Rechazo"]
    base = [_LINEA_BASE_REAL["generado_total_ton"], _LINEA_BASE_REAL["aprovechado_total_ton"], _LINEA_BASE_REAL["rechazo_total_ton"]]
    escenario = [generado, aprovechado, rechazo]

    fig, ax = _figura_oscura((7, 4))
    x = np.arange(len(categorias))
    ancho = 0.32
    ax.bar(x - ancho / 2, base, ancho, label="Línea base (hoy)", color=INK_SECUNDARIO)
    ax.bar(x + ancho / 2, escenario, ancho, label="Escenario actual", color=AZUL)
    ax.set_xticks(x)
    ax.set_xticklabels(categorias)
    ax.set_ylabel("Toneladas acumuladas")
    ax.set_title("Balance de masa: línea base vs. escenario", fontsize=10, color=INK_PRIMARIO)
    leyenda = ax.legend(loc="upper right", fontsize=8, frameon=False)
    for t in leyenda.get_texts():
        t.set_color(INK_SECUNDARIO)
    fig.tight_layout()
    solara.FigureMatplotlib(fig, format="png")


# =================================================================================================
# Rigor y validación (audiencia: comité de tesis)
# =================================================================================================

@solara.component
def PanelSensibilidadParametros():
    """Sensibilidad de los 4 parámetros libres del comportamiento de hogares — construida
    directamente de los resultados YA CALCULADOS en la recalibración de 2 etapas (80
    combinaciones, 2026-07-13), no se vuelve a simular nada. Ver
    `data/processed/24_sensibilidad_parametros.csv` y `Investigacion_Salto_Aprovechamiento.md` §8."""
    try:
        df = pd.read_csv(config_datos.DATA_PROCESSED / "24_sensibilidad_parametros.csv")
    except Exception:
        solara.Text("No se pudo cargar el análisis de sensibilidad.", style=f"color:{INK_MUTED};")
        return

    etiquetas = {
        "factor_brecha_intencion_accion": "Brecha intención-acción",
        "beta_decaimiento": "Tasa de decaimiento",
        "beta_recuperacion": "Tasa de recuperación",
        "umbral_percepcion_impacto": "Umbral de percepción",
    }
    rango_por_parametro = df.groupby("parametro")["rmse_pp"].agg(lambda s: s.max() - s.min()).sort_values()

    fig, ax = _figura_oscura((7, 3.6))
    nombres = [etiquetas.get(p, p) for p in rango_por_parametro.index]
    ax.barh(nombres, rango_por_parametro.values, color=AZUL, height=0.55)
    ax.set_xlabel("Rango de RMSE al variar el parámetro (pp) — más alto = más influyente")
    ax.set_title("Sensibilidad de parámetros libres (80 combinaciones probadas)", fontsize=10, color=INK_PRIMARIO)
    ax.tick_params(labelsize=8)
    fig.tight_layout()
    solara.FigureMatplotlib(fig, format="png")

    solara.Text(
        "La brecha intención-acción domina el ajuste; la tasa de recuperación no mueve el RMSE en "
        "ninguna combinación probada (no es un error — con datos anuales agregados de ciudad, ese "
        "parámetro solo importaría si hubiera cohortes que decayeron y luego ven mejorar a sus "
        "vecinos, algo raro en 6 años dominados por erosión). Documentado en "
        "Investigacion_Salto_Aprovechamiento.md §8.",
        style=f"color:{INK_MUTED}; font-size:0.72rem; margin-top:4px;",
    )


@solara.component
def PanelLimitacionesHonestas():
    limitaciones = [
        "El % de aprovechamiento oficial de Bogotá es la salida de un modelo econométrico "
        "(UAESP), no una medición directa — dos fuentes oficiales distintas difieren ~2× para el "
        "mismo año. Por eso este ABM se calibra contra la serie 2018-2023 (la última internamente "
        "consistente), no contra el 43.88%/48.50% de 2024-2025.",
        "Solo 1 de los 4 parámetros de comportamiento del hogar (brecha intención-acción) es "
        "identificable con los datos disponibles — los otros 3 no tienen dato longitudinal real "
        "que fije su velocidad exacta (ver panel de sensibilidad arriba).",
        "La resolución espacial real es la UPZ (112 zonas) — no hay dato de calles, rutas de "
        "camión individuales, ni GPS de flota real en ninguna fuente pública disponible.",
        "Los hogares que se ven en los mapas son posiciones simbólicas (proporcionales a la "
        "composición real de estrato, o al estado real de comportamiento en el panel de "
        "\"Comportamiento de agentes\") — no son coordenadas GPS reales de viviendas.",
        "El costo fiscal del incentivo (VIAT) asume que toda tonelada aprovechada recibe el pago "
        "completo — no descuenta fricciones administrativas reales del proceso de pago.",
        "Se evaluó agregar emisiones de CO2 evitadas, árboles equivalentes y empleos verdes "
        "generados (como en dashboards similares de gestión de residuos) — se excluyen por no "
        "existir, en las fuentes disponibles para este proyecto, un factor de conversión oficial "
        "citable (ton CO2/ton reciclada, empleos/ton, etc.). Agregarlos sin esa fuente sería "
        "inventar precisión donde no la hay — se documenta como trabajo futuro, no como omisión "
        "accidental.",
    ]
    with solara.Card("Limitaciones honestas (declaradas, no escondidas)", style=f"background-color:{SURFACE};"):
        for item in limitaciones:
            with solara.Row(style="gap:8px; align-items:flex-start; margin-bottom:4px;"):
                solara.Text("•", style=f"color:{INK_MUTED};")
                solara.Text(item, style=f"color:{INK_SECUNDARIO}; font-size:0.78rem;")


# =================================================================================================
# Cómo funciona el sistema (audiencia: público general)
# =================================================================================================

@solara.component
def IntroPublicoGeneral():
    with solara.Card(style=f"background-color:{SURFACE};"):
        solara.Markdown(f"""
### ¿Qué estás viendo?

Este es un **modelo basado en agentes (ABM)**: en vez de asumir un número fijo de "% de
reciclaje", se simulan miles de hogares individuales de Bogotá (con el estrato, la ubicación y el
comportamiento real medido en encuestas oficiales) tomando la decisión de separar basura o no,
día a día, durante un año — y se suma el resultado.

Los mapas de abajo muestran los **mecanismos reales** detrás de esa decisión: dónde hay más
puntos de acumulación de basura (infraestructura), y cómo varía la tarifa de aseo según el
estrato (incentivo económico) — ambos con datos oficiales reales de la ciudad, no supuestos.
""")


# =================================================================================================
# Panel de agentes + log de simulación ("centro de mando")
# =================================================================================================

@solara.component
def PanelAgentesYLog(model):
    update_counter.get()
    n_hogares = len(model.agents_by_type[HogarAgente])
    n_recicladores = len(model.agents_by_type[PoblacionRecicladoresUPZ])
    n_operadores = len(model.operadores_ase)

    df = model.datacollector.get_model_vars_dataframe()
    ultimos = df.tail(12).iloc[::-1] if not df.empty else df

    with solara.Row(style="gap:10px; align-items:flex-start; flex-wrap:wrap;"):
        with solara.Card("Agentes activos", style=f"background-color:{SURFACE}; min-width:220px;"):
            for etiqueta, valor, color in [
                ("Hogares (muestra real)", f"{n_hogares:,}", AZUL),
                ("Poblaciones de recicladores", f"{n_recicladores}", AQUA),
                ("Operadores ASE", f"{n_operadores}", AMARILLO),
            ]:
                with solara.Row(style="justify-content:space-between; min-width:200px;"):
                    solara.Text(etiqueta, style=f"color:{INK_SECUNDARIO}; font-size:0.82rem;")
                    solara.Text(valor, style=f"color:{color}; font-weight:700; font-size:0.82rem;")

        with solara.Card("Registro de simulación (últimos días)", style=f"background-color:{SURFACE}; flex:1; min-width:340px;"):
            with solara.Column(style=f"font-family:monospace; font-size:0.74rem; color:{INK_SECUNDARIO}; max-height:220px; overflow-y:auto;"):
                if ultimos is None or ultimos.empty:
                    solara.Text("(sin días simulados todavía — presiona ▶ o Step)")
                else:
                    for dia, fila in ultimos.iterrows():
                        color_pct = BUENO if fila["pct_aprovechamiento_dia"] >= config_datos.APROVECHAMIENTO_GROUND_TRUTH_PCT else INK_SECUNDARIO
                        solara.HTML(
                            tag="div",
                            unsafe_innerHTML=(
                                f"día {int(dia):>3}  gen={fila['generado_dia_ton']:,.0f}t  "
                                f"aprov={fila['aprovechado_dia_ton']:,.0f}t  "
                                f"<span style='color:{color_pct}'>({fila['pct_aprovechamiento_dia']:.1f}%)</span>  "
                                f"cap.usada={fila['capacidad_formal_usada_pct']:.0f}%"
                            ),
                        )


# =================================================================================================
# Ensamblaje del dashboard — layout propio (reemplaza SolaraViz/ComponentsView, ver docstring)
# =================================================================================================

_MODELO_INICIAL = ModeloResiduosBogota(anio=2024, rng=config_abm.SEMILLA_ALEATORIA)

_PARAMETROS_MODELO = {
    # Año real simulado (2018-2024, único rango con datos reales — ver df_modelo.csv). No es una
    # proyección: cada año usa sus propios insumos reales (población, infraestructura SIGAB más
    # cercana, capacidad formal RBL) — ver `ModeloResiduosBogota.__init__`. Reemplaza la idea de
    # un "horizonte 2025-2035" (ronda 6): ese horizonte no tiene ningún dato real que lo sostenga.
    "anio": {
        "type": "SliderInt", "label": "📅 Año simulado (dato real, no proyección)",
        "value": 2024, "min": 2018, "max": 2024, "step": 1,
    },
    "rng": config_abm.SEMILLA_ALEATORIA,
    # --- 🏛️ Escenario de política: los ÚNICOS 2 parámetros con mecanismo causal verificado
    # (multiplican `infraestructura_index`/`capacidad_dia_ton` reales — ver modelo.py). Van
    # primero en el formulario a propósito, separados visualmente de los de calibración abajo
    # (ver caption en Page()) — no se agregan más sliders de "escenario" (educación ambiental,
    # incentivos, frecuencia de recolección) porque ninguno tiene mecanismo causal en el modelo.
    "multiplicador_infraestructura": {
        "type": "SliderFloat", "label": "🏛️ Escenario: inversión en infraestructura real (× hoy)",
        "value": 1.0, "min": 0.5, "max": 2.0, "step": 0.1,
    },
    "multiplicador_capacidad_formal": {
        "type": "SliderFloat", "label": "🏛️ Escenario: capacidad formal de recolección (× hoy)",
        "value": 1.0, "min": 0.5, "max": 2.0, "step": 0.1,
    },
    # --- 🔬 Parámetros de comportamiento (calibración, avanzado) — ya calibrados contra la serie
    # real 2018-2023 (ver config_abm.py); tocarlos aquí sirve para explorar sensibilidad, no son
    # controles de política.
    "capacidad_recoleccion_individual": {
        "type": "SliderFloat", "label": "🔬 Capacidad de recolección por reciclador (kg/día)",
        "value": config_abm.CAPACIDAD_RECOLECCION_KG_DIA_POR_RECICLADOR, "min": 5.0, "max": 30.0, "step": 1.0,
    },
    "beta_decaimiento": {
        "type": "SliderFloat", "label": "🔬 Tasa de decaimiento de la separación (free-riding)",
        "value": config_abm.BETA_DECAIMIENTO_SEPARACION, "min": 0.0, "max": 0.10, "step": 0.01,
    },
    "beta_recuperacion": {
        "type": "SliderFloat", "label": "🔬 Tasa de recuperación de la separación",
        "value": config_abm.BETA_RECUPERACION_SEPARACION, "min": 0.0, "max": 0.10, "step": 0.01,
    },
    "umbral_percepcion_impacto": {
        "type": "SliderFloat", "label": "🔬 Margen de percepción de impacto (relativo a la base propia)",
        "value": config_abm.UMBRAL_PERCEPCION_IMPACTO, "min": 0.0, "max": 0.10, "step": 0.005,
    },
    "factor_brecha_intencion_accion": {
        "type": "SliderFloat", "label": "🔬 Brecha intención-acción (encuesta → aprovechamiento medido)",
        "value": config_abm.FACTOR_BRECHA_INTENCION_ACCION, "min": 0.20, "max": 1.00, "step": 0.05,
    },
}

# Línea base REAL (multiplicadores=1.0, sin intervención) — corrida offline una sola vez, misma
# semilla que el dashboard (`config_abm.SEMILLA_ALEATORIA`). Sirve de referencia fija para el
# panel "Escenarios y política": comparar cualquier escenario contra "lo que hay hoy", sin tener
# que correr dos simulaciones completas en vivo cada vez.
# Refrescada 2026-07-14 (ronda 5): `prob_separa` cambió de fuente (ECA2021/localidad → EM2021/UPZ)
# y se recalibró — ver Justificacion_Metodologica_Comite.md §5bis.
_LINEA_BASE_REAL = {
    "pct_aprovechamiento": 18.80,
    "generado_total_ton": 2_478_285.8,
    "aprovechado_total_ton": 465_907.9,
    "rechazo_total_ton": 2_012_377.9,
    "costo_fiscal_viat_cop": 465_907.9 * config_abm.VIAT_PESOS_POR_TONELADA,
}


@solara.component
def PanelLateralPanorama(model):
    """Panel compacto de leyenda + conteo de agentes, al lado del mapa principal (layout
    inspirado en la referencia que prefirió el usuario: mapa grande + panel lateral)."""
    update_counter.get()
    n_hogares = len(model.agents_by_type[HogarAgente])
    n_recicladores = len(model.agents_by_type[PoblacionRecicladoresUPZ])
    n_operadores = len(model.operadores_ase)

    with solara.Column(style="gap:10px;"):
        with solara.Card("Agentes activos", style=f"background-color:{SURFACE};"):
            for etiqueta, valor, color in [
                ("Hogares (muestra real)", f"{n_hogares:,}", AZUL),
                ("Poblaciones de recicladores", f"{n_recicladores}", AQUA),
                ("Operadores ASE", f"{n_operadores}", AMARILLO),
                ("Puntos críticos reales (SIGAB)", f"{len(_PUNTOS_CRITICOS_REALES)}", CRITICO),
            ]:
                with solara.Row(style="justify-content:space-between;"):
                    solara.Text(etiqueta, style=f"color:{INK_SECUNDARIO}; font-size:0.78rem;")
                    solara.Text(valor, style=f"color:{color}; font-weight:700; font-size:0.78rem;")

        with solara.Card("Leyenda del mapa", style=f"background-color:{SURFACE};"):
            for marcador, etiqueta, color in [
                ("●", "Hogar — estrato bajo (simbólico)", AMARILLO),
                ("●", "Hogar — estrato medio (simbólico)", VIOLETA),
                ("●", "Hogar — estrato alto (simbólico)", MAGENTA),
                ("✕", "Punto crítico REAL (SIGAB)", CRITICO),
            ]:
                with solara.Row(style="gap:8px;"):
                    solara.Text(marcador, style=f"color:{color}; font-weight:700;")
                    solara.Text(etiqueta, style=f"color:{INK_SECUNDARIO}; font-size:0.76rem;")
            solara.Text(
                "Los hogares son posiciones simbólicas/ilustrativas (no hay GPS real de hogares) "
                "— la composición por estrato y las zonas sí son 100% reales. Camiones/rutas "
                "individuales se omiten por ahora (sin dato real de flota, ver "
                "Reglas_Negocio_v2_y_Modelado_Agentes.md §4quater) — quedan para una fase futura.",
                style=f"color:{INK_MUTED}; font-size:0.68rem; margin-top:4px;",
            )


@solara.component
def EncabezadoSeccion(numero: str, titulo: str, subtitulo: str, color: str = AZUL):
    """Marca de sección para una página continua de una sola pantalla (sin pestañas, por
    decisión explícita del usuario: "quiero una sola página robusta... un control de mando
    avanzado"). El color lateral + el número grande dan orientación visual sin necesidad de
    clics — se puede ver TODO haciendo scroll, nada queda escondido detrás de una pestaña."""
    with solara.Row(style=f"align-items:center; gap:14px; margin-top:10px; border-left:5px solid {color}; padding-left:14px;"):
        solara.Text(numero, style=f"color:{color}; font-size:2.1rem; font-weight:800; opacity:0.55;")
        with solara.Column(style="gap:0px;"):
            solara.Text(titulo, style=f"color:{INK_PRIMARIO}; font-size:1.25rem; font-weight:700;")
            solara.Text(subtitulo, style=f"color:{INK_MUTED}; font-size:0.8rem;")


@solara.component
def Page():
    solara.Style("""
    .v-application { background-color: #0d0d0d !important; }
    """)
    model = solara.use_reactive(_MODELO_INICIAL)
    reactive_model_parameters = solara.use_reactive({})
    reactive_play_interval = solara.use_reactive(80)
    reactive_render_interval = solara.use_reactive(1)
    reactive_use_threads = solara.use_reactive(False)
    contador_anio_completo = solara.use_reactive(0)
    vista_geografica = solara.use_reactive("UPZ")
    vista_columna_mapa = solara.use_reactive("% Aprovechamiento")

    def _correr_anio_completo():
        if contador_anio_completo.value == 0:
            return
        model.value.correr_anio()
        force_update()

    tarea_anio_completo = solara.lab.use_task(
        _correr_anio_completo, dependencies=[contador_anio_completo.value], prefer_threaded=True,
    )

    with solara.AppBar():
        solara.AppBarTitle("Bogotá en vivo — Simulación de Aprovechamiento de Residuos (ABM)")
        solara.lab.ThemeToggle()

    with solara.Sidebar(), solara.Column():
        with solara.Card("Controles"):
            solara.SliderInt(
                label="Play Interval (ms)", value=reactive_play_interval,
                on_value=reactive_play_interval.set, min=20, max=500, step=10,
            )
            ModelController(
                model, model_parameters=reactive_model_parameters,
                play_interval=reactive_play_interval, render_interval=reactive_render_interval,
                use_threads=reactive_use_threads,
            )
            solara.Button(
                "▶▶ Correr año completo (365 días)", color="primary", block=True,
                style="margin-top:6px;",
                disabled=tarea_anio_completo.pending or not model.value.running,
                on_click=lambda: contador_anio_completo.set(contador_anio_completo.value + 1),
            )
            if tarea_anio_completo.pending:
                solara.Text("Corriendo los 365 días… (~1-2 min, no se congela la página)",
                             style=f"color:{INK_MUTED}; font-size:0.72rem;")
            if not model.value.running:
                solara.Text("Año completo (365/365) — usa Reset para volver a correr.",
                             style=f"color:{BUENO}; font-size:0.72rem;")
        with solara.Card("Parámetros del modelo"):
            solara.Text(
                "🏛️ Escenario (2 primeros) = mecanismo causal verificado, para política pública. "
                "🔬 Resto = parámetros de calibración del comportamiento, para explorar sensibilidad.",
                style=f"color:{INK_MUTED}; font-size:0.68rem; margin-bottom:6px;",
            )
            ModelCreator(model, _PARAMETROS_MODELO, model_parameters=reactive_model_parameters)
        with solara.Card("Estado"):
            ShowSteps(model.value)

    m = model.value
    with solara.Column(style=f"background-color:{PAGINA}; padding:12px; gap:10px;"):
        FilaKPIs(m)

        EncabezadoSeccion("1", "Panorama en vivo", "Mapa real de Bogotá + tendencias del año en curso", AZUL)
        with solara.Column(style="gap:12px; padding-top:6px;"):
            with solara.Row(style="gap:16px; flex-wrap:wrap; align-items:center;"):
                solara.ToggleButtonsSingle(
                    value=vista_geografica.value, on_value=vista_geografica.set,
                    values=["UPZ", "Localidad"],
                )
                solara.ToggleButtonsSingle(
                    value=vista_columna_mapa.value, on_value=vista_columna_mapa.set,
                    values=["% Aprovechamiento", "Generación"],
                )
            with solara.Columns([2, 1]):
                MapaPrincipal(m, vista=vista_geografica.value, columna=vista_columna_mapa.value)
                PanelLateralPanorama(m)
            FilaMiniGraficos(m)
            SeriesTemporalesBalance(m)
            SerieAprovechamientoPct(m)
            PanelComportamientoAgentes(m)

        EncabezadoSeccion("2", "Escenarios y política", "Controles 🏛️ del sidebar — compara cualquier intervención contra la línea base real", AQUA)
        with solara.Column(style="gap:12px; padding-top:6px;"):
            PanelEscenarioComparacion(m)
            GraficoBalanceEscenario(m)

        EncabezadoSeccion("3", "Rigor y validación", "Real vs. simulado, sensibilidad de parámetros, límites declarados", VIOLETA)
        with solara.Column(style="gap:12px; padding-top:6px;"):
            GraficoContrafactual(m)
            PanelSensibilidadParametros()
            PanelLimitacionesHonestas()

        EncabezadoSeccion("4", "Cómo funciona el sistema", "Mecanismos reales detrás del modelo, en lenguaje simple", AMARILLO)
        with solara.Column(style="gap:12px; padding-top:6px;"):
            IntroPublicoGeneral()
            with solara.Row(style="gap:12px; flex-wrap:wrap;"):
                MapaInfraestructuraReal(m)
                MapaIncentivoEconomico(m)
            RankingUPZ(m, vista=vista_geografica.value)
            with solara.Row(style="gap:12px; flex-wrap:wrap;"):
                PanelComposicionReal()
                GraficoGeneracionPorEstrato(m)

        EncabezadoSeccion("5", "Agentes y registro de simulación", "Detalle técnico: conteos, flujo real y log día a día", MAGENTA)
        with solara.Column(style="gap:12px; padding-top:6px;"):
            PanelAgentesYLog(m)
            PanelFlujoAgentes(m)
