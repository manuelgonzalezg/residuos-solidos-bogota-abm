"""Construcción de features por UPZ y variables de entorno del ABM.

Unifica los ~10 `groupby` sueltos del notebook original en dos funciones con nombre, y mueve
los números mágicos (7 estratos, umbrales bajo/alto) a `config.py`.
"""
import numpy as np
import pandas as pd

from . import config


def construir_features_upz(gdf_manzana_upz: pd.DataFrame) -> pd.DataFrame:
    """A partir del resultado del join manzana→UPZ, construye una fila por UPZ con:
    num_manzanas, área (total/promedio/mediana), estrato (promedio/mediana/moda),
    distribución porcentual de estratos, diversidad de estratos y % del estrato dominante.
    """
    g = gdf_manzana_upz.groupby("CODIGO_UPZ")

    num_manzanas = g.size().reset_index(name="num_manzanas")

    area = g.agg(
        area_total_m2=("area_m2", "sum"),
        area_total_ha=("area_ha", "sum"),
        area_promedio_m2=("area_m2", "mean"),
        area_mediana_m2=("area_m2", "median"),
    ).reset_index()

    estrato = g.agg(
        estrato_promedio=("ESTRATO", "mean"),
        estrato_mediano=("ESTRATO", "median"),
    ).reset_index()

    moda = (
        g["ESTRATO"]
        .agg(lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else None)
        .reset_index(name="estrato_predominante")
    )

    tabla_estratos = pd.crosstab(gdf_manzana_upz["CODIGO_UPZ"], gdf_manzana_upz["ESTRATO"])
    tabla_estratos_pct = tabla_estratos.div(tabla_estratos.sum(axis=1), axis=0).multiply(100).reset_index()
    columnas_pct = [f"pct_e{c}" for c in tabla_estratos.columns]
    tabla_estratos_pct.columns = ["CODIGO_UPZ"] + columnas_pct

    columnas_pct_residenciales = [c for c in columnas_pct if c != "pct_e0"]
    estrato_max = (
        tabla_estratos_pct.set_index("CODIGO_UPZ")[columnas_pct_residenciales]
        .max(axis=1)
        .reset_index(name="pct_estrato_dominante")
    )

    diversidad = g["ESTRATO"].nunique().reset_index(name="diversidad_estratos")

    features = (
        num_manzanas
        .merge(area, on="CODIGO_UPZ")
        .merge(estrato, on="CODIGO_UPZ")
        .merge(moda, on="CODIGO_UPZ")
        .merge(tabla_estratos_pct, on="CODIGO_UPZ")
        .merge(diversidad, on="CODIGO_UPZ")
        .merge(estrato_max, on="CODIGO_UPZ")
    )
    return features


def enriquecer_variables_abm(df_modelo: pd.DataFrame) -> pd.DataFrame:
    """Agrega al `df_modelo` las variables derivadas que sirven de entorno estático del ABM."""
    df = df_modelo.copy()

    df["pct_hombres"] = df["Total_Hombres"] / df["Total"] * 100
    df["pct_mujeres"] = df["Total_Mujeres"] / df["Total"] * 100

    df["densidad_poblacional"] = df["Total"] / df["area_total_ha"].replace(0, np.nan)
    df["habitantes_por_manzana"] = df["Total"] / df["num_manzanas"].replace(0, np.nan)

    df["pct_estrato_bajo"] = df["pct_e1"] + df["pct_e2"]
    df["pct_estrato_medio"] = df["pct_e3"]
    df["pct_estrato_alto"] = df["pct_e4"] + df["pct_e5"] + df["pct_e6"]

    df["diversidad_normalizada"] = df["diversidad_estratos"] / config.N_ESTRATOS
    df["estrato_dominante_pct"] = df["pct_estrato_dominante"]

    df["predominio_bajo"] = df["estrato_predominante"] <= config.UMBRAL_ESTRATO_BAJO
    df["predominio_medio"] = df["estrato_predominante"] == 3
    df["predominio_alto"] = df["estrato_predominante"] >= config.UMBRAL_ESTRATO_ALTO

    df["clasificacion_social"] = df["estrato_predominante"].apply(_clasificacion_social)
    df["heterogeneidad_social"] = df["diversidad_estratos"].apply(_heterogeneidad_social)

    df["indice_fragmentacion_social"] = df["diversidad_normalizada"] * (1 - df["estrato_dominante_pct"] / 100)

    return df


def _clasificacion_social(estrato_predominante) -> str:
    if pd.isna(estrato_predominante):
        return "Sin dato"
    if estrato_predominante <= config.UMBRAL_ESTRATO_BAJO:
        return "Baja"
    elif estrato_predominante == 3:
        return "Media"
    return "Alta"


def _heterogeneidad_social(diversidad_estratos) -> str:
    if pd.isna(diversidad_estratos):
        return "Sin dato"
    if diversidad_estratos <= 2:
        return "Baja"
    elif diversidad_estratos <= 4:
        return "Media"
    return "Alta"
