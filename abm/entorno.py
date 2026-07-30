"""Ambiente del ABM: red de vecindad entre UPZ y el objeto de estado por UPZ.

No se usa mesa-geo ni geometría fina de manzanas — no hay red vial ni direcciones reales, así
que un grafo de 112 nodos UPZ es el techo honesto de resolución espacial de los datos
disponibles (ver Diseno_ABM.md §2).
"""
import geopandas as gpd
import networkx as nx
import pandas as pd

from . import config_abm

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src import config as config_datos  # noqa: E402


def construir_o_cargar_adyacencia_upz() -> pd.DataFrame:
    """Devuelve la tabla de vecindad UPZ (`upz_origen`, `upz_vecina`).

    Se construye una sola vez desde `IndUPZ.gpkg` (contigüidad tipo "queen", vía geopandas) y
    se guarda versionada en `data/processed/09_adyacencia_upz.csv` — no se recalcula en cada
    corrida del modelo.
    """
    ruta = config_abm.RUTA_ADYACENCIA_UPZ
    if ruta.exists():
        return pd.read_csv(ruta)

    gdf_upz = gpd.read_file(config_datos.ARCHIVOS["upz_limites"])
    gdf_upz["CODIGO_UPZ"] = pd.to_numeric(gdf_upz["CODIGO_UPZ"], errors="coerce")
    gdf_upz = gdf_upz.dropna(subset=["CODIGO_UPZ"]).reset_index(drop=True)

    sindex = gdf_upz.sindex
    pares = []
    for i, geom in enumerate(gdf_upz.geometry):
        vecinos_posibles = list(sindex.query(geom, predicate="touches"))
        for j in vecinos_posibles:
            if j == i:
                continue
            pares.append((int(gdf_upz.loc[i, "CODIGO_UPZ"]), int(gdf_upz.loc[j, "CODIGO_UPZ"])))

    df_adyacencia = pd.DataFrame(pares, columns=["upz_origen", "upz_vecina"]).drop_duplicates()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    df_adyacencia.to_csv(ruta, index=False)
    return df_adyacencia


def construir_grafo_upz(df_adyacencia: pd.DataFrame, codigos_upz: list[int]) -> nx.Graph:
    """Construye el grafo networkx de UPZ, garantizando que todos los `codigos_upz` sean nodos
    (incluso si quedaron sin vecinos detectados, para que ningún UPZ quede fuera de la red)."""
    grafo = nx.Graph()
    grafo.add_nodes_from(codigos_upz)
    aristas = [
        (int(row.upz_origen), int(row.upz_vecina))
        for row in df_adyacencia.itertuples()
        if row.upz_origen in codigos_upz and row.upz_vecina in codigos_upz
    ]
    grafo.add_edges_from(aristas)
    return grafo


class EntornoUPZ:
    """Estado (no-agente) de una UPZ: atributos anuales del dataset + variables de simulación.

    Los atributos demográficos/estrato vienen de `df_modelo` (Fase 1, reales).
    `infraestructura_index` ahora es REAL (promedio de puntos críticos de SIGAB en 4 cortes de
    tiempo, ver `abm/datos_reales.py`) — ya no la fórmula sintética de la v1 del MVP. También se
    agregan `factor_incentivo` (tarifa CRA real ponderada por estrato) y
    `pct_participacion_comunitaria` (EM2021, localidad) — dos mecanismos nuevos que no existían
    en el MVP original. Ver `Reglas_Negocio_v2_y_Modelado_Agentes.md`.
    """

    def __init__(self, codigo_upz: int, fila_df_modelo: pd.Series):
        self.codigo_upz = codigo_upz
        self.codigo_localidad = fila_df_modelo.get("codigo_localidad")
        self.nombre_localidad = fila_df_modelo.get("nombre_localidad")
        self.estrato_promedio = fila_df_modelo.get("estrato_promedio")
        self.clasificacion_social = fila_df_modelo.get("clasificacion_social")
        self.pct_estrato_bajo = fila_df_modelo.get("pct_estrato_bajo", 0.0)
        self.pct_estrato_medio = fila_df_modelo.get("pct_estrato_medio", 0.0)
        self.pct_estrato_alto = fila_df_modelo.get("pct_estrato_alto", 0.0)
        self.densidad_poblacional = fila_df_modelo.get("densidad_poblacional", 0.0)
        self.indice_socioeconomico = fila_df_modelo.get("indice_socioeconomico", 0.0)
        self.hogares_reales = fila_df_modelo.get("HOGARES", 0.0)
        self.poblacion_total = fila_df_modelo.get("Total", 0.0)
        self.num_recicladores_localidad = fila_df_modelo.get("num_recicladores_ruro", 0.0)

        self.infraestructura_index: float = 0.5  # se fija en modelo.py con datos_reales.py (ya no sintético)
        self.num_recicladores_asignados: float = 0.0  # se asigna proporcional a población (ver modelo.py)

        # --- Mecanismos nuevos (Fase 2/3), fijados en modelo.py al construir el entorno ---
        self.factor_incentivo: float = 0.0             # -0.70 a +0.60, tarifa CRA real por composición de estrato
        self.pct_participacion_comunitaria: float = 0.0  # EM2021, real, a nivel localidad
        self.pct_registro_activo_reciclador: float = 0.0     # RURO 2022, real, a nivel localidad
        self.pct_formalizacion_laboral_reciclador: float = 0.0  # RURO 2022 (ARL), real, a nivel localidad

        # --- Heterogeneidad real de hogar (ronda 4, 2026-07-14), EM2021, real a nivel localidad
        # (ver `datos_reales.construir_o_cargar_perfil_hogar_localidad` y
        # `Justificacion_Metodologica_Comite.md`) — mismos 2 predictores reales, significativos y
        # ya validados en el EDA que hasta ahora no se usaban en el ABM.
        self.pct_vivienda_propia_localidad: float = 0.0  # NVCBP10==1 ("Casa"), proxy de tenencia
        self.pct_informal_localidad: float = 0.0          # OINFORMAL, binaria DANE

        # Variables que se reinician cada paso (día)
        self.material_generado_dia = 0.0
        self.material_pool_disponible = 0.0
        self.material_aprovechado_dia = 0.0
        self.material_rechazo_dia = 0.0

        # Acumuladores para el balance de masa
        self.acumulado_generado = 0.0
        self.acumulado_aprovechado = 0.0
        self.acumulado_rechazo = 0.0

    def reiniciar_paso_diario(self):
        self.material_generado_dia = 0.0
        self.material_pool_disponible = 0.0
        self.material_aprovechado_dia = 0.0
        self.material_rechazo_dia = 0.0

    def cerrar_paso_diario(self):
        self.acumulado_generado += self.material_generado_dia
        self.acumulado_aprovechado += self.material_aprovechado_dia
        self.acumulado_rechazo += self.material_rechazo_dia
