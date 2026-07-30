# -*- coding: utf-8 -*-
"""Regenera `data/processed/23_confirmacion_calibracion_2018_2024.csv` con el combo FINAL de
`config_abm.py` a RESOLUCIÓN COMPLETA (365 días/año, muestreo 3%), con semilla fija, y reporta
el RMSE con la convención oficial del proyecto (2019-2023, año ancla 2018 excluido — ver
`calibracion.py::_error_cuadratico`).

Cierra el hallazgo A7 de `src/Auditorias/Auditoria_Matematica_y_UX_Simulador.md`: deja UN solo
artefacto de confirmación, trazable a UNA corrida documentada, consistente con la cifra citada
en la tesis.

Uso (desde la raíz del proyecto, con el mismo entorno Python del dashboard):
    python -m abm.regenerar_confirmacion

Duración estimada: ~15 min (7 años × 365 días × ~75k agentes).
"""
import math
import sys
import time
from pathlib import Path

import pandas as pd

PROYECTO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROYECTO))

from abm import calibracion, config_abm  # noqa: E402

RUTA_SALIDA = PROYECTO / "data" / "processed" / "23_confirmacion_calibracion_2018_2024.csv"


def main() -> None:
    t0 = time.time()
    print("Regenerando confirmación 2018-2024 a resolución completa...")
    print(f"  Combo final (config_abm): brecha={config_abm.FACTOR_BRECHA_INTENCION_ACCION}, "
          f"decay={config_abm.BETA_DECAIMIENTO_SEPARACION}, "
          f"recup={config_abm.BETA_RECUPERACION_SEPARACION}, "
          f"umbral={config_abm.UMBRAL_PERCEPCION_IMPACTO}, "
          f"cap_recol={config_abm.CAPACIDAD_RECOLECCION_KG_DIA_POR_RECICLADOR}, "
          f"semilla={config_abm.SEMILLA_ALEATORIA}")

    df = calibracion.correr_serie_anios(
        2018, 2024,
        dias_por_anio=None,          # None = resolución completa (365)
        rng=config_abm.SEMILLA_ALEATORIA,
        verbose=True,
    )

    df["pct_real"] = df["anio"].map(calibracion.SERIE_REAL_PCT_APROVECHAMIENTO)
    df.to_csv(RUTA_SALIDA, index=False, encoding="utf-8-sig")

    # RMSE con la convención oficial: 2019-2023, ancla 2018 excluida.
    filas = df[(df["anio"] != calibracion.ANIO_ANCLA) & df["pct_real"].notna()]
    rmse = math.sqrt(((filas["pct_aprovechamiento_simulado"] - filas["pct_real"]) ** 2).mean())

    print(f"\n  {RUTA_SALIDA.name} regenerado ({len(df)} filas).")
    print(f"  RMSE (2019-2023, año ancla excluido) = {rmse:.4f} pp")
    print("  Cifra citable: 'RMSE ≈ {:.2f} pp (2019-2023, año ancla excluido)'".format(rmse))
    print(f"  Tiempo total: {(time.time() - t0) / 60:.1f} min")


if __name__ == "__main__":
    main()
