"""Funciones de carga: una función por fuente de datos, sin lógica de limpieza.

Todas las rutas se resuelven a partir de `config.ARCHIVOS` (que a su vez cuelga de
`config.DRIVE_ROOT`) — un único punto de verdad para la ubicación de los datos en Google
Drive, en vez de las ~15 rutas absolutas de Colab repetidas por celda en el notebook original.
"""
import re
import unicodedata

import geopandas as gpd
import numpy as np
import pandas as pd

from . import config
from . import limpieza


def cargar_poblacion_upz() -> pd.DataFrame:
    crudo = pd.read_excel(config.ARCHIVOS["poblacion_upz"], sheet_name="UPZ Bogota 2018_2024", header=None)
    fila_header = limpieza.detectar_fila_encabezado(crudo, ["LOC", "UPZ"])
    df = limpieza.aplicar_encabezado(crudo, fila_header)
    df = limpieza.recortar_filas_validas(df, "LOC")
    df["LOC"] = pd.to_numeric(df["LOC"], errors="coerce")

    columnas_id = ["LOC", "ÁREA GEOGRÁFICA", "UPZ", "AÑO"]
    columnas_id_presentes = [c for c in columnas_id if c in df.columns]
    df, _ = limpieza.convertir_numericas(df, columnas_excluir=columnas_id_presentes)
    return df


def cargar_localidades() -> pd.DataFrame:
    return pd.read_excel(config.ARCHIVOS["localidades"])


def cargar_manzanas() -> gpd.GeoDataFrame:
    return gpd.read_file(config.ARCHIVOS["manzanas"])


def cargar_upz_limites() -> gpd.GeoDataFrame:
    return gpd.read_file(config.ARCHIVOS["upz_limites"])


def cargar_hogares_upz() -> pd.DataFrame:
    """El archivo tiene una fila señuelo (solo etiquetas, sin años) inmediatamente antes de la
    fila de encabezado real (etiquetas + años 2018..2035) — de ahí el token "2018" en la
    búsqueda, que distingue la fila real de la señuelo.
    """
    crudo = pd.read_excel(config.ARCHIVOS["hogares_upz"], header=None)
    fila_header = limpieza.detectar_fila_encabezado(crudo, ["UPZ", "CÓDIGO", "2018"])
    df = limpieza.aplicar_encabezado(crudo, fila_header)
    df = limpieza.recortar_filas_validas(df, "Código UPZ")
    return df


def cargar_disposicion_dj() -> pd.DataFrame:
    """Serie histórica 2018-2024 de disposición/aprovechamiento en Doña Juana."""
    df = pd.read_excel(config.ARCHIVOS["residuos_dj"])
    df = df.rename(columns={"año": "año"})
    return df


def cargar_caracterizacion_residuos() -> pd.DataFrame:
    return pd.read_excel(config.ARCHIVOS["caracterizacion_residuos"])


def cargar_tipo_residuos_localidad() -> pd.DataFrame:
    return pd.read_excel(config.ARCHIVOS["tipo_residuos_localidad"])


def cargar_recicladores_ruro() -> pd.DataFrame:
    """Registro Único de Recicladores de Oficio (RURO).

    El archivo fuente está separado por `;` y codificado en CP850 (codepage de MS-DOS
    heredado de exportes gubernamentales antiguos), no en UTF-8 — de ahí que una lectura
    ingenua con pandas falle con UnicodeDecodeError.
    """
    df = pd.read_csv(
        config.ARCHIVOS["recicladores_ruro"],
        sep=";",
        encoding="cp850",
        skiprows=2,  # las 2 primeras filas son título y una fila en blanco, no encabezado real
    )
    df.columns = [c.strip() for c in df.columns]
    df = df.dropna(axis=1, how="all")
    # Algunos valores no numéricos dispersos en estas columnas hacen que pandas infiera todo
    # el texto como dtype "str" en vez de numérico; se fuerza la conversión explícitamente
    # (los no convertibles quedan como NaN) para que agregaciones como .mean() funcionen.
    columnas_numero_edad = df.columns[[0, 3]]  # "Nº " y "EDAD", por posición (nombres con acentos/símbolos variables)
    for col in columnas_numero_edad:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    # "NIVEL EDUCATIVO" y "QUE MEDIO DE RECOLECCION UTILIZA" traían la misma categoría repetida
    # varias veces por espacios/mayúsculas inconsistentes (ej. "PRIMARIA" contada por separado
    # 3 veces) — confirmado que strip+mayúsculas colapsa correctamente todas las variantes sin
    # perder ninguna categoría real (verificado contra el diccionario de valores del archivo).
    columnas_categoricas_texto = ["NIVEL EDUCATIVO", "QUE MEDIO DE RECOLECCION UTILIZA"]
    for col in columnas_categoricas_texto:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper()
    return df


def cargar_grandes_generadores() -> pd.DataFrame:
    return pd.read_csv(config.ARCHIVOS["grandes_generadores"])


def cargar_superservicios_residuos() -> pd.DataFrame:
    df = pd.read_csv(config.ARCHIVOS["superservicios"])
    columna_municipio = "MUNICIPIO_ÁREA_DE_PRESTACIÓN"
    return df[df[columna_municipio].str.contains("BOGOT", case=False, na=False)].copy()


def cargar_recoleccion_concesionario() -> pd.DataFrame:
    return pd.read_csv(config.ARCHIVOS["recoleccion_concesionario"])


def cargar_puntos_limpios() -> pd.DataFrame:
    return pd.read_excel(config.ARCHIVOS["puntos_limpios"], sheet_name="2020")


def cargar_cantidad_entregada_ases() -> pd.DataFrame:
    return pd.read_excel(config.ARCHIVOS["cantidad_entregada_ases"])


# --- Fuentes externas de Fase 2 (loaders para el EDA dirigido, Fase 3) -------------------------

def cargar_ruro_oficial_2012_2021() -> dict[str, pd.DataFrame]:
    """RURO oficial (Datos Abiertos Bogotá), un archivo con varias mini-tablas en una sola hoja
    (no es una tabla rectangular) — se extrae cada bloque por su rango de filas/columnas real,
    verificado leyendo el archivo (ver "Recoleccion_Datos_Fase2.md" §3.3). Devuelve un dict de
    DataFrames pequeños, uno por bloque.
    """
    ruta = config.ARCHIVOS_FASE2["ruro_oficial_2012_2021"]

    def _bloque(usecols, skiprows, nrows, columnas):
        df = pd.read_excel(ruta, sheet_name="Hoja1", header=None, usecols=usecols,
                            skiprows=skiprows, nrows=nrows)
        df.columns = columnas
        return df.dropna(how="all").reset_index(drop=True)

    return {
        "serie_anual": _bloque("A:B", 5, 10, ["anio", "n_recicladores"]),
        "estado": _bloque("A:B", 36, 2, ["estado", "cantidad"]),
        "causas_retiro": _bloque("A:B", 19, 11, ["causa", "cantidad"]),
        "discapacidad": _bloque("D:E", 19, 10, ["tipo", "cantidad"]),
        "cantidad_por_localidad": _bloque("D:E", 36, 22, ["localidad", "cantidad"]),
        "departamento_nacimiento": _bloque("A:B", 66, 34, ["departamento", "cantidad"]),
        "nivel_salud": _bloque("D:E", 66, 4, ["tipo_afiliacion", "cantidad"]),
        "tipo_vivienda": _bloque("D:E", 74, 10, ["tipo_vivienda", "cantidad"]),
    }


def cargar_ruro_2022_por_localidad() -> pd.DataFrame:
    """RURO 2022 (Datos Abiertos Bogotá), 18 archivos — uno por localidad — cada uno con filas
    ya agrupadas por combinación de Estado/medio de recolección/vivienda/salud/etc. Se
    consolidan en un único DataFrame largo con la localidad como columna.
    """
    carpeta = config.ARCHIVOS_FASE2["ruro_oficial_2022_por_localidad"]
    partes = []
    for archivo in sorted(carpeta.glob("*.xlsx")):
        df = pd.read_excel(archivo, sheet_name="Hoja1")
        df.columns = [str(c).strip() for c in df.columns]
        partes.append(df)
    return pd.concat(partes, ignore_index=True)


def cargar_sigab_snapshot(nombre_snapshot: str) -> dict[str, pd.DataFrame]:
    """Un snapshot de SIGAB ya extraído (ver `config.ARCHIVOS_FASE2`, claves `sigab_*`).

    `nombre_snapshot` es una de las claves `sigab_2020` / `sigab_2022_diciembre` /
    `sigab_2024_diciembre` / `sigab_2026_junio`. Los nombres de archivo dentro de cada carpeta
    varían de mayúsculas/prefijo entre snapshots (ver Recoleccion_Datos_Fase2.md §3.1) — se
    identifican por palabra clave, no por nombre exacto. Los archivos vacíos (1 byte, hallazgo
    de calidad ya documentado) se omiten silenciosamente en vez de fallar.
    """
    carpeta = config.ARCHIVOS_FASE2[nombre_snapshot]
    claves = {
        "puntoscriticos": "puntos_criticos", "ptoscriticos": "puntos_criticos",
        "contenedores": "contenedores",
        "grandesgeneradores": "grandes_generadores", "grandes-generadores": "grandes_generadores",
        "pqrsxlocalidad": "pqrs_por_localidad",
        "pqrsxestrato": "pqrs_por_estrato",
        "pqrsxconcesionario": "pqrs_por_concesionario",
    }
    resultado = {}
    for archivo in carpeta.glob("*.csv"):
        if archivo.stat().st_size <= 1:  # archivos vacíos confirmados en la fuente oficial
            continue
        nombre_normalizado = _rbl_normalizar_texto(archivo.stem).replace(" ", "").replace("_", "")
        for clave_archivo, clave_destino in claves.items():
            if clave_archivo.replace("_", "").replace("-", "") in nombre_normalizado:
                # Todos los CSV de SIGAB están delimitados por "|", no por ",".
                try:
                    resultado[clave_destino] = pd.read_csv(archivo, sep="|", encoding="latin-1")
                except Exception as exc:
                    print(f"Advertencia: no se pudo leer {archivo.name} ({exc}), se omite.")
                break
    return resultado


def cargar_macrorutas(tipo: str = "recoleccion") -> gpd.GeoDataFrame:
    """Macrorutas de recolección o de barrido (UAESP, Datos Abiertos Bogotá), GeoJSON real con
    horario/frecuencia por zona operativa — `tipo` es "recoleccion" o "barrido"."""
    clave = f"macrorutas_{tipo}"
    return gpd.read_file(config.ARCHIVOS_FASE2[clave])


def cargar_diccionario_eca2021() -> dict[str, dict]:
    """Diccionario de códigos de la ECA 2021 (hoja `DICCIONARIO`): el microdato crudo
    (`cargar_eca2021_microdatos`) trae las respuestas como códigos numéricos (1, 2, 99...), no
    como texto — sin este diccionario, cualquier gráfico de esas respuestas mostraría números
    sin significado. Devuelve `{texto_de_la_pregunta: {codigo: etiqueta}}`.
    """
    ruta = config.ARCHIVOS["cultura_ambiental_crudo"]
    crudo = pd.read_excel(ruta, sheet_name="DICCIONARIO", header=None)
    fila_header = limpieza.detectar_fila_encabezado(crudo, ["Variable", "Código"], max_filas_busqueda=20)
    df = crudo.iloc[fila_header + 1:].reset_index(drop=True)
    df.columns = crudo.iloc[fila_header]
    df["Atributo (pregunta)"] = df["Atributo (pregunta)"].ffill()

    diccionario = {}
    for pregunta, grupo in df.groupby("Atributo (pregunta)"):
        codigos = grupo.dropna(subset=["Código"])
        if codigos.empty:
            continue
        diccionario[pregunta] = {
            int(fila["Código"]): fila["Etiqueta de código"] for _, fila in codigos.iterrows()
        }
    return diccionario


def cargar_eca2021_microdatos() -> pd.DataFrame:
    """Encuesta de Cultura Ambiental 2021, microdato crudo por encuesta individual (hoja `NUM`),
    en vez del agregado de 20 filas por localidad ya usado en la Fase 1. Las 2 primeras filas
    son basura de encabezado mal alineado (ver "Recoleccion_Datos_Fase2.md" §A auditoría) —
    se detecta la fila de encabezado real por contenido en vez de asumir la fila 0.
    """
    ruta = config.ARCHIVOS["cultura_ambiental_crudo"]
    crudo = pd.read_excel(ruta, sheet_name="NUM", header=None)
    fila_header = limpieza.detectar_fila_encabezado(crudo, ["LOCALIDAD"], max_filas_busqueda=5)
    df = limpieza.aplicar_encabezado(crudo, fila_header)
    df = df[pd.to_numeric(df.iloc[:, 0], errors="coerce").notna()].reset_index(drop=True)
    return df


# --- Consolidación de la carpeta RBL (Recolección, Barrido y Limpieza), Fase 2 -----------------
#
# La carpeta fuente tiene 97 archivos (2017-2026) con encabezados, nombres de columna y formatos
# numéricos inconsistentes entre eras — ver hallazgos en "Recoleccion_Datos_Fase2.md". Estas
# constantes documentan, en el propio código, las decisiones tomadas para consolidar la serie.

_MESES_ES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6, "junio-": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12, "dic.": 12,
}

# Duplicados/versiones parciales de 2018 confirmados leyendo los archivos (ver
# "Recoleccion_Datos_Fase2.md"): se excluye la versión no autoritativa de cada mes repetido, y
# "data-set-rbl_nuevo_esquema_aseo.csv" (resultó ser un corte parcial del 12-28 de febrero 2018,
# no una tabla de equivalencia zona→ASE ni un mes completo).
_RBL_ARCHIVOS_EXCLUIDOS = {
    "data_set_rbl_marzo_2018(1).csv",
    "marzo-2018-rbl-residuos.csv",
    "febrero-2018-rbl-residuos.csv",
    "agosto-2018-rbl-residuos.csv",
    "data-set-rbl_nuevo_esquema_aseo.csv",
}

# (palabras clave que deben aparecer en el nombre de columna normalizado) -> nombre destino.
# Coincidencia por substring, no exacta: los nombres reales varían en tildes/espacios/unidad
# ("toneladas/mes" vs "t/mes") entre los ~97 archivos.
_RBL_MAPA_COLUMNAS = [
    (("domiciliario",), "domiciliario"),
    (("barrido",), "barrido"),
    (("cesped",), "corte_cesped"),
    (("grandes generadores",), "grandes_generadores"),
    (("mixtos",), "mixtos_ordinarios_escombros"),
    (("poda",), "poda_arboles"),
    (("plazas",), "plazas_mercado"),
    (("voluminosos",), "voluminosos"),
    (("total",), "total_toneladas"),
    (("ase", "concesionario", "operador"), "operador"),  # "operador" cubre "Operador y Zona" (2017)
]


def _rbl_normalizar_texto(texto) -> str:
    texto = str(texto).strip().lower()
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")


def _rbl_detectar_mes(nombre_archivo: str) -> int | None:
    nombre = _rbl_normalizar_texto(nombre_archivo)
    for mes_texto, numero in _MESES_ES.items():
        if _rbl_normalizar_texto(mes_texto) in nombre:
            return numero
    return None


def _rbl_detectar_fila_encabezado(crudo: pd.DataFrame) -> int:
    """Prueba varios tokens posibles (el nombre de la columna de operador cambia de era en era:
    "ASE y Concesionario"/"Área de Servicio Exclusivo y Concesionario" en 2018+, "Operador y
    Zona" en 2017) y usa el primero que aparezca en las primeras filas. Si ninguno aparece, asume
    que la fila 0 ya es el encabezado real.

    Deliberadamente NO se usa "ASE" como token: es substring de los valores de datos de cada fila
    ("ASE 1 Promoambiental"), así que buscarlo encuentra la primera fila de DATOS, no el
    encabezado real, en archivos donde el encabezado dice "Concesionario"/"Operador" en vez de
    "ASE" literal (confirmado con `data-set-abril.xlsx` de 2021, que sin este cuidado detectaba
    la fila 1 como encabezado en vez de la fila 0 real).
    """
    for token in ("CONCESIONARIO", "OPERADOR"):
        try:
            return limpieza.detectar_fila_encabezado(crudo, [token], max_filas_busqueda=5)
        except ValueError:
            continue
    return 0


def _rbl_mapear_columna(nombre_columna) -> str | None:
    normalizado = _rbl_normalizar_texto(nombre_columna)
    for claves, destino in _RBL_MAPA_COLUMNAS:
        if any(clave in normalizado for clave in claves):
            return destino
    return None


# Nombre canónico por número de ASE (2018+). Se canonicaliza por el NÚMERO ("ASE 4", "ASE 5"...)
# y no por palabra clave del nombre del concesionario: varios archivos de la carpeta RBL están
# codificados de forma inconsistente (algunos latin-1 reales, otros en realidad UTF-8 leídos
# como latin-1), lo que corrompe irrecuperablemente letras acentuadas como "Á" en "BOGOTÁ
# LIMPIA"/"ÁREA LIMPIA" — confirmado comparando archivos de la misma ASE con distinto resultado
# de decodificación. El número de ASE no se corrompe por encoding, así que es la clave robusta.
_RBL_ASE_POR_NUMERO = {
    "1": "ASE 1 Promoambiental",
    "2": "ASE 2 LIME",
    "3": "ASE 3 Ciudad Limpia",
    "4": "ASE 4 Bogotá Limpia",
    "5": "ASE 5 Área Limpia",
}

# Valores que aparecieron en la columna de operador por error de detección de encabezado en
# algún archivo puntual (ej. una fila de unidades leída como si fuera una fila de datos) — se
# descartan explícitamente en vez de tratarse como un operador real.
_RBL_OPERADOR_VALORES_INVALIDOS = {"t/mes", "toneladas/mes", "ton/mes"}


def _rbl_normalizar_operador(operador: str) -> str:
    normalizado = _rbl_normalizar_texto(operador)
    match_ase = re.search(r"\base\s*(\d)\b", normalizado)
    if match_ase and match_ase.group(1) in _RBL_ASE_POR_NUMERO:
        return _RBL_ASE_POR_NUMERO[match_ase.group(1)]
    if "rpc" in normalizado or "aguas de bogot" in normalizado:
        return "RPC Aguas de Bogotá"
    # Esquema de zonas de 2017 (sin ASE equivalente documentado en la carpeta fuente): se limpia
    # solo espacios/mayúsculas, sin forzar una canonicalización a un nombre de ASE que no le
    # corresponde — ver nota sobre la serie no comparable 2017 en `cargar_rbl_consolidado`.
    return " ".join(operador.split()).strip().title()


def _rbl_parsear_numero(valor):
    """Convierte un valor de celda a float.

    Los archivos XLSX (2021+) ya entregan `float`/`int` nativos de Excel — pasan directo. Los
    CSV (2017-2020, siempre) entregan texto en formato europeo/colombiano: "." separador de
    miles, "," separador decimal (ej. "22.132,99"). **No se debe intentar `float(texto)` directo
    primero**: para un valor como "34.659" (sin coma) eso da 34.659 en vez de 34659 — un error de
    magnitud ~1000x que pasó silenciosamente hasta que se comparó contra el orden de magnitud
    esperado (miles de toneladas/mes, no decenas). Como los dos formatos coinciden exactamente
    con "es CSV" vs. "es XLSX" en esta carpeta (confirmado archivo por archivo), cualquier texto
    siempre se trata como europeo — nunca se prueba el formato nativo sobre un string.
    """
    if pd.isna(valor):
        return np.nan
    if isinstance(valor, (int, float)):
        return float(valor)
    texto = str(valor).strip()
    if texto in ("", "-"):
        return np.nan
    try:
        return float(texto.replace(".", "").replace(",", "."))
    except ValueError:
        return np.nan


def cargar_rbl_consolidado() -> pd.DataFrame:
    """Consolida la carpeta RBL (Recolección, Barrido y Limpieza, 2017-2026): serie mensual de
    toneladas recolectadas por operador/ASE, agregada a nivel ciudad — no tiene desagregación
    geográfica (ver "Recoleccion_Datos_Fase2.md" para el detalle de la auditoría).

    2017 usa un esquema de 6 "zonas" (operadores distintos a los 5 ASE de 2018 en adelante) y no
    existe, en la carpeta fuente, ningún archivo de equivalencia zona→ASE — se conserva con
    `esquema="zonas_2017"` para que la serie comparable (`esquema="ase_2018+"`) se pueda filtrar
    sin perder el dato de 2017 por completo.
    """
    carpeta = config.ARCHIVOS["rbl_carpeta"]
    filas = []

    for anio_dir in sorted(carpeta.iterdir()):
        if not anio_dir.is_dir():
            continue
        try:
            anio = int(anio_dir.name)
        except ValueError:
            continue

        for archivo in sorted(anio_dir.iterdir()):
            nombre = archivo.name
            if nombre.lower() == "desktop.ini":
                continue
            if "meta" in nombre.lower():
                continue
            if nombre in _RBL_ARCHIVOS_EXCLUIDOS:
                continue
            if archivo.suffix.lower() not in (".csv", ".xlsx"):
                continue

            mes = _rbl_detectar_mes(nombre)

            try:
                if archivo.suffix.lower() == ".csv":
                    try:
                        crudo = pd.read_csv(archivo, header=None, encoding="latin-1", sep=None, engine="python")
                        columnas_insuficientes = crudo.shape[1] < 4
                    except Exception:
                        # El sniffer de separador falla por completo en varios CSV de 2020 —
                        # confirmado con marzo/febrero-2020: los números usan coma decimal
                        # ("34.212,97"), lo que hace que el sniffer detecte "," como delimitador
                        # y produzca conteos de columnas inconsistentes fila a fila (ParserError),
                        # no solo una lectura angosta silenciosa. Se retiene el error solo para
                        # decidir el reintento; no se descarta el archivo todavía.
                        crudo = None
                        columnas_insuficientes = True
                    if columnas_insuficientes:
                        # El sniffer de separador elige mal el delimitador en varios CSV de
                        # 2020 (confirmado con enero-2020-rbl-residuos.csv: el archivo es
                        # ";"-delimitado pero el sniffer detecta "," y produce una sola columna
                        # ilegible) — se reintenta con ";" explícito antes de descartar el archivo.
                        crudo = pd.read_csv(archivo, header=None, encoding="latin-1", sep=";")
                else:
                    crudo = pd.read_excel(archivo, header=None)
            except Exception as exc:
                print(f"Advertencia: no se pudo leer {nombre} ({exc}), se omite del consolidado RBL.")
                continue

            fila_header = _rbl_detectar_fila_encabezado(crudo)
            df = limpieza.aplicar_encabezado(crudo, fila_header)

            mapa_columnas = {}
            for col in df.columns:
                destino = _rbl_mapear_columna(col)
                if destino and destino not in mapa_columnas:
                    mapa_columnas[destino] = col

            if "operador" not in mapa_columnas:
                print(f"Advertencia: no se encontró columna de operador en {nombre}, se omite del consolidado RBL.")
                continue

            columnas_tipo = [c for c in mapa_columnas if c not in ("operador", "total_toneladas")]

            for _, fila in df.iterrows():
                operador = str(fila[mapa_columnas["operador"]]).strip()
                if (
                    not operador
                    or operador.lower() in ("nan", "none")
                    or "total" in operador.lower()
                    or operador.lower() in _RBL_OPERADOR_VALORES_INVALIDOS
                ):
                    continue
                operador = _rbl_normalizar_operador(operador)
                # El esquema se determina por el NOMBRE canonicalizado, no por el año: se
                # confirmó (probando contra los datos reales) que varios archivos de 2018 y
                # 2019 siguen usando la nomenclatura antigua de "zonas" en vez de "ASE" — la
                # transición real fue gradual, no un corte limpio el 1 de enero de 2018 como se
                # asumió en el diseño inicial.
                esquema = "ase_2018+" if (operador.startswith("ASE ") or operador == "RPC Aguas de Bogotá") else "zonas_2017"
                for tipo in columnas_tipo:
                    toneladas = _rbl_parsear_numero(fila[mapa_columnas[tipo]])
                    if pd.isna(toneladas):
                        continue
                    filas.append({
                        "anio": anio,
                        "mes": mes,
                        "esquema": esquema,
                        "operador": operador,
                        "tipo_residuo": tipo,
                        "toneladas": toneladas,
                        "archivo_origen": nombre,
                    })

    return pd.DataFrame(filas)


def cargar_cultura_ambiental() -> pd.DataFrame:
    """Encuesta de Cultura Ambiental 2021, ya agregada por localidad.

    Cierra el hueco que el notebook original dejaba marcado como "Pendiente modelar".
    """
    return pd.read_csv(config.ARCHIVOS["cultura_ambiental_localidad"])


def puntos_desde_lonlat(df: pd.DataFrame, col_lon: str, col_lat: str, crs: str = "EPSG:4326") -> gpd.GeoDataFrame:
    """Convierte un DataFrame con columnas de longitud/latitud en texto (coma decimal) a GeoDataFrame."""
    df = df.copy()
    lon = pd.to_numeric(df[col_lon].astype(str).str.replace(",", "."), errors="coerce")
    lat = pd.to_numeric(df[col_lat].astype(str).str.replace(",", "."), errors="coerce")
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(lon, lat), crs=crs)
    return gdf[gdf.geometry.notna() & gdf.geometry.is_valid]


COLUMNAS_MULTIPROPOSITO = [
    "DIRECTORIO", "DIRECTORIO_HOG", "MPIO", "COD_LOCALIDAD", "NOMBRE_LOCALIDAD", "FEX_C", "NVCBP11AA",
    "NHCCP38", "NHCCP38AA", "NHCCP38AB", "NHCCP38AC", "NHCCP38AD", "NHCCP38AF", "NHCCP38AG",
    "NHCCP38B", "NHCDP5", "NHCDP6",
    # --- Ampliación Fase 2: columnas nombradas en el `select()` original de PySpark (antes del
    # refactor a pandas de la Fase 1) y dejadas fuera al construir esta lista por primera vez —
    # ver "Analisis_Variables_Negocio.md" §4 (regresión de alcance) y "Recoleccion_Datos_Fase2.md".
    "NPCJP1F", "NPCJP1I",          # participación comunitaria (organización ambiental, JAC)
    "NPCKP23", "NPCKP17", "OINFORMAL", "NPCKP44A",  # ingresos laborales / informalidad
    "NHCLP9C", "NHCLP9E", "NHCLP9F", "NHCLP10", "NHCLP11",  # percepción ambiental adicional
    "NPCHP4", "NPCHP1",            # educación
    "NHCCPCTRL2",                  # composición del hogar (número de personas)
    "NVCBP10", "NVCBP4", "NVCBP9", "NHCCP35",  # condiciones habitacionales
    # --- Ampliación Fase 2: columnas confirmadas en el diccionario oficial durante la auditoría
    # de `data/raw/` (Fase 2), no nombradas en el `select()` original — entorno y disposición de
    # basuras alrededor de la vivienda, complementarias a NHCCP38* (qué separa el hogar).
    "NVCBP11D", "NVCBP14B", "NVCBP14I", "NVCBP15F", "NVCBP15K", "NHCCP37",
    # --- Ampliación ronda 5 (2026-07-14): geografía real a nivel UPZ (o grupo de 2-4 UPZ,
    # fusionadas por diseño muestral) — existía en el archivo crudo desde siempre, nunca se había
    # extraído. Verificado contra las 112 UPZ reales: 111 cubiertas directamente, sin conflictos
    # (ver `abm/datos_reales.py::construir_o_cargar_separacion_upz_em2021` y
    # `Justificacion_Metodologica_Comite.md`). Es más fino que `COD_LOCALIDAD`, la única geografía
    # usada hasta ahora para comportamiento.
    "COD_UPZ_GRUPO", "NOMBRE_UPZ_GRUPO",
]

# Naturaleza de cada columna nueva de la Fase 2, verificada contra
# "20230620_diccionario_variables_encuesta_em2021.xlsx" — documentado aquí para que cualquier
# limpieza/recodificación futura no tenga que releer el diccionario ni adivinar el tipo. Esto es
# solo información de tipo/dominio, no una decisión de qué variables usar en el modelo (esa
# decisión sigue pendiente, fuera de alcance de esta fase).
NATURALEZA_COLUMNAS_MULTIPROPOSITO_FASE2 = {
    # Numéricas (valor real, no código categórico)
    "NPCKP23": "numérica — ingreso mensual laboral antes de descuentos, en pesos",
    "NHCCPCTRL2": "numérica — número de personas del hogar",
    # Categóricas binarias Sí/No (1=Sí, 2=No)
    "NVCBP4": "categórica 1/2 (Sí/No) — vivienda en conjunto residencial",
    "NVCBP9": "categórica 1/2 (Sí/No) — espacio de negocio en la vivienda",
    "NHCLP11": "categórica 1/2 (Sí/No) — se considera pobre",
    "NPCHP1": "categórica 1/2 (Sí/No) — sabe leer y escribir",
    "NVCBP11D": "categórica 1/2 (Sí/No) — servicio público/privado de recolección de basuras",
    "NVCBP14B": "categórica 1/2 (Sí/No) — vivienda cerca de basureros/botaderos",
    "NVCBP14I": "categórica 1/2 (Sí/No) — vivienda cerca de caños de aguas residuales",
    "NVCBP15F": "categórica 1/2 (Sí/No) — entorno con disposición inadecuada de basuras",
    "NVCBP15K": "categórica 1/2 (Sí/No) — entorno con disposición inadecuada de residuos hospitalarios",
    "NPCJP1F": "categórica 1/2 (Sí/No) — pertenece a organización ambientalista",
    "NPCJP1I": "categórica 1/2 (Sí/No) — pertenece a Junta de Acción Comunal",
    # Categóricas ordinales/multi-opción (ver diccionario para las etiquetas completas de cada código)
    "NHCLP9C": "ordinal 1-3 + 9=No sabe — percepción de cambio en disposición de basuras 2017→hoy",
    "NHCLP9E": "ordinal 1-3 + 9=No sabe — percepción de cambio en barrido/limpieza de calles 2017→hoy",
    "NHCLP9F": "ordinal 1-3 + 9=No sabe — percepción de cambio en reciclaje de residuos 2017→hoy",
    "NHCLP10": "ordinal 1-3 — suficiencia de ingresos del hogar frente a gastos",
    "NPCHP4": "ordinal 1-11 — nivel educativo más alto alcanzado",
    "NPCKP17": "categórica multi-opción — posición ocupacional (obrero, independiente, etc.)",
    "OINFORMAL": "binaria construida por DANE — 1=ocupado informal",
    "NVCBP10": "categórica multi-opción — tipo de vivienda (casa/apartamento/cuarto/otro)",
    "NHCCP35": "categórica multi-opción — disponibilidad de cuarto de baño",
    "NHCCP37": "categórica multi-opción — cómo elimina la basura el hogar (incluye 'la tiran a un río/lote', más grave que 'no separa')",
    "COD_UPZ_GRUPO": "código — UPZ individual (coincide con CODIGO_UPZ real) o grupo de 2-4 UPZ "
                      "fusionadas (códigos ≥800), ver crosswalk en 26_crosswalk_em2021_upz.csv",
    "NOMBRE_UPZ_GRUPO": "texto — nombre de la UPZ individual, o 'LOCALIDAD: NombreA + NombreB' si es grupo",
    # Advertencia de calidad de fuente, no de tipo de dato
    "NPCKP44A": "presente en em2021.csv y en el `select()` original, pero NO aparece documentada "
                "en el diccionario oficial 20230620 — usar con la reserva de no tener definición "
                "textual verificada; se conserva porque el `select()` original ya la nombraba.",
}


def cargar_multiproposito() -> pd.DataFrame:
    """Encuesta Multipropósito 2021 (em2021.csv).

    El archivo pesa 1.25GB en disco por sus 1553 columnas, pero solo tiene 292,282 filas y
    aquí se necesitan ~16 columnas — se leen con pandas y `usecols` en vez de PySpark. Esto
    evita una dependencia de JVM que resultó frágil en esta máquina (Java 8 instalado, PySpark
    4.x requiere Java 17+) y es más simple para un volumen de filas que pandas maneja sin
    problema.
    """
    # Se usa pyarrow.csv directamente (no pandas.read_csv(engine="pyarrow")): el archivo tiene
    # al menos una fila corrupta con menos columnas de las esperadas (1352 en vez de 1553), lo
    # que hace que el motor C se cuelgue tratando de tokenizarla ("out of memory") y que el
    # wrapper de pandas para pyarrow la rechace de plano. `invalid_row_handler` permite saltar
    # esas filas puntuales sin perder el resto del archivo.
    import pyarrow as pa
    import pyarrow.csv as pv

    filas_invalidas = {"total": 0}

    def _saltar_fila_invalida(row):
        filas_invalidas["total"] += 1
        return "skip"

    tabla = pv.read_csv(
        str(config.ARCHIVOS["em2021"]),
        read_options=pv.ReadOptions(encoding="latin-1"),
        parse_options=pv.ParseOptions(invalid_row_handler=_saltar_fila_invalida),
        convert_options=pv.ConvertOptions(
            include_columns=COLUMNAS_MULTIPROPOSITO,
            column_types={c: pa.string() for c in COLUMNAS_MULTIPROPOSITO},
        ),
    )
    df = tabla.to_pandas()
    if filas_invalidas["total"]:
        print(f"Advertencia: se saltaron {filas_invalidas['total']} filas corruptas de em2021.csv (columnas incompletas).")
    df = df[df["MPIO"] == "11001"]
    df = df[df["NVCBP11AA"].isin(["1", "2", "3", "4", "5", "6"])]
    return df
