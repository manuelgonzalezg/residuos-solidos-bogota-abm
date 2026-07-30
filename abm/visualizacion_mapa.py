"""Mapa geoespacial estático del resultado del ABM sobre el mapa real de Bogotá.

No usa `mesa-geo`: el modelo nunca necesitó que sus agentes vivieran en un `GeoSpace`, solo la
salida agregada (`modelo.resumen_por_upz()`) necesita geometría, vía un join posterior con
`IndUPZ.gpkg` — el mismo patrón ya usado en la Fase 1 (`src/eda.py::graficar_mapa_coropletico`).
"""
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src import config as config_datos  # noqa: E402
from src import eda  # noqa: E402


def unir_resumen_upz_con_geometria(resumen_upz: pd.DataFrame) -> gpd.GeoDataFrame:
    """Une el resumen por UPZ del modelo (`ModeloResiduosBogota.resumen_por_upz()`, un
    DataFrame plano indexado por `UPZ`) con los polígonos reales de `IndUPZ.gpkg`."""
    gdf_upz = gpd.read_file(config_datos.ARCHIVOS["upz_limites"])
    gdf_upz["CODIGO_UPZ"] = pd.to_numeric(gdf_upz["CODIGO_UPZ"], errors="coerce")

    gdf_resultado = gdf_upz.merge(resumen_upz, left_on="CODIGO_UPZ", right_on="UPZ", how="inner")
    return gdf_resultado


def graficar_mapa_aprovechamiento(resumen_upz: pd.DataFrame, titulo: str | None = None):
    """Choropleth del % de aprovechamiento acumulado por UPZ sobre el mapa real de Bogotá.

    Reutiliza `src.eda.graficar_mapa_coropletico` — mismo estilo/paleta que los mapas de la
    Fase 1 (EDA), para que todas las figuras del proyecto se vean consistentes.
    """
    gdf = unir_resumen_upz_con_geometria(resumen_upz)
    titulo = titulo or "% de aprovechamiento simulado por UPZ (ABM)"
    return eda.graficar_mapa_coropletico(gdf, "pct_aprovechamiento", titulo)


def graficar_mapa_infraestructura(resumen_upz: pd.DataFrame, titulo: str | None = None):
    """Choropleth del índice de infraestructura REAL por UPZ (puntos críticos SIGAB, ver
    `abm/datos_reales.py` y `Reglas_Negocio_v2_y_Modelado_Agentes.md` §3.1) — ya NO es la fórmula
    sintética de la v1 del MVP (esa función fue eliminada de `agentes_infraestructura.py`)."""
    gdf = unir_resumen_upz_con_geometria(resumen_upz)
    titulo = titulo or "Índice de infraestructura REAL por UPZ (puntos críticos SIGAB, 4 cortes)"
    return eda.graficar_mapa_coropletico(gdf, "infraestructura_index", titulo)
