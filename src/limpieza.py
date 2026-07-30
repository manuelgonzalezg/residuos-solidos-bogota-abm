"""Funciones de limpieza reutilizables.

Reemplazan el slicing posicional frágil del notebook original (`iloc[6]`, `columns[4:70]`,
`iloc[7:791]`) por detección basada en contenido, y corrigen de raíz (no solo documentan)
el bug de la suma de composición de residuos.
"""
import numpy as np
import pandas as pd


def detectar_fila_encabezado(df_raw: pd.DataFrame, columnas_esperadas: list[str], max_filas_busqueda: int = 15) -> int:
    """Busca, en las primeras `max_filas_busqueda` filas de un DataFrame leído con header=None,
    la fila cuyo contenido incluye todas las `columnas_esperadas` (búsqueda por substring,
    insensible a mayúsculas/acentos exactos). Reemplaza el `iloc[6]` hardcodeado del original.
    """
    limite = min(max_filas_busqueda, len(df_raw))
    for i in range(limite):
        fila = [str(v).strip().upper() for v in df_raw.iloc[i].tolist()]
        fila_texto = " | ".join(fila)
        if all(exp.upper() in fila_texto for exp in columnas_esperadas):
            return i
    raise ValueError(
        f"No se encontró fila de encabezado con columnas {columnas_esperadas} "
        f"en las primeras {limite} filas. Revisar si el formato del archivo cambió."
    )


def aplicar_encabezado(df_raw: pd.DataFrame, fila_encabezado: int) -> pd.DataFrame:
    """Asigna la fila detectada como encabezado y descarta las filas anteriores."""
    df = df_raw.copy()
    df.columns = df.iloc[fila_encabezado]
    df = df.iloc[fila_encabezado + 1:].reset_index(drop=True)
    return df


def recortar_filas_validas(df: pd.DataFrame, columna_clave: str) -> pd.DataFrame:
    """Conserva solo las filas donde `columna_clave` es convertible a numérico.

    Reemplaza el corte fijo `iloc[7:791]` del original: en vez de asumir un número exacto
    de filas de datos, se descartan las filas finales (notas al pie, fuentes, etc.) donde la
    columna identificadora no es un número válido.
    """
    numerico = pd.to_numeric(df[columna_clave], errors="coerce")
    return df[numerico.notna()].reset_index(drop=True)


def convertir_numericas(df: pd.DataFrame, columnas_excluir: list[str]) -> tuple[pd.DataFrame, list[str]]:
    """Convierte a numérico todas las columnas que no estén en `columnas_excluir`.

    Reemplaza `df.columns[4:70]` (posicional) por una selección explícita basada en las
    columnas de identificación conocidas, así el código no se rompe si cambia el número de
    columnas del archivo fuente.
    """
    df = df.copy()
    columnas_numericas = [c for c in df.columns if c not in columnas_excluir]
    for col in columnas_numericas:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df[columnas_numericas] = df[columnas_numericas].fillna(0).astype("int64")
    return df, columnas_numericas


def enriquecer_con_localidad(df: pd.DataFrame, df_localidades: pd.DataFrame, on_left: str = "LOC") -> pd.DataFrame:
    return pd.merge(
        df,
        df_localidades[["codigo_localidad", "nombre_localidad"]],
        left_on=on_left,
        right_on="codigo_localidad",
        how="left",
    )


def transformar_hogares_wide_to_long(df_hogares_upz: pd.DataFrame, anio_min: int = 2018, anio_max: int = 2024) -> pd.DataFrame:
    """Convierte la tabla de hogares por UPZ (una columna por año) a formato largo."""
    df = df_hogares_upz.copy()
    if "UPZ" in df.columns and "Código UPZ" in df.columns:
        df = df.drop(columns=["UPZ"])

    columnas_anio = [c for c in df.columns if str(c).replace(".0", "").isdigit()]

    df_largo = df.melt(
        id_vars=["Código UPZ"],
        value_vars=columnas_anio,
        var_name="AÑO",
        value_name="HOGARES",
    )
    df_largo["AÑO"] = df_largo["AÑO"].astype(str).str.replace(".0", "", regex=False).astype(int)
    df_largo["Código UPZ"] = df_largo["Código UPZ"].astype(int)
    df_largo = df_largo.rename(columns={"Código UPZ": "UPZ"})
    return df_largo.query(f"{anio_min} <= AÑO <= {anio_max}")


# --- Composición de residuos: fix real del bug de suma (no solo diagnóstico) -----------------

def limpiar_composicion_residuos(df: pd.DataFrame, columnas_categoria: list[str]) -> pd.DataFrame:
    """Elimina registros sin ninguna categoría reportada y rellena el resto con 0."""
    df = df.copy()
    df = df[~df[columnas_categoria].isna().all(axis=1)].reset_index(drop=True)
    df[columnas_categoria] = df[columnas_categoria].fillna(0)
    return df


def normalizar_filas_composicion(df: pd.DataFrame, columnas_categoria: list[str]) -> pd.DataFrame:
    """Reescala cada registro individual para que sus categorías sumen 1.

    Causa raíz del bug original: los registros crudos no necesariamente suman 1 entre sí
    (algunas categorías no reportadas se rellenan con 0 en vez de redistribuirse), así que el
    promedio simple por columna entre varios registros de un mismo año no preserva la
    propiedad de sumar 1. Al normalizar cada fila ANTES de promediar, el promedio anual de
    filas que ya suman 1 también suma 1 (la suma es lineal), lo que corrige el problema de
    raíz para todos los años, no solo para el año con el error más visible (2023).
    """
    df = df.copy()
    total_fila = df[columnas_categoria].sum(axis=1)
    factor = np.where(total_fila > 0, 1.0 / total_fila, 0.0)
    df[columnas_categoria] = df[columnas_categoria].mul(factor, axis=0)
    return df


def calcular_composicion_anual(df: pd.DataFrame, columnas_categoria: list[str], columna_anio: str = "año") -> pd.DataFrame:
    """Calcula el promedio anual de composición ya normalizado por registro.

    Reemplaza el patrón original (promediar columnas crudas y luego solo *imprimir* el error de
    suma) por una corrección estructural: se normaliza cada registro antes de agregar, así que
    `Error_Total` debería quedar ~0 para todos los años por construcción.
    """
    df_normalizado = normalizar_filas_composicion(df, columnas_categoria)
    anual = df_normalizado.groupby(columna_anio, as_index=False)[columnas_categoria].mean()
    anual["Total"] = anual[columnas_categoria].sum(axis=1)
    anual["Error_Total"] = anual["Total"] - 1
    return anual
