"""Agente Hogar: genera residuos y decide separarlos o no.

Opera mecanismo #1 de la hipótesis (free-riding / bajo impacto percibido) como un proceso
emergente: la probabilidad de separación de un hogar se ajusta con el tiempo según lo que
observa en sus vecinos de red del mismo estrato, no como un valor fijo por UPZ.

Granularidad de población: ver Diseno_ABM.md §3 — cada agente representa una fracción muestreada
de los hogares reales de su UPZ×estrato (no una cohorte agregada, no 1 agente por hogar real),
con un peso de escalamiento (`poblacion_representada`) para que los agregados del modelo
extrapolen a la población total real.

`participacion_comunitaria` (Fase 3, EM2021): el predictor más fuerte de separación encontrado
en todo el EDA (odds ratio ≈ 2.6 para JAC, ≈ 2.3 para organización ambiental, ver
`Reglas_Negocio_v2_y_Modelado_Agentes.md` §4bis) — no existe a nivel de hogar individual en
ningún dato real, solo el % de participación de la localidad (EM2021). Se resuelve muestreando,
por agente, si "participa" con esa probabilidad real, y aplicando el odds ratio medido a su
`prob_separa_base` — no un número inventado, es la traducción directa del hallazgo del EDA.
"""
import mesa
import numpy as np

from . import config_abm

# Odds ratio ponderado de participación comunitaria sobre separación (Sección 8/9 del EDA,
# EDA_Dirigido_Fase3.ipynb) — se usa el promedio de JAC (2.63) y organización ambiental (2.33)
# como un único efecto conservador, ya que el modelo no distingue entre los dos tipos.
ODDS_RATIO_PARTICIPACION_COMUNITARIA = 2.48

# Odds ratios reales adicionales de la misma regresión logística multivariada ponderada (Sección
# 8/9 del EDA), agregados 2026-07-14 — hasta entonces calculados y validados pero nunca conectados
# al ABM (ver `Justificacion_Metodologica_Comite.md`). `vivienda_propia` es el proxy de tenencia
# usado en el propio EDA (NVCBP10==1, "Casa"), no la variable legal de propiedad. `log_ingreso`
# NO se incluye: se probó y no fue significativo (p=0.33, ver el mismo documento).
ODDS_RATIO_VIVIENDA_PROPIA = 1.40
ODDS_RATIO_INFORMAL = 0.85  # <1: la informalidad laboral reduce la probabilidad de separar


def _ajustar_probabilidad_por_odds_ratio(probabilidad: float, odds_ratio: float) -> float:
    """Convierte correctamente un odds ratio en un ajuste de probabilidad (no es válido
    multiplicar probabilidades directamente por un odds ratio — se debe pasar por la escala de
    momios: odds = p/(1-p), aplicar el ratio, y volver a probabilidad)."""
    probabilidad = min(max(probabilidad, 1e-6), 1 - 1e-6)
    momios = probabilidad / (1 - probabilidad)
    nuevos_momios = momios * odds_ratio
    return nuevos_momios / (1 + nuevos_momios)


def _factor_relativo_por_odds_ratio(odds_ratio: float) -> float:
    """Traduce un odds ratio a un multiplicador relativo (>1 aumenta, <1 reduce), aplicando el
    odds ratio sobre una base NEUTRA de 0.5 (donde probabilidad y momios son simétricos) y
    devolviendo cuánto se movió la probabilidad relativa a esa base. Usado solo para
    `factor_heterogeneidad_hogar` (ver más abajo) — NO para `prob_separa_base`, que sigue el
    ajuste de momios completo vía `_ajustar_probabilidad_por_odds_ratio`."""
    ajustada = _ajustar_probabilidad_por_odds_ratio(0.5, odds_ratio)
    return ajustada / 0.5


_FACTOR_VIVIENDA_PROPIA = _factor_relativo_por_odds_ratio(ODDS_RATIO_VIVIENDA_PROPIA)
_FACTOR_INFORMAL = _factor_relativo_por_odds_ratio(ODDS_RATIO_INFORMAL)


class HogarAgente(mesa.Agent):
    def __init__(self, model, codigo_upz: int, estrato_categoria: str,
                 poblacion_representada: float, prob_separa_base: float,
                 pct_calidad_separacion: float,
                 pct_participacion_comunitaria_localidad: float = 0.0,
                 pct_vivienda_propia_localidad: float = 0.0,
                 pct_informal_localidad: float = 0.0,
                 beta_decaimiento: float | None = None,
                 beta_recuperacion: float | None = None,
                 umbral_percepcion_impacto: float | None = None,
                 factor_brecha_intencion_accion: float | None = None):
        super().__init__(model)
        self.codigo_upz = codigo_upz
        self.estrato_categoria = estrato_categoria  # "Baja" / "Media" / "Alta"
        self.poblacion_representada = poblacion_representada

        # Parámetros libres (ver Diseno_ABM.md §6): configurables por corrida —p.ej. desde los
        # Sliders del dashboard— en vez de leerse siempre del módulo config_abm.
        self.beta_decaimiento = beta_decaimiento if beta_decaimiento is not None else config_abm.BETA_DECAIMIENTO_SEPARACION
        self.beta_recuperacion = beta_recuperacion if beta_recuperacion is not None else config_abm.BETA_RECUPERACION_SEPARACION
        self.umbral_percepcion_impacto = (
            umbral_percepcion_impacto if umbral_percepcion_impacto is not None else config_abm.UMBRAL_PERCEPCION_IMPACTO
        )

        # BUG real encontrado y corregido (2026-07-13): `PROB_SEPARA_PISO` (0.5916) se calibró
        # directamente contra el % crudo de encuesta (pct_separa_en_fuente), pero
        # `prob_separa_base` ya viene reescalado por `factor_brecha_intencion_accion` (~0.56) —
        # mezclar las dos escalas sin corregir dejaba el piso muy por encima de la base real de
        # >99% de los agentes (verificado: solo 0.35% de la población tenía base > piso), así que
        # el decaimiento era un no-op para casi todos, sin importar si el disparador se cumplía.
        # Se reescala el piso por el mismo factor de brecha, para que quede en la misma escala que
        # `prob_separa_base` (con el factor por defecto, esto activa el piso para ~85% de la
        # población en vez de ~0.35%).
        factor_brecha = (
            factor_brecha_intencion_accion if factor_brecha_intencion_accion is not None
            else config_abm.FACTOR_BRECHA_INTENCION_ACCION
        )
        self.piso_escalado = config_abm.PROB_SEPARA_PISO * factor_brecha

        # NOTA: la brecha intención-acción (ver config_abm.py) se aplica en `modelo.py`, ANTES de
        # llegar aquí, y solo sobre el valor crudo de encuesta del año ancla — no sobre un
        # `prob_separa_base` ya encadenado de un año anterior (eso compondría la brecha cada año).

        # Se muestrea si ESTE hogar participa comunitariamente con la probabilidad real de su
        # localidad (EM2021) — no hay dato de participación por hogar individual, solo el % local.
        self.participa_comunitariamente = self.random.random() < (pct_participacion_comunitaria_localidad / 100.0)
        if self.participa_comunitariamente:
            prob_separa_base = _ajustar_probabilidad_por_odds_ratio(prob_separa_base, ODDS_RATIO_PARTICIPACION_COMUNITARIA)

        self.prob_separa_base = prob_separa_base
        self.pct_calidad_separacion = pct_calidad_separacion / 100.0 if pct_calidad_separacion > 1 else pct_calidad_separacion
        self.prob_separa_actual = prob_separa_base

        # Heterogeneidad real adicional (ronda 4, 2026-07-14): mismo patrón de muestreo que
        # participación comunitaria arriba (tasa real de la localidad, EM2021), pero aplicada
        # como un MULTIPLICADOR DE SALIDA separado (`factor_heterogeneidad_hogar`), NO sobre
        # `prob_separa_base`. Motivo, encontrado al verificar numéricamente esta ronda (ver
        # `Justificacion_Metodologica_Comite.md`): `prob_separa_base` también gobierna el
        # disparador de decaimiento en `actualizar_actitud_separacion` (comparación no lineal
        # contra un umbral). Mutar `prob_separa_base` por agente —aun preservando el promedio de
        # la cohorte— cambia CUÁNTOS agentes cruzan el umbral (un efecto de varianza sobre una
        # regla no lineal, no solo de nivel), lo que desvió sistemáticamente la trayectoria
        # 2018-2023 (RMSE pasó de 1.15pp a 4.25pp en la primera versión de este cambio). Separando
        # la heterogeneidad del disparador de decaimiento —el mecanismo calibrado queda IDÉNTICO,
        # actuando sobre el `prob_separa_base` uniforme de la cohorte— y aplicándola solo a la
        # salida diaria (`step()`), cada hogar sigue separando una cantidad real distinta de
        # material según sus covariables reales, sin mover la dinámica ya calibrada.
        self.tiene_vivienda_propia = self.random.random() < (pct_vivienda_propia_localidad / 100.0)
        self.es_informal = self.random.random() < (pct_informal_localidad / 100.0)
        factor = 1.0
        if self.tiene_vivienda_propia:
            factor *= _FACTOR_VIVIENDA_PROPIA
        if self.es_informal:
            factor *= _FACTOR_INFORMAL
        # Normalizado después, en `normalizar_factor_heterogeneidad` (llamada desde `modelo.py`
        # tras instanciar toda la cohorte), para que el promedio ponderado por población de este
        # factor quede en 1.0 exacto — sin eso, la fracción real de agentes con vivienda propia/
        # informalidad en cada localidad movería el promedio agregado de material separado.
        self.factor_heterogeneidad_hogar = factor

        from src import config as config_datos
        self.generacion_diaria = (
            self.poblacion_representada * config_datos.RESIDUOS_PER_CAPITA_TON_ANIO / config_abm.DIAS_POR_ANIO
        )

        self.material_separado_acumulado = 0.0
        self.material_no_separado_acumulado = 0.0

    def step(self):
        """Un día: genera residuos y separa (o no) según su probabilidad actual."""
        entorno = self.model.entornos[self.codigo_upz]

        infraestructura = entorno.infraestructura_index
        # `factor_heterogeneidad_hogar` (normalizado a promedio 1.0 por cohorte, ver
        # `normalizar_factor_heterogeneidad`) traslada la heterogeneidad real de vivienda/
        # informalidad a la salida diaria, sin tocar `prob_separa_actual` (que gobierna la
        # dinámica de decaimiento/recuperación ya calibrada). El clip a 1.0 es una salvaguarda de
        # sentido físico (una fracción separada no puede superar el 100% del material generado);
        # verificado que rara vez se activa dado el rango real de `prob_separa_actual` y del
        # factor (ver script de verificación).
        prob_efectiva = min(self.prob_separa_actual * infraestructura * self.factor_heterogeneidad_hogar, 1.0)

        material_separado = self.generacion_diaria * prob_efectiva * self.pct_calidad_separacion
        material_no_separado = self.generacion_diaria - material_separado

        entorno.material_generado_dia += self.generacion_diaria
        entorno.material_pool_disponible += material_separado

        self.material_separado_acumulado += material_separado
        self.material_no_separado_acumulado += material_no_separado

    def actualizar_actitud_separacion(self, promedio_vecinos: float):
        """Efecto de imitación/free-riding: ajusta `prob_separa_actual` según el promedio de
        vecinos de red del mismo estrato (mecanismo #1 de la hipótesis), en una cadencia más
        lenta que la generación diaria (ver `ModeloResiduosBogota._actualizar_actitudes_hogares`,
        que precalcula `promedio_vecinos` una sola vez por UPZ×estrato en vez de que cada agente
        recorra la red — con miles de agentes, hacerlo por agente es demasiado lento).

        BUG real encontrado y corregido (2026-07-13): el disparador de decaimiento comparaba
        `promedio_vecinos` contra un umbral ABSOLUTO fijo (0.15) — pero se verificó que NINGUNA
        de las 204 cohortes UPZ×estrato reales tiene un promedio de vecinos por debajo de 0.187
        (el mínimo real observado). El umbral era matemáticamente inalcanzable desde el primer
        día: como cada agente arranca exactamente en su propio techo (`prob_separa_actual =
        prob_separa_base`), y la rama de "recuperación" en el techo es un no-op (`min(base, base
        + beta) = base`), el modelo quedaba congelado desde el día 1 — de ahí que TODAS las
        series del dashboard (generado, aprovechado, rechazo, %) salieran perfectamente planas, y
        también explica retroactivamente por qué 4 de los 5 parámetros libres salieron "no
        identificables" en la calibración (§7.6 de `Investigacion_Salto_Aprovechamiento.md`):
        nunca llegaban a ejecutarse. Se corrige comparando contra un umbral RELATIVO a la propia
        base del agente (¿mis vecinos separan sensiblemente MENOS que yo?), que sí es alcanzable:
        con un margen de 0.02 (el nuevo valor por defecto, ver `config_abm.py`), ~17% de las
        cohortes reales disparan decaimiento desde el arranque — ni 0% ni 100%.
        """
        if promedio_vecinos < (self.prob_separa_base - self.umbral_percepcion_impacto):
            # entorno de baja participación + aporte individual percibido como irrelevante -> decae.
            # El piso (`self.piso_escalado`, ya en la misma escala que `prob_separa_base` — ver
            # __init__) nunca puede superar la propia base del agente, para que el agente nunca
            # "decaiga" hacia arriba y rompa el invariante de que `prob_separa_actual` nunca
            # excede la base.
            piso_efectivo = min(self.piso_escalado, self.prob_separa_base)
            self.prob_separa_actual = max(
                piso_efectivo,
                self.prob_separa_actual - self.beta_decaimiento,
            )
        else:
            # entorno mejora -> se recupera hacia la base (nunca por encima de ella en el MVP)
            self.prob_separa_actual = min(
                self.prob_separa_base,
                self.prob_separa_actual + self.beta_recuperacion,
            )


def normalizar_factor_heterogeneidad(agentes: list[HogarAgente]) -> None:
    """Reescala `factor_heterogeneidad_hogar` de TODOS los agentes de una cohorte UPZ×estrato
    para que su promedio ponderado por población quede exactamente en 1.0.

    Se llama una sola vez por cohorte, en `modelo.py`, justo después de instanciar todos sus
    agentes. Sin esto, la fracción real de hogares con vivienda propia/informalidad de cada
    localidad (que varía de localidad a localidad) movería el promedio agregado de material
    separado de la cohorte — invalidando el % de aprovechamiento de ciudad que la calibración
    ajustó. Con la normalización, cada hogar sigue separando una cantidad distinta según sus
    covariables reales, pero el promedio de la cohorte no se mueve.

    A diferencia de la corrección de `prob_separa_base` que se intentó primero (ver nota en
    `HogarAgente.__init__`), esta es una reescala LINEAL simple (no en espacio de momios): el
    factor es un multiplicador de salida sin restricción [0,1], así que no hace falta bisección.
    """
    if not agentes:
        return

    pesos = np.array([a.poblacion_representada for a in agentes], dtype=float)
    peso_total = pesos.sum()
    if peso_total <= 0:
        return

    factores = np.array([a.factor_heterogeneidad_hogar for a in agentes], dtype=float)
    promedio_actual = np.average(factores, weights=pesos)
    if promedio_actual <= 0:
        return

    factores_normalizados = factores / promedio_actual
    for agente, factor in zip(agentes, factores_normalizados):
        agente.factor_heterogeneidad_hogar = float(factor)
