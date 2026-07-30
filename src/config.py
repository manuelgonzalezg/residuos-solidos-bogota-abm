"""Configuración central del pipeline: rutas y constantes.

Única fuente de verdad para la ubicación de los datos (en Google Drive) y para los
parámetros que antes estaban repetidos como "números mágicos" en el notebook original.
"""
from pathlib import Path

# --- Ruta base en Google Drive (montado como unidad G:\ por Google Drive para escritorio) ---
DRIVE_PROYECTO = Path(r"G:\Mi unidad\Analitica para la toma de decisiones\Proyecto")
DRIVE_ROOT = DRIVE_PROYECTO / "Variables - Construyendo el Dataset"

DEMOGRAFICAS = DRIVE_ROOT / "Demograficas"
RESIDUOS = DRIVE_ROOT / "Residuos"
CULTURA = DRIVE_ROOT / "Cultura"
SALIDAS_DRIVE = DRIVE_ROOT / "Salidas"
OTROS = DRIVE_PROYECTO / "Otros"

# --- Rutas de archivos fuente (todas relativas a las carpetas de arriba) ---
ARCHIVOS = {
    "poblacion_upz": DEMOGRAFICAS / "anexo-proyecciones-poblacion-bogota-desagreacion-loc-2018-2035-UPZ-2018-2024 (1).xlsx",
    "localidades": DEMOGRAFICAS / "Maestra_Localidades_Bogota.xlsx",
    "manzanas": DEMOGRAFICAS / "manzanaestratificacion.gpkg",
    "upz_limites": DEMOGRAFICAS / "IndUPZ.gpkg",
    "hogares_upz": DEMOGRAFICAS / "202503_upz_proyeccion_hogares_viviendas_2018_2035.xlsx",
    "em2021": DEMOGRAFICAS / "em2021.csv",
    "residuos_dj": RESIDUOS / "Residuos generados bogota.xlsx",
    "caracterizacion_residuos": RESIDUOS / "caracterizacion-de-resiudos-solidosvf.xlsx",
    "tipo_residuos_localidad": RESIDUOS / "tipo residuos localidad.xlsx",
    "recicladores_ruro": RESIDUOS / "informacion-ruro-.csv",
    "grandes_generadores": RESIDUOS / "Grandes_Generadores__de_Residuos_-_UAESP_20260702.csv",
    "superservicios": RESIDUOS / "Superservicios_Residuos_Generados_en_el_area_de_Prestación_del_Servicio_20260702 (1).csv",
    "recoleccion_concesionario": RESIDUOS / "03_recoleccion_por_concesionario.csv",
    "rbl_carpeta": RESIDUOS / "datos-residuos-recogidos-rbl-2017-2025 (1)",
    "cultura_ambiental_localidad": CULTURA / "02_variables_comportamiento_localidad.csv",
    "cultura_ambiental_crudo": CULTURA / "2021-04-22-base-datos-abiertos_eca-2021_scrd-1.xlsx",
    "diccionario_em2021": CULTURA / "20230620_diccionario_variables_encuesta_em2021.xlsx",
    "puntos_limpios": OTROS / "dataset-gestion-residuos-punto-limpio-2020.xlsx",
    "cantidad_entregada_ases": OTROS / "cantidad-entregada-por-ases.xlsx",
}

# --- Salidas locales del pipeline (generadas, no fuente) ---
PROYECTO_DIR = Path(__file__).resolve().parent.parent
DATA_PROCESSED = PROYECTO_DIR / "data" / "processed"

# --- Fase 2: fuentes externas descargadas de portales de datos abiertos (no vienen de Drive,
# solo existen localmente) — ver "Recoleccion_Datos_Fase2.md" para procedencia, licencia y fecha
# de descarga de cada una. Ningún `cargar_*()` las usa todavía; quedan como rutas listas para
# cuando se decida integrarlas al pipeline (fuera de alcance de esta fase).
EXTERNO_FASE2 = PROYECTO_DIR / "data" / "raw" / "externo_fase2"

ARCHIVOS_FASE2 = {
    "sigab_2020": EXTERNO_FASE2 / "UAESP_SIGAB" / "extraidos" / "2020",
    "sigab_2022_diciembre": EXTERNO_FASE2 / "UAESP_SIGAB" / "extraidos" / "2022_diciembre",
    "sigab_2024_diciembre": EXTERNO_FASE2 / "UAESP_SIGAB" / "extraidos" / "2024_diciembre",
    "sigab_2026_junio": EXTERNO_FASE2 / "UAESP_SIGAB" / "extraidos" / "2026_junio",
    "macrorutas_recoleccion": EXTERNO_FASE2 / "UAESP_Macrorutas" / "macrorutas_recoleccion.geojson",
    "macrorutas_barrido": EXTERNO_FASE2 / "UAESP_Macrorutas" / "macrorutas_barrido.geojson",
    "ruro_oficial_2012_2021": EXTERNO_FASE2 / "RURO_Generalidades" / "RURO_2012-2021.xlsx",
    "ruro_oficial_2022_por_localidad": EXTERNO_FASE2 / "RURO_Generalidades" / "2022_por_localidad",
    "pgirs_documento_tecnico": EXTERNO_FASE2 / "PGIRS" / "PGIRS_Documento_Tecnico_Soporte.pdf",
    "cra_tarifas_ase3": EXTERNO_FASE2 / "CRA_Tarifas" / "Tarifas_ASE3_202512.pdf",
    "pqrs_idu_2018": EXTERNO_FASE2 / "PQRS" / "consolidado_pqrs_2018.csv",  # descartado, ver nota en el documento de cierre
}

# --- CRS ---
CRS_PROYECTO = "EPSG:3116"  # MAGNA-SIRGAS / Bogotá, usado para cálculos de área
CRS_UPZ_ORIGEN = "EPSG:4686"  # CRS nativo de IndUPZ.gpkg (MAGNA-SIRGAS geográfico)
AREA_HA_MIN_ESPERADA = 25_000
AREA_HA_MAX_ESPERADA = 40_000

# --- Constantes de negocio ---
# Generación per cápita real: `Residuos generados bogota.xlsx` (toneladas/año) ÷ población real de
# la ciudad (`poblacion_upz`, suma de todas las UPZ) — verificado consistente en 0.336-0.368 para
# cada uno de los años 2018-2023 (ver Investigacion_Salto_Aprovechamiento.md); se usa el promedio
# de esos 6 años. Corregido 2026-07-11 (antes 0.28, un valor sin sustento verificable que
# subestimaba la generación real ~20-25%).
RESIDUOS_PER_CAPITA_TON_ANIO = 0.35  # ton/persona/año, promedio real 2018-2023

# --- Estratos socioeconómicos ---
N_ESTRATOS = 7  # 0 a 6
UMBRAL_ESTRATO_BAJO = 2   # estrato <= 2 se considera "bajo"
UMBRAL_ESTRATO_ALTO = 4   # estrato >= 4 se considera "alto"

# --- Ground truth de aprovechamiento ---
# REVISADO — ver Investigacion_Salto_Aprovechamiento.md (2026-07-11). El valor de 48.50%
# (2025) se descartó como objetivo de calibración: es la salida de un modelo econométrico de la
# UAESP (no una medición directa), con un salto de 18.56% (2023) a 43.88% (2024) que coincide con
# una reforma regulatoria confirmada (Decreto 1381 de 2024 — nuevo censo obligatorio anual de
# recicladores, nuevo PGIRS 2024-2028) y con evidencia cuantitativa de que fuentes oficiales
# distintas (UAESP/OAB vs. SUI) difieren en factor ~2x para los mismos años — no es una serie
# comparable en el tiempo. Se usa en cambio **18.56% (2023)**, el último año de la serie
# internamente consistente 2018-2023 (15.38% → 18.56%, tendencia gradual y físicamente
# plausible), como el objetivo real de calibración del comportamiento de separación/aprovechamiento.
APROVECHAMIENTO_GROUND_TRUTH_PCT = 18.56  # 2023, último año pre-quiebre regulatorio de 2024

# --- Localidades sin UPZ urbanas (excluidas de los análisis por UPZ) ---
LOCALIDAD_SUMAPAZ = 20
