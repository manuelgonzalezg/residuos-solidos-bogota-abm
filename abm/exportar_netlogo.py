# -*- coding: utf-8 -*-
"""Exporta a CSV planos los datos reales que ya usa `ModeloResiduosBogota` (Mesa/Python), para
que el port a NetLogo (`abm/netlogo/residuos_bogota.nlogo`) los consuma sin reimplementar
ninguna lógica de carga/limpieza -- se reutiliza el modelo real ya construido y validado, no se
recalculan los datos por una segunda vía.

Genera, en abm/netlogo/datos/:
  - netlogo_zonas.csv           (112 UPZ x 7 anios = filas)
  - netlogo_adyacencia_upz.csv  (copia directa de 09_adyacencia_upz.csv)
  - netlogo_operadores_ase.csv  (hasta 5 ASE x 7 anios)

Nota de diseno: instanciar ModeloResiduosBogota crea de hecho los ~75k HogarAgente de cada anio
(con sus 3 sorteos aleatorios) solo para poder leer los atributos ya resueltos de
`modelo.entornos`/`modelo.operadores_ase` -- ese costo es unico y offline (no afecta a NetLogo) y
es deliberado: garantiza que el export usa EXACTAMENTE los mismos numeros que ya usa el modelo
Python (infraestructura con snapshot+fallback, capacidad ASE con fallback `confiable`,
recicladores ya prorrateados por poblacion), sin re-derivar esa logica por una segunda vez.
"""
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd

PROYECTO = Path(r"C:\Users\personal\Projects\Proyectos Manuel\EDA + ABM Residuos Bogota")
sys.path.insert(0, str(PROYECTO))

from src import config as config_datos  # noqa: E402
from src import geoespacial  # noqa: E402
from abm import config_abm, datos_reales, entorno, modelo  # noqa: E402

OUT_DIR = PROYECTO / "abm" / "netlogo" / "datos"
OUT_DIR.mkdir(parents=True, exist_ok=True)

ANIOS = [2018, 2019, 2020, 2021, 2022, 2023, 2024]
METROS_POR_PATCH = 150.0  # ver Plan: nucleo real (ancho~23.7km/alto~41.2km) / 150 ~= 158x275 patches


def calcular_centroides_upz() -> pd.DataFrame:
    """Centroides reales de las 112 UPZ, en metros (EPSG:3116), centrados en su propio promedio
    y escalados a unidades de patch de NetLogo. Reutiliza el mismo loader y la misma funcion de
    reproyeccion ya usados en el resto del proyecto (src.carga_datos / src.geoespacial)."""
    from src import carga_datos
    gdf = carga_datos.cargar_upz_limites()
    gdf["CODIGO_UPZ"] = pd.to_numeric(gdf["CODIGO_UPZ"], errors="coerce")
    gdf = gdf.dropna(subset=["CODIGO_UPZ"]).reset_index(drop=True)
    gdf = geoespacial.verificar_y_reproyectar_crs(gdf, crs_destino=config_datos.CRS_PROYECTO)

    centroides = gdf.geometry.centroid
    df = pd.DataFrame({
        "UPZ": gdf["CODIGO_UPZ"].astype(int),
        "x_m": centroides.x,
        "y_m": centroides.y,
    }).drop_duplicates(subset="UPZ")

    cx, cy = df["x_m"].mean(), df["y_m"].mean()
    df["x_centroide"] = (df["x_m"] - cx) / METROS_POR_PATCH
    df["y_centroide"] = (df["y_m"] - cy) / METROS_POR_PATCH
    return df[["UPZ", "x_centroide", "y_centroide"]]


def exportar_zonas(df_centroides: pd.DataFrame, df_separacion_upz: pd.DataFrame):
    filas = []
    for anio in ANIOS:
        print(f"  Construyendo ModeloResiduosBogota(anio={anio}) para exportar zonas...")
        m = modelo.ModeloResiduosBogota(anio=anio, rng=config_abm.SEMILLA_ALEATORIA)
        for codigo_upz, ent in m.entornos.items():
            fila_sep = df_separacion_upz.loc[codigo_upz] if codigo_upz in df_separacion_upz.index else None
            filas.append({
                "anio": anio,
                "codigo_upz": codigo_upz,
                "codigo_localidad": ent.codigo_localidad,
                "nombre_localidad": ent.nombre_localidad,
                "clasificacion_social": ent.clasificacion_social,
                "x_centroide": 0.0,
                "y_centroide": 0.0,
                "hogares_reales": ent.hogares_reales,
                "poblacion_total": ent.poblacion_total,
                "pct_estrato_bajo": ent.pct_estrato_bajo,
                "pct_estrato_medio": ent.pct_estrato_medio,
                "pct_estrato_alto": ent.pct_estrato_alto,
                "infraestructura_index_real": ent.infraestructura_index,
                "pct_separa_upz_real": fila_sep["pct_separa_upz"] if fila_sep is not None else 0.0,
                "pct_calidad_separacion_upz_real": fila_sep["pct_calidad_separacion_upz"] if fila_sep is not None else 0.0,
                "pct_participacion_comunitaria_localidad": ent.pct_participacion_comunitaria,
                "pct_vivienda_propia_localidad": ent.pct_vivienda_propia_localidad,
                "pct_informal_localidad": ent.pct_informal_localidad,
                "pct_registro_activo_reciclador": ent.pct_registro_activo_reciclador,
                "pct_formalizacion_laboral_reciclador": ent.pct_formalizacion_laboral_reciclador,
                "num_recicladores_asignados": ent.num_recicladores_asignados,
                "factor_incentivo": ent.factor_incentivo,
            })

    df = pd.DataFrame(filas)
    # Union de centroides reales por codigo UPZ (columna "UPZ" en df_centroides)
    df = df.drop(columns=["x_centroide", "y_centroide"]).merge(
        df_centroides.rename(columns={"UPZ": "codigo_upz"}), on="codigo_upz", how="left"
    )
    faltantes = df[df["x_centroide"].isna()]["codigo_upz"].unique()
    if len(faltantes) > 0:
        print(f"  AVISO: {len(faltantes)} UPZ sin centroide real (se fijan en 0,0): {list(faltantes)}")
        df["x_centroide"] = df["x_centroide"].fillna(0.0)
        df["y_centroide"] = df["y_centroide"].fillna(0.0)

    columnas_orden = [
        "anio", "codigo_upz", "codigo_localidad", "nombre_localidad", "clasificacion_social",
        "x_centroide", "y_centroide", "hogares_reales", "poblacion_total",
        "pct_estrato_bajo", "pct_estrato_medio", "pct_estrato_alto",
        "infraestructura_index_real", "pct_separa_upz_real", "pct_calidad_separacion_upz_real",
        "pct_participacion_comunitaria_localidad", "pct_vivienda_propia_localidad", "pct_informal_localidad",
        "pct_registro_activo_reciclador", "pct_formalizacion_laboral_reciclador",
        "num_recicladores_asignados", "factor_incentivo",
    ]
    df = df[columnas_orden]
    ruta = OUT_DIR / "netlogo_zonas.csv"
    df.to_csv(ruta, index=False, encoding="utf-8-sig")
    print(f"  {ruta} -> {len(df)} filas, {df['codigo_upz'].nunique()} UPZ unicas")
    return df


def exportar_operadores():
    filas = []
    for anio in ANIOS:
        print(f"  Construyendo ModeloResiduosBogota(anio={anio}) para exportar operadores ASE...")
        m = modelo.ModeloResiduosBogota(anio=anio, rng=config_abm.SEMILLA_ALEATORIA)
        for op in m.operadores_ase:
            filas.append({"anio": anio, "ase": op.ase_nombre, "capacidad_dia_ton": op.capacidad_dia_ton})
    df = pd.DataFrame(filas)
    ruta = OUT_DIR / "netlogo_operadores_ase.csv"
    df.to_csv(ruta, index=False, encoding="utf-8-sig")
    print(f"  {ruta} -> {len(df)} filas")
    return df


def exportar_adyacencia():
    df = entorno.construir_o_cargar_adyacencia_upz()
    ruta = OUT_DIR / "netlogo_adyacencia_upz.csv"
    df.to_csv(ruta, index=False, encoding="utf-8-sig")
    print(f"  {ruta} -> {len(df)} pares")
    return df


if __name__ == "__main__":
    print("1. Centroides reales de UPZ...")
    df_centroides = calcular_centroides_upz()
    print(f"   {len(df_centroides)} centroides calculados.")

    print("2. Separacion real EM2021 por UPZ (constante entre anios)...")
    df_separacion_upz = datos_reales.construir_o_cargar_separacion_upz_em2021()
    df_separacion_upz["UPZ"] = df_separacion_upz["UPZ"].astype(int)
    df_separacion_upz = df_separacion_upz.set_index("UPZ")

    print("3. Exportando netlogo_zonas.csv (7 anios x ~112 UPZ)...")
    df_zonas = exportar_zonas(df_centroides, df_separacion_upz)

    print("4. Exportando netlogo_operadores_ase.csv...")
    df_operadores = exportar_operadores()

    print("5. Exportando netlogo_adyacencia_upz.csv...")
    df_adyacencia = exportar_adyacencia()

    print("\nListo. Archivos en:", OUT_DIR)
