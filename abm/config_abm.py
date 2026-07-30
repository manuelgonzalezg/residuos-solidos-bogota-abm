"""Parámetros del ABM (MVP): muestreo de población, calendario y parámetros libres.

Separado de `src/config.py` (que es de la Fase 1 de datos) porque estos valores son propios
de la simulación, no de la carga/limpieza de datos. Los parámetros marcados como "libre" no
tienen valor real en `03_reglas_negocio.csv` (quedaron "Pendiente") — se fija aquí un valor de
partida razonable, documentado como supuesto, ajustable en la fase de calibración (post-MVP).
"""
from pathlib import Path

PROYECTO_DIR = Path(__file__).resolve().parent.parent
RUTA_ADYACENCIA_UPZ = PROYECTO_DIR / "data" / "processed" / "09_adyacencia_upz.csv"

# --- Muestreo de hogares (ver Diseno_ABM.md §3) ---
# Ni 3 cohortes agregadas ni 1 agente por cada hogar real (~2.7 millones, inviable). Se muestrea
# esta fracción de los hogares reales de cada UPZ×estrato como agentes individuales, cada uno
# con un peso de escalamiento para que los agregados del modelo representen la población total.
FRACCION_MUESTREO_HOGARES = 0.03  # 3% — ajustable si el desempeño de la máquina lo permite
MIN_AGENTES_HOGAR_POR_CELDA = 1   # al menos 1 agente por UPZ×estrato con HOGARES > 0

# --- Calendario ---
DIAS_POR_ANIO = 365
CADA_CUANTOS_DIAS_ACTUALIZA_ACTITUD = 7  # cadencia "lenta" del efecto de imitación/free-riding

# --- Parámetros libres de comportamiento del hogar ---
# `PROB_SEPARA_PISO` ya NO es un número inventado: es el mínimo real observado de
# `pct_separa_upz` entre las 112 UPZ reales (EM2021, ver
# `abm/datos_reales.py::construir_o_cargar_separacion_upz_em2021`) — ver
# Justificacion_Metodologica_Comite.md §5.
#
# Recalculado 2026-07-14 (ronda 5): antes (0.5916) era el mínimo de `pct_separa_en_fuente`
# (ECA2021) entre LOCALIDADES con muestra razonable, excluyendo Los Mártires (n=1) y Santa Fe
# (n=3) por ser degeneradas. Con EM2021 a nivel UPZ, cada una de las 112 UPZ tiene 600+ hogares de
# muestra — ya no hace falta excluir nada, el mínimo real (UPZ 95, Las Cruces, Santa Fe, n=939)
# es un dato genuinamente confiable, no un artefacto de muestra pequeña.
PROB_SEPARA_PISO = 0.4399  # mínimo real observado (UPZ 95 Las Cruces, n=939, 43.99% de pct_separa_upz)

# Los 3 siguientes SIGUEN siendo supuestos de VELOCIDAD — ningún dato longitudinal (que siga a
# los mismos hogares en el tiempo) existe en ninguna fuente disponible para medir qué tan rápido
# cambia una actitud. Documentado como el punto más débil del modelo (Reglas_Negocio_v2... §3.3).
#
# HISTORIA DE ESTA CALIBRACIÓN (dejada trazable a propósito, no se borra):
# - 2026-07-11: primera calibración (`factor_brecha`=0.56, RMSE≈1.07pp) reportó estos 3
#   parámetros como "no identificables" — atribuido entonces a un límite de resolución de los
#   datos anuales agregados.
# - 2026-07-13: se encontró que la "no identificabilidad" en realidad era DOS bugs reales de
#   mecanismo, no un límite de datos:
#   (1) el disparador de decaimiento en `agentes_hogar.py::actualizar_actitud_separacion`
#       comparaba contra un umbral ABSOLUTO (0.15) que ninguna de las 204 cohortes UPZ×estrato
#       reales alcanzaba nunca (mínimo real observado: 0.187) — corregido a un umbral RELATIVO a
#       la base propia del agente.
#   (2) `PROB_SEPARA_PISO` (0.5916) estaba calibrado contra el % crudo de encuesta pero nunca se
#       reescalaba por `FACTOR_BRECHA_INTENCION_ACCION` como sí se hace con `prob_separa_base` —
#       dejaba el piso muy por encima de la base real de 99.65% de los agentes, bloqueando el
#       decaimiento aunque el disparador sí se cumpliera. Corregido: el piso se reescala por la
#       misma brecha (ver `HogarAgente.__init__`, `self.piso_escalado`).
#   Con el mecanismo real y funcionando, se recalibraron los 4 parámetros juntos (búsqueda en
#   rejilla de 2 etapas, 80 combinaciones, contra los 6 puntos reales 2018-2023) — resultado:
#   RMSE≈1.15pp a resolución completa (comparable al 1.07pp "roto" de antes, pero ahora con un
#   mecanismo genuinamente vivo). `beta_recuperacion` sigue sin afectar el resultado (no es un
#   bug: la recuperación solo importa para cohortes que ya decayeron y luego ven mejorar a sus
#   vecinos, algo raro en una cadena de 6 años) — se conserva en su valor de partida.
# - 2026-07-14 (ronda 5): `prob_separa` cambió de fuente (ECA2021/localidad → EM2021/UPZ, ver
#   `PROB_SEPARA_PISO` arriba y `Justificacion_Metodologica_Comite.md` §5bis) — nivel de ciudad
#   subió ~2.6pp, así que se recalibró de nuevo. Búsqueda en 3 etapas (rejilla ampliada 2 veces
#   porque el óptimo caía en el borde) a resolución reducida encontró
#   `brecha=0.63, decay=0.04, umbral=0.07` con RMSE≈1.21pp — pero al confirmar a RESOLUCIÓN
#   COMPLETA (365 días/año) ese mismo combo dio RMSE=2.10pp, mucho peor. Hallazgo metodológico
#   nuevo: a diferencia de las 2 recalibraciones anteriores, esta vez la resolución reducida (90
#   días/año) NO fue un proxy confiable de la resolución completa — hipótesis: el ciclo semanal de
#   actualización de actitud corre solo ~12 veces en 90 días pero ~52 veces en 365 días, así que
#   un `beta_decaimiento` que se ve bien con 12 ciclos puede sobre-acumular decaimiento con 52. Se
#   probaron 4 variantes adicionales DIRECTAMENTE a resolución completa (más caro pero
#   definitivo): `decay=0.02` (en vez de 0.04) con los mismos brecha/umbral dio **RMSE=1.1961pp**
#   — el mejor de los 5 combos probados a resolución completa, prácticamente igual al 1.15pp
#   histórico. `umbral=0.035` (el valor de antes de esta ronda) resultó MUCHO peor con la nueva
#   base (RMSE 5.4-6.6pp en 3 variantes distintas de brecha/decay) — confirma que el umbral más
#   ancho (0.07) es necesario con EM2021, no es intercambiable con el valor viejo.
BETA_DECAIMIENTO_SEPARACION = 0.02    # cuánto baja prob_separa_actual si el entorno es de baja participación
BETA_RECUPERACION_SEPARACION = 0.02   # cuánto sube prob_separa_actual si el entorno mejora (no identificable)
UMBRAL_PERCEPCION_IMPACTO = 0.07      # margen bajo la base propia (no absoluto) que activa el decaimiento

# --- Brecha intención-acción (parámetro libre, nuevo 2026-07-11, recalibrado 2026-07-13 y 2026-07-14) ---
# `prob_separa` viene de una ENCUESTA ("¿este hogar clasifica los residuos?", autorreporte) — no
# es la misma magnitud que el % de aprovechamiento OFICIAL (medición/estimación de material
# efectivamente recuperado). La brecha entre "digo que separo" y "el material realmente se
# recupera y se cuenta como aprovechado" está ampliamente documentada en la literatura de
# comportamiento ambiental (intention-action gap / social-desirability bias) — no es un error de
# encuesta ni del modelo. Ver `abm/calibracion.py` y `Investigacion_Salto_Aprovechamiento.md` §7.
#
# NOTA DE CORRECCIÓN DE DOCUMENTACIÓN (2026-07-14): esta línea decía por error "EM2021" cuando la
# fuente real de `prob_separa` hasta el 2026-07-13 era ECA2021 (confirmado: `PROB_SEPARA_PISO`
# "Kennedy n=191" solo cuadra con la muestra pequeña de ECA2021 — EM2021 tiene 26,638 encuestas en
# Kennedy). A partir de la ronda 5 (2026-07-14) la fuente SÍ es EM2021 (a nivel UPZ, ver arriba),
# así que el texto ya es correcto hacia adelante — se deja esta nota para que quede trazable que
# fue un error corregido, no una casualidad.
#
# Recalibrado 2026-07-13 (de 0.56 a 0.60, tras corregir 2 bugs de mecanismo) y de nuevo el
# 2026-07-14 (ronda 5, de 0.60 a 0.63) al cambiar la fuente de `prob_separa` de ECA2021/localidad
# a EM2021/UPZ — búsqueda en rejilla de 3 etapas (rejilla ampliada 2 veces porque el óptimo caía
# en el borde) contra los 6 puntos reales 2018-2023, confirmado a RESOLUCIÓN COMPLETA (no solo a
# la resolución reducida de la búsqueda, ver nota en `BETA_DECAIMIENTO_SEPARACION` arriba sobre
# por qué esta vez sí hubo que confirmar con cuidado): **RMSE=1.1961pp**, contrafactual y demás
# cifras derivadas pendientes de recalcular con esta base (ver Justificacion_Metodologica_
# Comite.md §5bis e Investigacion_Salto_Aprovechamiento.md §7-8 para el detalle completo).
FACTOR_BRECHA_INTENCION_ACCION = 0.63

# --- Parámetros libres de recicladores (RN020-022 en 03_reglas_negocio.csv están "Pendiente") ---
# Sigue siendo un supuesto (ningún dato mide productividad individual), pero ahora con una cota
# superior de consistencia: 15 kg/día × ~24,895 recicladores activos ≈ 11,200 ton/mes, del orden
# de ~7% de lo que recolecta el sistema formal (RBL) — un valor implausible se saldría de ese
# orden de magnitud. Ver Reglas_Negocio_v2_y_Modelado_Agentes.md §3.2.
CAPACIDAD_RECOLECCION_KG_DIA_POR_RECICLADOR = 15.0  # supuesto acotado, rango plausible 10-25

# --- Incentivo económico real (VIAT + factor de subsidio por estrato, CRA/Ciudad Limpia dic-2025) ---
# Mecanismo NUEVO, no existía en el MVP original — ver abm/datos_reales.py y
# Reglas_Negocio_v2_y_Modelado_Agentes.md §3.5. Tarifa oficial real (CRA/Ciudad Limpia).
VIAT_PESOS_POR_TONELADA = 11_388.0

# --- Reparto del pool de material entre recicladores y sumidero formal ---
# Ya NO es "sin restricción de capacidad": OperadorUAESP ahora se instancia (5 agentes, uno por
# ASE) con capacidad diaria real (promedio histórico del RBL consolidado, ver
# abm/datos_reales.py::construir_o_cargar_capacidad_ase) — ver Reglas_Negocio_v2... §4quater.
# En la práctica, esa capacidad real casi nunca se satura (evidencia del EDA §2), por lo que el
# comportamiento agregado es similar al del MVP, pero ahora es verificable, no solo asumido.

SEMILLA_ALEATORIA = 42
