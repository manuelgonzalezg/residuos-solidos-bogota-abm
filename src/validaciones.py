"""Chequeos de calidad de datos ausentes en el notebook original: duplicados y outliers."""
import pandas as pd


def reportar_duplicados(df: pd.DataFrame, columnas_llave: list[str], nombre: str = "") -> pd.DataFrame:
    """Cuenta y devuelve los registros duplicados según `columnas_llave`. Imprime un resumen."""
    duplicados = df[df.duplicated(subset=columnas_llave, keep=False)]
    etiqueta = nombre or "DataFrame"
    print(f"[{etiqueta}] duplicados por {columnas_llave}: {len(duplicados)} de {len(df)} registros")
    return duplicados


def detectar_outliers_iqr(df: pd.DataFrame, columna: str, factor: float = 1.5) -> pd.DataFrame:
    """Detecta outliers por rango intercuartílico. No elimina nada: solo reporta para revisión manual."""
    q1 = df[columna].quantile(0.25)
    q3 = df[columna].quantile(0.75)
    iqr = q3 - q1
    limite_inferior = q1 - factor * iqr
    limite_superior = q3 + factor * iqr
    outliers = df[(df[columna] < limite_inferior) | (df[columna] > limite_superior)]
    print(
        f"[{columna}] outliers IQR: {len(outliers)} de {len(df)} registros "
        f"(límites: {limite_inferior:.2f} .. {limite_superior:.2f})"
    )
    return outliers


def verificar_suma_filas(df: pd.DataFrame, columnas: list[str], valor_esperado: float = 100.0, tolerancia: float = 0.5, nombre: str = "") -> None:
    """Verifica que cada fila sume aproximadamente `valor_esperado` (p.ej. distribuciones porcentuales)."""
    suma = df[columnas].sum(axis=1)
    fuera_de_rango = (suma - valor_esperado).abs() > tolerancia
    etiqueta = nombre or "tabla"
    if fuera_de_rango.any():
        print(f"[{etiqueta}] {fuera_de_rango.sum()} filas no suman ~{valor_esperado} (tolerancia {tolerancia})")
    else:
        print(f"[{etiqueta}] OK: todas las filas suman ~{valor_esperado}")
