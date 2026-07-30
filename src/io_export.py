"""Escritores de los entregables locales en data/processed/.

El notebook original prometía en su introducción una carpeta `data/` con 9 archivos, pero
nunca llamaba a `to_csv`/`to_pickle` en ninguna de sus 132 celdas de código. Este módulo cierra
ese hueco.
"""
from pathlib import Path

import pandas as pd

from . import config

config.DATA_PROCESSED.mkdir(parents=True, exist_ok=True)


def _ruta(nombre_archivo: str) -> Path:
    return config.DATA_PROCESSED / nombre_archivo


def exportar_poblacion_upz(df: pd.DataFrame) -> Path:
    ruta = _ruta("01_poblacion_upz.csv")
    df.to_csv(ruta, index=False, encoding="utf-8-sig")
    return ruta


def exportar_manzanas_upz(df: pd.DataFrame) -> Path:
    ruta = _ruta("02_manzanas_upz.csv")
    df.drop(columns=["geometry"], errors="ignore").to_csv(ruta, index=False, encoding="utf-8-sig")
    return ruta


def exportar_reglas_negocio(df: pd.DataFrame) -> Path:
    ruta = _ruta("03_reglas_negocio.csv")
    df.to_csv(ruta, index=False, encoding="utf-8-sig")
    return ruta


def exportar_composicion_residuos(df: pd.DataFrame) -> Path:
    ruta = _ruta("04_composicion_residuos.csv")
    df.to_csv(ruta, index=False, encoding="utf-8-sig")
    return ruta


def exportar_actores(df: pd.DataFrame) -> Path:
    ruta = _ruta("05_actores.csv")
    df.to_csv(ruta, index=False, encoding="utf-8-sig")
    return ruta


def exportar_parametros_abm(df: pd.DataFrame) -> Path:
    ruta = _ruta("06_parametros_abm.csv")
    df.to_csv(ruta, index=False, encoding="utf-8-sig")
    return ruta


def exportar_escenarios_placeholder() -> Path:
    """Placeholder: la construcción de escenarios de simulación es parte del ABM, fuera de alcance de esta fase."""
    ruta = _ruta("07_escenarios.csv")
    pd.DataFrame(columns=["escenario", "descripcion", "estado"]).to_csv(ruta, index=False, encoding="utf-8-sig")
    return ruta


def exportar_catalogo_variables(catalogo: pd.DataFrame) -> Path:
    ruta = _ruta("08_catalogo_variables.csv")
    catalogo.to_csv(ruta, index=False, encoding="utf-8-sig")
    return ruta


def exportar_df_modelo(df: pd.DataFrame) -> Path:
    ruta = _ruta("df_modelo.pkl")
    df.to_pickle(ruta)
    df.to_csv(_ruta("df_modelo.csv"), index=False, encoding="utf-8-sig")
    return ruta


def exportar_manzanas_excluidas(df: pd.DataFrame) -> Path:
    ruta = _ruta("manzanas_excluidas_join.csv")
    df.to_csv(ruta, index=False, encoding="utf-8-sig")
    return ruta


# --- Fase 2: activación de loaders locales sin usar (ver "Recoleccion_Datos_Fase2.md") ---------

def exportar_recoleccion_concesionario(df: pd.DataFrame) -> Path:
    ruta = _ruta("12_recoleccion_concesionario.csv")
    df.to_csv(ruta, index=False, encoding="utf-8-sig")
    return ruta


def exportar_puntos_limpios(df: pd.DataFrame) -> Path:
    ruta = _ruta("13_puntos_limpios.csv")
    df.to_csv(ruta, index=False, encoding="utf-8-sig")
    return ruta


def exportar_cantidad_entregada_ases(df: pd.DataFrame) -> Path:
    ruta = _ruta("14_cantidad_entregada_ases.csv")
    df.to_csv(ruta, index=False, encoding="utf-8-sig")
    return ruta


def exportar_rbl_consolidado(df: pd.DataFrame) -> Path:
    ruta = _ruta("15_rbl_consolidado.csv")
    df.to_csv(ruta, index=False, encoding="utf-8-sig")
    return ruta
