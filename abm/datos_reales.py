"""Variables reales de la Fase 2/3 que reemplazan supuestos del MVP original (ver
`Reglas_Negocio_v2_y_Modelado_Agentes.md`). Cada función sigue el mismo patrón que
`entorno.construir_o_cargar_adyacencia_upz`: se calcula una sola vez desde las fuentes crudas y
se cachea en `data/processed/`, en vez de recalcularse en cada corrida del modelo.

Todas parten de datos ya verificados en `Recoleccion_Datos_Fase2.md` y
`Auditoria_Completa_Datos_Limpieza_EDA.md`.
"""
import re
import sys
import unicodedata
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src import carga_datos, config as config_datos, geoespacial  # noqa: E402

DATA_PROCESSED = config_datos.DATA_PROCESSED

RUTA_INFRAESTRUCTURA_REAL = DATA_PROCESSED / "16_infraestructura_real_upz.csv"
RUTA_PARTICIPACION_COMUNITARIA = DATA_PROCESSED / "17_participacion_comunitaria_localidad.csv"
RUTA_FORMALIZACION_RECICLADORES = DATA_PROCESSED / "18_formalizacion_recicladores_localidad.csv"
RUTA_CAPACIDAD_ASE = DATA_PROCESSED / "19_capacidad_ase.csv"
RUTA_INFRAESTRUCTURA_POR_ANIO = DATA_PROCESSED / "20_infraestructura_real_upz_por_anio.csv"
RUTA_CAPACIDAD_ASE_POR_ANIO = DATA_PROCESSED / "21_capacidad_ase_por_anio.csv"
RUTA_PERFIL_HOGAR_LOCALIDAD = DATA_PROCESSED / "25_perfil_hogar_localidad.csv"
RUTA_CROSSWALK_EM2021_UPZ = DATA_PROCESSED / "26_crosswalk_em2021_upz.csv"
RUTA_SEPARACION_UPZ_EM2021 = DATA_PROCESSED / "27_separacion_upz_em2021.csv"

# Snapshot SIGAB -> año calendario que representa.
_SIGAB_SNAPSHOT_ANIO = {
    "sigab_2020": 2020, "sigab_2022_diciembre": 2022, "sigab_2024_diciembre": 2024, "sigab_2026_junio": 2026,
}
# Meses de cobertura mínima en el RBL consolidado para confiar en la cifra ANUAL propia de ese
# año (en vez de recurrir al promedio histórico multi-año) — ver docstring de
# `construir_o_cargar_capacidad_ase_por_anio`.
_RBL_MIN_MESES_CONFIABLE = 6

# Factor de subsidio(-)/contribución(+) real por estrato — CRA / Ciudad Limpia, dic-2025
# (`Recoleccion_Datos_Fase2.md` §3.5). Tarifa oficial real, no un supuesto.
FACTOR_SUBSIDIO_POR_ESTRATO = {1: -0.70, 2: -0.40, 3: -0.15, 4: 0.0, 5: 0.50, 6: 0.60}
VIAT_PESOS_POR_TONELADA = 11_388.0


def _normalizar_texto(s) -> str:
    s = str(s).strip().lower()
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")


def _normalizar_nombre_upz(s) -> str:
    """Como `_normalizar_texto`, pero además colapsa todo lo que no sea letra/número a un solo
    espacio — para comparar nombres de UPZ escritos de forma inconsistente entre fuentes (ej.
    puntuación/guiones distintos). El caso "sin espacio" (ej. "Monteblanco" en EM2021 vs. el
    nombre real "MONTE BLANCO") se resuelve aparte, comparando también la versión sin espacios
    (ver `_construir_crosswalk_em2021_upz`)."""
    return re.sub(r"[^a-z0-9]+", " ", _normalizar_texto(s)).strip()


def _promedio_ponderado_simple(valores: pd.Series, pesos: pd.Series) -> float:
    """Promedio ponderado de dos Series alineadas por índice, con descarte de pares con valor o
    peso nulo (listwise deletion) — la pieza compartida entre los promedios por UPZ y por
    localidad de `construir_o_cargar_separacion_upz_em2021`."""
    datos = pd.DataFrame({"v": valores, "p": pesos}).dropna()
    if datos["p"].sum() <= 0:
        return float("nan")
    return float(np.average(datos["v"], weights=datos["p"]))


def _conteos_puntos_criticos_por_snapshot() -> pd.DataFrame:
    """Tabla UPZ x snapshot con el conteo de puntos críticos SIGAB en cada corte — la pieza
    compartida entre la versión blended (`construir_o_cargar_infraestructura_real`) y la versión
    por año (`construir_o_cargar_infraestructura_real_por_anio`)."""
    gdf_upz = carga_datos.cargar_upz_limites()
    gdf_upz["CODIGO_UPZ"] = pd.to_numeric(gdf_upz["CODIGO_UPZ"], errors="coerce")
    gdf_upz = gdf_upz.dropna(subset=["CODIGO_UPZ"])

    conteos_por_snapshot = []
    for snapshot in _SIGAB_SNAPSHOT_ANIO:
        datos = carga_datos.cargar_sigab_snapshot(snapshot)
        puntos = datos.get("puntos_criticos")
        if puntos is None:
            continue
        col_lon = [c for c in puntos.columns if "LONG" in c.upper()][0]
        col_lat = [c for c in puntos.columns if "LAT" in c.upper()][0]
        gdf_puntos = carga_datos.puntos_desde_lonlat(puntos, col_lon, col_lat)
        gdf_puntos_upz = geoespacial.join_puntos_a_upz(gdf_puntos, gdf_upz)
        conteo = gdf_puntos_upz.groupby("CODIGO_UPZ").size().rename(snapshot)
        conteos_por_snapshot.append(conteo)

    tabla_conteos = pd.concat(conteos_por_snapshot, axis=1).fillna(0.0)
    tabla_conteos = gdf_upz[["CODIGO_UPZ"]].set_index("CODIGO_UPZ").join(tabla_conteos).fillna(0.0)
    return tabla_conteos


def _index_desde_conteos(serie_conteos: pd.Series) -> pd.Series:
    """Convierte un conteo de puntos críticos en el índice normalizado 1=buena cobertura. Misma
    convención en la versión blended y en la versión por año: más puntos críticos = peor
    infraestructura, se invierte (1 - normalizado), con piso 0.2 para no anular ninguna UPZ."""
    maximo = serie_conteos.max()
    normalizado = serie_conteos / maximo if maximo > 0 else 0.0
    return (1.0 - normalizado).clip(lower=0.2)


def construir_o_cargar_infraestructura_real() -> pd.DataFrame:
    """Índice de infraestructura REAL por UPZ, a partir del promedio de puntos críticos de los
    4 snapshots de SIGAB (2020, dic-2022, dic-2024, jun-2026) — reemplaza la fórmula sintética
    de `agentes_infraestructura.calcular_infraestructura_index_sintetico` (ver
    `Reglas_Negocio_v2_y_Modelado_Agentes.md` §3.1). Se conserva como el valor por defecto (p.ej.
    para años fuera del rango 2018-2024 de calibración); para simulación multi-año usar
    `construir_o_cargar_infraestructura_real_por_anio`, que preserva la evolución real en vez de
    diluirla en un solo promedio.
    """
    if RUTA_INFRAESTRUCTURA_REAL.exists():
        return pd.read_csv(RUTA_INFRAESTRUCTURA_REAL)

    tabla_conteos = _conteos_puntos_criticos_por_snapshot()
    promedio = tabla_conteos.mean(axis=1).rename("n_puntos_criticos_promedio")

    resultado = promedio.reset_index()
    resultado["infraestructura_index_real"] = _index_desde_conteos(resultado["n_puntos_criticos_promedio"])
    resultado = resultado.rename(columns={"CODIGO_UPZ": "UPZ"})

    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    resultado.to_csv(RUTA_INFRAESTRUCTURA_REAL, index=False)
    return resultado


def construir_o_cargar_infraestructura_real_por_anio() -> pd.DataFrame:
    """Versión SIN blending del índice de infraestructura: un valor real por UPZ para CADA uno
    de los 4 snapshots SIGAB (2020, 2022, 2024, 2026), en vez de un único promedio de los 4.

    Se usa para dar a la simulación multi-año (`abm/calibracion.py`) una fuente REAL de variación
    en el tiempo — antes de este cambio, el índice de infraestructura era idéntico en los 7 años
    simulados (2018-2024), lo cual, junto con que `pct_separa_en_fuente` también es estático (una
    sola encuesta EM2021 repetida), dejaba al modelo sin ningún mecanismo real capaz de explicar
    una tendencia — ver la decomposición shift-share en `Investigacion_Salto_Aprovechamiento.md`.
    Un año simulado que no coincide con ningún snapshot toma el snapshot real más cercano en el
    tiempo (empate se resuelve con el snapshot anterior, no el futuro, para no usar información
    "del futuro" en años de calibración pasados).
    """
    if RUTA_INFRAESTRUCTURA_POR_ANIO.exists():
        return pd.read_csv(RUTA_INFRAESTRUCTURA_POR_ANIO)

    tabla_conteos = _conteos_puntos_criticos_por_snapshot()
    filas = []
    for snapshot, anio_snapshot in _SIGAB_SNAPSHOT_ANIO.items():
        indice = _index_desde_conteos(tabla_conteos[snapshot])
        for codigo_upz, valor in indice.items():
            filas.append({"UPZ": codigo_upz, "anio_snapshot": anio_snapshot, "infraestructura_index_real": valor})

    resultado = pd.DataFrame(filas)
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    resultado.to_csv(RUTA_INFRAESTRUCTURA_POR_ANIO, index=False)
    return resultado


def snapshot_infraestructura_mas_cercano(anio_simulado: int, anios_disponibles: list[int]) -> int:
    """Año de snapshot SIGAB real más cercano a `anio_simulado`. En empate exacto (equidistante
    entre un snapshot pasado y uno futuro) se prefiere el PASADO, para que un año de calibración
    histórico nunca use infraestructura "del futuro" que en ese momento no existía."""
    return min(anios_disponibles, key=lambda a: (abs(a - anio_simulado), a > anio_simulado))


def _promedio_ponderado_por_grupo(df: pd.DataFrame, columna_valor: str, columna_peso: str,
                                   columna_grupo: str) -> pd.Series:
    """Promedio ponderado por `columna_peso` (factor de expansión de la encuesta), agrupado por
    `columna_grupo` — descarta filas con valor o peso nulo antes de promediar (listwise deletion).
    Ver `Reglas_Negocio_v2_y_Modelado_Agentes.md` §4bis: ponderar por `FEX_C` cambió magnitudes
    reales (ej. odds ratio de JAC 2.05→2.63) frente a promediar la muestra cruda — "son las
    ponderadas las que hay que citar en la tesis, no las crudas".
    """
    datos = df[[columna_valor, columna_peso, columna_grupo]].dropna()

    def _promedio(grupo: pd.DataFrame) -> float:
        peso_total = grupo[columna_peso].sum()
        if peso_total <= 0:
            return float("nan")
        return float(np.average(grupo[columna_valor], weights=grupo[columna_peso]))

    return datos.groupby(columna_grupo).apply(_promedio, include_groups=False)


def construir_o_cargar_participacion_comunitaria() -> pd.DataFrame:
    """% de hogares que participan en Junta de Acción Comunal o en organización ambiental, por
    localidad (EM2021) — el predictor más fuerte encontrado en toda la Fase 3 del EDA. Solo
    existe a nivel localidad (`COD_LOCALIDAD`), no UPZ — mismo límite de resolución que
    `pct_separa_en_fuente` (ver `Diseno_ABM.md` §8).

    Ponderado por `FEX_C` (factor de expansión de la encuesta) — corregido 2026-07-14: la versión
    original de esta función promediaba la muestra cruda sin ponderar, pese a que la Sección 8bis
    del EDA (`EDA_Dirigido_Fase3.ipynb`) ya había demostrado que la muestra sin ponderar
    sobrerrepresenta personas muy participativas (ver `Justificacion_Metodologica_Comite.md`).
    """
    if RUTA_PARTICIPACION_COMUNITARIA.exists():
        return pd.read_csv(RUTA_PARTICIPACION_COMUNITARIA)

    df_em = carga_datos.cargar_multiproposito()
    df_em["_cod_localidad"] = pd.to_numeric(df_em["COD_LOCALIDAD"], errors="coerce")
    df_em["_peso"] = pd.to_numeric(df_em["FEX_C"], errors="coerce")
    df_em["_participa"] = (
        (df_em["NPCJP1F"] == "1") | (df_em["NPCJP1I"] == "1")
    ).astype(float)

    resultado = (
        _promedio_ponderado_por_grupo(df_em, "_participa", "_peso", "_cod_localidad")
        .mul(100)
        .rename("pct_participacion_comunitaria")
        .reset_index()
        .rename(columns={"_cod_localidad": "codigo_localidad"})
    )
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    resultado.to_csv(RUTA_PARTICIPACION_COMUNITARIA, index=False)
    return resultado


def construir_o_cargar_perfil_hogar_localidad() -> pd.DataFrame:
    """% real por localidad (EM2021, ponderado por `FEX_C`) de los 2 predictores de separación
    validados en la Sección 8/9 del EDA (`EDA_Dirigido_Fase3.ipynb`, regresión logística
    multivariada ponderada, n=60,235 hogares muestra / 2,061,804 reales) que hasta 2026-07-14 no
    se usaban en el ABM más allá de participación comunitaria:

    - `pct_vivienda_propia` (`NVCBP10==1`, "Casa"): odds ratio real ponderado ≈1.40, p<0.001.
      Es el proxy de tenencia usado en el propio EDA ("1=Casa, proxy simple de tipo/tenencia" —
      NO es la variable legal de propiedad, se documenta así también en
      `Justificacion_Metodologica_Comite.md` para no sobrevender la etiqueta).
    - `pct_informal` (`OINFORMAL`, binaria DANE, 1=ocupado informal): odds ratio real ponderado
      ≈0.85, p<0.001, dirección negativa (reduce la probabilidad de separar).

    Mismo límite de resolución que `construir_o_cargar_participacion_comunitaria`: real solo a
    nivel localidad, no UPZ (ver `Diseno_ABM.md` §8). `log_ingreso` NO se incluye aquí: se probó
    en el EDA y no fue significativo (p=0.33) — se documenta como descartado, no como omisión.
    """
    if RUTA_PERFIL_HOGAR_LOCALIDAD.exists():
        return pd.read_csv(RUTA_PERFIL_HOGAR_LOCALIDAD)

    df_em = carga_datos.cargar_multiproposito()
    df_em["_cod_localidad"] = pd.to_numeric(df_em["COD_LOCALIDAD"], errors="coerce")
    df_em["_peso"] = pd.to_numeric(df_em["FEX_C"], errors="coerce")
    df_em["_vivienda_propia"] = (pd.to_numeric(df_em["NVCBP10"], errors="coerce") == 1).astype(float)
    df_em["_informal"] = pd.to_numeric(df_em["OINFORMAL"].replace("NA", np.nan), errors="coerce")

    resultado = (
        _promedio_ponderado_por_grupo(df_em, "_vivienda_propia", "_peso", "_cod_localidad")
        .mul(100)
        .rename("pct_vivienda_propia")
        .to_frame()
    )
    resultado["pct_informal"] = (
        _promedio_ponderado_por_grupo(df_em, "_informal", "_peso", "_cod_localidad").mul(100)
    )
    resultado = resultado.reset_index().rename(columns={"_cod_localidad": "codigo_localidad"})

    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    resultado.to_csv(RUTA_PERFIL_HOGAR_LOCALIDAD, index=False)
    return resultado


def construir_o_cargar_formalizacion_recicladores() -> pd.DataFrame:
    """Dos indicadores DISTINTOS de formalización de recicladores por localidad (RURO 2022):
    `pct_registro_activo` (estar vigente en el RURO, ~90% de la ciudad) y
    `pct_formalizacion_laboral` (afiliación ARL, ~0-14%) — no son lo mismo, ver
    `Reglas_Negocio_v2_y_Modelado_Agentes.md` §3.6.
    """
    if RUTA_FORMALIZACION_RECICLADORES.exists():
        return pd.read_csv(RUTA_FORMALIZACION_RECICLADORES)

    gdf_recol = carga_datos.cargar_macrorutas("recoleccion")
    mapa_localidad_a_codigo = (
        gdf_recol[["IDLOCALID", "NOMLOCALID"]]
        .dropna()
        .assign(_clave=lambda d: d["NOMLOCALID"].map(_normalizar_texto))
        .drop_duplicates("_clave")
        .set_index("_clave")["IDLOCALID"]
        .to_dict()
    )

    df_ruro = carga_datos.cargar_ruro_2022_por_localidad()
    df_ruro["_clave"] = df_ruro["Nom_Localidad"].map(_normalizar_texto)
    df_ruro["codigo_localidad"] = df_ruro["_clave"].map(mapa_localidad_a_codigo)

    agregado = df_ruro.groupby("codigo_localidad").agg(
        total_recicladores=("#Recicladores", "sum"),
        con_arl=("#ARL", "sum"),
    )
    agregado["pct_formalizacion_laboral"] = 100 * agregado["con_arl"] / agregado["total_recicladores"]

    df_ruro["_activo"] = (df_ruro["Estado En Ruro"].astype(str).str.strip().str.upper() == "ACTIVO")
    activos = (
        df_ruro.groupby("codigo_localidad")
        .apply(lambda d: 100 * (d.loc[d["_activo"], "#Recicladores"].sum() / d["#Recicladores"].sum()) if d["#Recicladores"].sum() else 0.0, include_groups=False)
        .rename("pct_registro_activo")
    )

    resultado = agregado.join(activos)[["pct_registro_activo", "pct_formalizacion_laboral"]].reset_index()
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    resultado.to_csv(RUTA_FORMALIZACION_RECICLADORES, index=False)
    return resultado


def construir_o_cargar_capacidad_ase() -> pd.DataFrame:
    """Capacidad diaria real de recolección formal por ASE (promedio histórico de toneladas
    domiciliarias/mes del RBL consolidado, esquema `ase_2018+` únicamente — reemplaza el
    supuesto "capacidad no vinculante" por una capacidad medida (`Reglas_Negocio_v2...` §4quater).
    Se conserva como valor por defecto (años sin cobertura suficiente); para simulación
    multi-año usar `construir_o_cargar_capacidad_ase_por_anio`.
    """
    if RUTA_CAPACIDAD_ASE.exists():
        return pd.read_csv(RUTA_CAPACIDAD_ASE)

    df_rbl = carga_datos.cargar_rbl_consolidado()
    df_comparable = df_rbl[(df_rbl["esquema"] == "ase_2018+") & (df_rbl["tipo_residuo"] == "domiciliario")]

    # BUG corregido (2026-07-11): `.sum()` por (año, operador) da un TOTAL ANUAL (suma de los
    # meses disponibles ese año), no un total mensual — dividir ese total anual por 30 inflaba la
    # capacidad diaria ~12x (resultaba en ~38,913 ton/día de capacidad formal agregada, 5 veces
    # la generación diaria real de TODA la ciudad, ~7,300-10,900 ton/día). Se divide por 365.
    promedio_anual = df_comparable.groupby(["anio", "operador"])["toneladas"].sum().groupby("operador").mean()
    resultado = (promedio_anual / 365.0).rename("capacidad_dia_ton").reset_index().rename(columns={"operador": "ase"})
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    resultado.to_csv(RUTA_CAPACIDAD_ASE, index=False)
    return resultado


def construir_o_cargar_capacidad_ase_por_anio() -> pd.DataFrame:
    """Capacidad diaria real por ASE, un valor DISTINTO para cada año 2018-2025 (en vez del
    promedio histórico único de `construir_o_cargar_capacidad_ase`).

    La cobertura mensual del RBL consolidado es irregular en los años tempranos (auditoría ya
    documentada en `Recoleccion_Datos_Fase2.md`: 2018=3 meses, 2019=5, 2020=3 —tras corregir un
    bug real de parseo en `cargar_rbl_consolidado`, ver nota en `src/carga_datos.py`—, 2021=9,
    2022=11, 2023=9, 2024=12). Un año con pocos meses no se anualiza ingenuamente (sesgaría la
    capacidad hacia abajo/arriba según qué meses falten): se extrapola por regla de tres desde
    los meses SÍ disponibles (`suma / n_meses * 12`), y se marca `confiable=False` cuando hay
    menos de `_RBL_MIN_MESES_CONFIABLE` meses — para esos años, el llamador debe preferir el
    promedio histórico blended (`construir_o_cargar_capacidad_ase`) en vez de este valor ruidoso.
    """
    if RUTA_CAPACIDAD_ASE_POR_ANIO.exists():
        return pd.read_csv(RUTA_CAPACIDAD_ASE_POR_ANIO)

    df_rbl = carga_datos.cargar_rbl_consolidado()
    df_comparable = df_rbl[(df_rbl["esquema"] == "ase_2018+") & (df_rbl["tipo_residuo"] == "domiciliario")]

    agregado = df_comparable.groupby(["anio", "operador"]).agg(
        toneladas_suma=("toneladas", "sum"), meses_disponibles=("mes", "nunique"),
    ).reset_index()
    agregado["capacidad_dia_ton"] = (
        agregado["toneladas_suma"] / agregado["meses_disponibles"] * 12.0 / 365.0
    )
    agregado["confiable"] = agregado["meses_disponibles"] >= _RBL_MIN_MESES_CONFIABLE

    resultado = agregado.rename(columns={"operador": "ase"})[
        ["anio", "ase", "capacidad_dia_ton", "meses_disponibles", "confiable"]
    ]
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    resultado.to_csv(RUTA_CAPACIDAD_ASE_POR_ANIO, index=False)
    return resultado


def _construir_crosswalk_em2021_upz() -> pd.DataFrame:
    """Cruza `COD_UPZ_GRUPO`/`NOMBRE_UPZ_GRUPO` (EM2021) con las 112 UPZ reales
    (`carga_datos.cargar_upz_limites`). La mayoría de los códigos EM2021 coinciden EXACTAMENTE
    con `CODIGO_UPZ` real (son UPZ individuales); los códigos de la serie 800+ son grupos de 2-4
    UPZ reales fusionadas por diseño muestral (ej. "USAQUÉN: Country Club + Santa Bárbara" = UPZ
    reales 15+16) — se resuelven parseando el nombre del grupo y macheándolo contra el nombre
    real de cada UPZ (con y sin espacios, para casos como "Monteblanco" vs. "MONTE BLANCO").

    Verificado (2026-07-14): 111 de las 112 UPZ reales cubiertas, sin conflictos (ninguna UPZ
    real cae en 2 grupos EM2021 distintos) — ver `Justificacion_Metodologica_Comite.md`.
    """
    if RUTA_CROSSWALK_EM2021_UPZ.exists():
        return pd.read_csv(RUTA_CROSSWALK_EM2021_UPZ, dtype=str)

    gdf_upz = carga_datos.cargar_upz_limites()
    gdf_upz["CODIGO_UPZ"] = gdf_upz["CODIGO_UPZ"].astype(str).str.strip()
    codigos_reales = set(gdf_upz["CODIGO_UPZ"])
    nombre_a_codigo = {
        _normalizar_nombre_upz(nombre): codigo
        for codigo, nombre in zip(gdf_upz["CODIGO_UPZ"], gdf_upz["NOMBRE"])
    }
    nombre_sin_espacios_a_codigo = {clave.replace(" ", ""): codigo for clave, codigo in nombre_a_codigo.items()}

    df_em = carga_datos.cargar_multiproposito()
    grupos = df_em[["COD_UPZ_GRUPO", "NOMBRE_UPZ_GRUPO"]].dropna().drop_duplicates()

    filas = []
    for _, fila in grupos.iterrows():
        cod = str(fila["COD_UPZ_GRUPO"]).strip()
        nombre_grupo = str(fila["NOMBRE_UPZ_GRUPO"])
        if cod in codigos_reales:
            # Coincidencia directa por código: el "grupo" es en realidad 1 sola UPZ real.
            filas.append({"cod_upz_grupo_em2021": cod, "codigo_upz_real": cod})
            continue

        # Código de grupo (serie 800+): "LOCALIDAD: NombreA + NombreB + ..."
        parte_nombres = nombre_grupo.split(":", 1)[-1]
        for candidato in parte_nombres.split("+"):
            clave = _normalizar_nombre_upz(candidato)
            codigo_real = nombre_a_codigo.get(clave) or nombre_sin_espacios_a_codigo.get(clave.replace(" ", ""))
            if codigo_real is not None:
                filas.append({"cod_upz_grupo_em2021": cod, "codigo_upz_real": codigo_real})

    resultado = pd.DataFrame(filas).drop_duplicates().reset_index(drop=True)
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    resultado.to_csv(RUTA_CROSSWALK_EM2021_UPZ, index=False)
    return resultado


def construir_o_cargar_separacion_upz_em2021() -> pd.DataFrame:
    """% de hogares que separan residuos (`NHCCP38`) y % de calidad de separación (cuántos de 6
    tipos de material separa, `NHCCP38AA-AG`), por UPZ REAL — EM2021, ponderado por `FEX_C`,
    deduplicado a nivel hogar (`DIRECTORIO_HOG`; verificado que `FEX_C`/`COD_UPZ_GRUPO` son
    constantes dentro de un mismo hogar, 0 excepciones en 107,119 hogares).

    Reemplaza a `pct_separa_en_fuente`/`pct_calidad_separacion` (ECA2021, congelados en
    `data/processed/05_actores.csv`), que solo eran reales a nivel LOCALIDAD (20, algunas con
    muestra degenerada: Los Mártires n=1, Santa Fe n=3) — aquí cada UPZ real tiene su propia
    medición, con 600-1,300+ hogares de muestra cada una (ver
    `Justificacion_Metodologica_Comite.md`).

    La única UPZ sin cobertura directa del crosswalk cae al promedio de su localidad (mismo
    criterio de fallback que ya usaba `05_actores.csv`) — marcado explícitamente en la columna
    `es_fallback_localidad`, no de forma silenciosa.
    """
    if RUTA_SEPARACION_UPZ_EM2021.exists():
        return pd.read_csv(RUTA_SEPARACION_UPZ_EM2021)

    columnas_material = ["NHCCP38AA", "NHCCP38AB", "NHCCP38AC", "NHCCP38AD", "NHCCP38AF", "NHCCP38AG"]

    df_em = carga_datos.cargar_multiproposito()
    df_hogares = df_em.drop_duplicates(subset="DIRECTORIO_HOG").copy()
    df_hogares["_peso"] = pd.to_numeric(df_hogares["FEX_C"], errors="coerce")
    df_hogares["_cod_localidad"] = pd.to_numeric(df_hogares["COD_LOCALIDAD"], errors="coerce")
    df_hogares["_separa"] = (df_hogares["NHCCP38"] == "1").astype(float)
    df_hogares["_calidad"] = (
        sum((df_hogares[c] == "1").astype(float) for c in columnas_material) / len(columnas_material)
    )

    crosswalk = _construir_crosswalk_em2021_upz()
    df_hogares = df_hogares.merge(
        crosswalk, left_on="COD_UPZ_GRUPO", right_on="cod_upz_grupo_em2021", how="left"
    )

    por_upz = (
        df_hogares.dropna(subset=["codigo_upz_real"])
        .groupby("codigo_upz_real")
        .apply(
            lambda g: pd.Series({
                "pct_separa_upz": 100 * _promedio_ponderado_simple(g["_separa"], g["_peso"]),
                "pct_calidad_separacion_upz": 100 * _promedio_ponderado_simple(g["_calidad"], g["_peso"]),
                "n_hogares": len(g),
            }),
            include_groups=False,
        )
        .reset_index()
        .rename(columns={"codigo_upz_real": "UPZ"})
    )
    por_upz["UPZ"] = por_upz["UPZ"].astype(str)
    por_upz["es_fallback_localidad"] = False

    por_localidad = (
        df_hogares.dropna(subset=["_cod_localidad"])
        .groupby("_cod_localidad")
        .apply(
            lambda g: pd.Series({
                "pct_separa_localidad": 100 * _promedio_ponderado_simple(g["_separa"], g["_peso"]),
                "pct_calidad_separacion_localidad": 100 * _promedio_ponderado_simple(g["_calidad"], g["_peso"]),
            }),
            include_groups=False,
        )
        .reset_index()
        .rename(columns={"_cod_localidad": "codigo_localidad"})
    )

    df_upz_localidad = pd.read_csv(config_datos.DATA_PROCESSED / "df_modelo.csv")[["UPZ", "codigo_localidad"]]
    df_upz_localidad = df_upz_localidad.drop_duplicates()
    df_upz_localidad["UPZ"] = df_upz_localidad["UPZ"].astype(int).astype(str)

    resultado = df_upz_localidad.merge(por_upz, on="UPZ", how="left")
    resultado = resultado.merge(por_localidad, on="codigo_localidad", how="left")

    faltantes = resultado["pct_separa_upz"].isna()
    resultado.loc[faltantes, "pct_separa_upz"] = resultado.loc[faltantes, "pct_separa_localidad"]
    resultado.loc[faltantes, "pct_calidad_separacion_upz"] = resultado.loc[faltantes, "pct_calidad_separacion_localidad"]
    resultado.loc[faltantes, "es_fallback_localidad"] = True
    resultado["n_hogares"] = resultado["n_hogares"].fillna(0).astype(int)

    resultado = resultado[[
        "UPZ", "codigo_localidad", "pct_separa_upz", "pct_calidad_separacion_upz",
        "n_hogares", "es_fallback_localidad",
    ]]
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    resultado.to_csv(RUTA_SEPARACION_UPZ_EM2021, index=False)
    return resultado


def factor_incentivo_upz(pct_e1, pct_e2, pct_e3, pct_e4, pct_e5, pct_e6) -> float:
    """Factor de subsidio(-)/contribución(+) ponderado por composición de estrato de una UPZ —
    mismo cálculo ya usado en la Sección 5 del EDA (`EDA_Dirigido_Fase3.ipynb`)."""
    pesos = [pct_e1, pct_e2, pct_e3, pct_e4, pct_e5, pct_e6]
    return sum(
        (p or 0.0) / 100.0 * FACTOR_SUBSIDIO_POR_ESTRATO[estrato]
        for estrato, p in zip(range(1, 7), pesos)
    )
