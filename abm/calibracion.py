"""Calibración multi-año del ABM contra la trayectoria real 2018-2023 de % de aprovechamiento
(ver `Investigacion_Salto_Aprovechamiento.md`).

2018 es el año de INICIALIZACIÓN (ancla): no existe un año anterior del cual heredar estado de
actitud de separación, así que no se calibra contra él. Las 5 transiciones reales 2019-2023 son
el objetivo de la búsqueda. El error de decomposición shift-share (mismo documento) ya mostró que
la recomposición demográfica pura explica ~1.8% del cambio real 2018→2023 — el resto tiene que
salir de los mecanismos reales del modelo (infraestructura/capacidad variando por año +
dinámica de actitud de los hogares), no de que la ciudad simplemente creció.

Con solo 6 puntos reales y 4 parámetros libres, el problema sigue subdeterminado (ver
`Diseno_ABM.md` §8): se hace una búsqueda EXHAUSTIVA en una rejilla pequeña, no un optimizador de
caja negra, y se reporta el ranking completo de combinaciones plausibles — no "el" óptimo falso.
"""
import itertools
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from . import config_abm  # noqa: E402
from .modelo import ModeloResiduosBogota  # noqa: E402

# Serie real oficial (Residuos generados bogota.xlsx), reconciliada en
# Investigacion_Salto_Aprovechamiento.md §1 — única fuente de verdad para estos 6 números.
SERIE_REAL_PCT_APROVECHAMIENTO = {
    2018: 15.38, 2019: 15.70, 2020: 17.28, 2021: 19.18, 2022: 18.27, 2023: 18.56,
}
ANIO_ANCLA = 2018
ANIOS_CALIBRACION = [2019, 2020, 2021, 2022, 2023]
ULTIMO_ANIO_DF_MODELO = 2024  # ver nota en Investigacion_Salto_Aprovechamiento.md: la hoja UPZ del
# DANE (fuente de población) no cubre 2025+, así que el contrafactual real solo llega hasta 2024.


def correr_serie_anios(anio_inicio: int, anio_fin: int, dias_por_anio: int | None = None,
                        rng: int | None = None, verbose: bool = False, **parametros_libres) -> pd.DataFrame:
    """Corre el modelo año a año de `anio_inicio` a `anio_fin`, ENCADENANDO el estado de actitud
    de separación de cada cohorte UPZ×estrato de un año al siguiente (ver
    `ModeloResiduosBogota.estado_final_por_cohorte` / parámetro `estado_previo_cohortes`) — sin
    este encadenamiento cada año se reinicia desde la misma foto fija de la encuesta EM2021 y no
    hay ningún mecanismo capaz de producir una tendencia (ver docstring de `agentes_hogar.py`).
    Devuelve una fila por año con el % de aprovechamiento anual simulado.
    """
    filas = []
    estado_previo = None
    for anio in range(anio_inicio, anio_fin + 1):
        t0 = time.time()
        modelo = ModeloResiduosBogota(
            anio=min(anio, ULTIMO_ANIO_DF_MODELO), rng=rng, estado_previo_cohortes=estado_previo, **parametros_libres
        )
        modelo.correr_anio(dias=dias_por_anio)
        pct = modelo.pct_aprovechamiento_anual()
        filas.append({"anio": anio, "pct_aprovechamiento_simulado": pct})
        estado_previo = modelo.estado_final_por_cohorte()
        if verbose:
            real = SERIE_REAL_PCT_APROVECHAMIENTO.get(anio)
            etiqueta_real = f"(real={real}%)" if real is not None else "(sin dato real / contrafactual)"
            print(f"  {anio}: simulado={pct:.2f}% {etiqueta_real}  [{time.time()-t0:.1f}s]")
    return pd.DataFrame(filas)


def _error_cuadratico(df_simulado: pd.DataFrame) -> tuple[float, int]:
    error, n = 0.0, 0
    for _, fila in df_simulado.iterrows():
        real = SERIE_REAL_PCT_APROVECHAMIENTO.get(int(fila["anio"]))
        if real is None or int(fila["anio"]) == ANIO_ANCLA:
            continue
        error += (fila["pct_aprovechamiento_simulado"] - real) ** 2
        n += 1
    return error, n


def busqueda_en_rejilla(rejilla: dict, dias_por_anio: int = 90, fraccion_muestreo_hogares: float = 0.01,
                         rng: int | None = None) -> pd.DataFrame:
    """Búsqueda exhaustiva sobre una rejilla pequeña de combinaciones de los 4 parámetros libres,
    A RESOLUCIÓN REDUCIDA por tractabilidad (`dias_por_anio` y `fraccion_muestreo_hogares` mucho
    menores que la corrida final de confirmación, 365 días / 3% de muestreo) — práctica estándar
    de "búsqueda gruesa, confirmación fina": la mejor combinación encontrada aquí se re-corre
    después a resolución completa (ver `ejecutar_calibracion.py` / notebook de calibración).
    """
    fraccion_original = config_abm.FRACCION_MUESTREO_HOGARES
    config_abm.FRACCION_MUESTREO_HOGARES = fraccion_muestreo_hogares
    resultados = []
    try:
        claves = list(rejilla.keys())
        combinaciones = list(itertools.product(*rejilla.values()))
        for i, combo in enumerate(combinaciones):
            parametros = dict(zip(claves, combo))
            df_sim = correr_serie_anios(ANIO_ANCLA, 2023, dias_por_anio=dias_por_anio, rng=rng, **parametros)
            error, n = _error_cuadratico(df_sim)
            rmse = (error / n) ** 0.5 if n else float("inf")
            print(f"[{i+1}/{len(combinaciones)}] {parametros} -> RMSE={rmse:.2f}pp")
            resultados.append({**parametros, "error_cuadratico_total": error, "rmse_pp": rmse})
    finally:
        config_abm.FRACCION_MUESTREO_HOGARES = fraccion_original
    return pd.DataFrame(resultados).sort_values("error_cuadratico_total").reset_index(drop=True)
