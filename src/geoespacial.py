"""Operaciones geoespaciales: verificación de CRS y joins espaciales.

Corrige de raíz el bug de la celda 51 del notebook original: allí se calculaba
`df_spatial_join_result` (una variable nueva, nunca usada) mientras el diagnóstico seguía
leyendo `df_join`, una variable global que en otras versiones del notebook terminaba
sobreescrita por resultados de agregación. Aquí el resultado del join es un único
GeoDataFrame inmutable que se pasa explícitamente como parámetro a cada función que lo
necesita — nunca se recalcula ni se depende de una variable global.
"""
import geopandas as gpd
import pandas as pd

from . import config


def verificar_y_reproyectar_crs(gdf: gpd.GeoDataFrame, crs_destino: str = config.CRS_PROYECTO) -> gpd.GeoDataFrame:
    """Reproyecta a `crs_destino` si hace falta y calcula área en m2/ha."""
    gdf = gdf.copy()
    epsg_actual = gdf.crs.to_epsg() if gdf.crs is not None else None
    epsg_destino = int(crs_destino.split(":")[1])
    if epsg_actual != epsg_destino:
        gdf = gdf.to_crs(crs_destino)
    gdf["area_m2"] = gdf.area
    gdf["area_ha"] = gdf.area / 10_000
    return gdf


def validar_area_total(gdf: gpd.GeoDataFrame, ha_min: float = config.AREA_HA_MIN_ESPERADA, ha_max: float = config.AREA_HA_MAX_ESPERADA) -> float:
    """Verifica que el área total esté en el rango esperado para Bogotá. Lanza AssertionError si no."""
    total_ha = gdf["area_ha"].sum()
    assert ha_min <= total_ha <= ha_max, (
        f"Área total fuera de rango esperado ({ha_min:,}-{ha_max:,} ha): {total_ha:,.1f} ha. "
        "Revisar CRS de origen antes de continuar."
    )
    return total_ha


def join_manzanas_upz(df_manzanas: gpd.GeoDataFrame, df_upz: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Join espacial manzana→UPZ por centroide (predicate='intersects').

    Devuelve UN solo GeoDataFrame inmutable con la geometría original de manzana restaurada
    (no el centroide usado para el join). Este es el único resultado del join en todo el
    pipeline — no se recalcula en ningún otro punto.
    """
    df_upz = df_upz.to_crs(df_manzanas.crs)

    df_centroides = df_manzanas.copy()
    df_centroides["geometry"] = df_centroides.geometry.centroid

    resultado = gpd.sjoin(df_centroides, df_upz, how="left", predicate="intersects")
    resultado["geometry"] = df_manzanas.geometry.values
    resultado = gpd.GeoDataFrame(resultado, geometry="geometry", crs=df_manzanas.crs)
    return resultado


def diagnosticar_manzanas_sin_upz(gdf_manzana_upz: gpd.GeoDataFrame, area_total_manzanas_ha: float) -> pd.DataFrame:
    """Diagnostica manzanas que quedaron sin UPZ asignada tras el join.

    Recibe el resultado del join como parámetro explícito (nunca lee una variable global),
    lo que corrige el bug original donde el diagnóstico podía quedar leyendo un `df_join`
    obsoleto si en algún punto posterior del notebook esa variable se reasignaba.
    """
    sin_upz = gdf_manzana_upz[gdf_manzana_upz["CODIGO_UPZ"].isna()].copy()
    area_excluida_ha = sin_upz["area_ha"].sum()
    pct_area_excluida = area_excluida_ha / area_total_manzanas_ha * 100 if area_total_manzanas_ha else float("nan")

    resumen = {
        "total_manzanas_sin_upz": len(sin_upz),
        "area_excluida_ha": area_excluida_ha,
        "pct_area_excluida": pct_area_excluida,
        "distribucion_estrato": sin_upz["ESTRATO"].value_counts().sort_index().to_dict(),
    }

    manzanas_excluidas = sin_upz[["CODIGO_MANZANA", "ESTRATO", "area_ha"]].copy()
    manzanas_excluidas["razon_exclusion"] = "Sin UPZ en join centroide"
    return resumen, manzanas_excluidas


def join_puntos_a_upz(gdf_puntos: gpd.GeoDataFrame, df_upz: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Join espacial genérico punto→UPZ (usado para grandes generadores, puntos limpios, etc.).

    Misma lógica de `predicate='intersects'` que `join_manzanas_upz`, generalizada para
    cualquier capa de puntos con geometría ya construida (ver `carga_datos.puntos_desde_lonlat`).
    """
    df_upz_reproy = df_upz.to_crs(gdf_puntos.crs)
    return gpd.sjoin(gdf_puntos, df_upz_reproy, how="left", predicate="intersects")
