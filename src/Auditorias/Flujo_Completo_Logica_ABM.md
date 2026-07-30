# Flujo Completo del Sistema — Lógica Exacta que Ejecuta el ABM

### De la inicialización anual al ciclo diario, semanal y multi-año — con cita de archivo/función para cada paso

---

## 0. Cómo leer este documento

Este documento traza, en el orden exacto en que el código lo ejecuta, todo el flujo del ABM: qué
pasa una vez al iniciar un año, qué pasa cada día, qué pasa cada semana, y qué pasa al encadenar
varios años. No es una descripción conceptual — cada paso cita el archivo y la función real que
lo ejecuta (`abm/modelo.py`, `abm/agentes_hogar.py`, `abm/agentes_reciclador.py`,
`abm/agentes_infraestructura.py`, `abm/entorno.py`, `abm/calibracion.py`). Complementa a
`Diseno_ABM.md` (diseño), `Reglas_Negocio_v2_y_Modelado_Agentes.md` (origen de cada regla) y
`Justificacion_Metodologica_Comite.md` (por qué UPZ, de dónde sale cada beta) — aquí lo que
importa es el **orden de ejecución**, no la justificación de cada número.

Hay un diagrama visual del mismo flujo (ver mensaje de entrega) — este documento es su versión
citable y detallada.

---

## 1. Inicialización — una vez, al construir el modelo de un año (`ModeloResiduosBogota.__init__`)

1. **Carga de insumos del año** (`modelo.py:72-76`): lee `df_modelo.csv`, filtra las 112 filas
   (una por UPZ) del `anio` pedido. Si el año pedido es posterior a 2024 (último año con datos
   DANE de población), usa el snapshot de 2024 (`ULTIMO_ANIO_DF_MODELO`).
2. **Red de vecindad UPZ** (`modelo.py:79-81`): construye el grafo de contigüidad geográfica
   entre las 112 UPZ (`entorno.construir_grafo_upz`) — es el canal por el que se propaga la
   imitación social (§3).
3. **Carga de datos reales** (`modelo.py:84-106`), todos cacheados en `data/processed/`, ninguno
   recalculado en cada corrida:
   - Infraestructura real por UPZ y año (`datos_reales.construir_o_cargar_infraestructura_real_por_anio`,
     puntos críticos SIGAB, snapshot más cercano al año simulado).
   - Participación comunitaria por localidad (`construir_o_cargar_participacion_comunitaria`,
     EM2021, ponderada por `FEX_C`).
   - Perfil de hogar por localidad — vivienda propia e informalidad
     (`construir_o_cargar_perfil_hogar_localidad`, EM2021, ponderada).
   - Formalización de recicladores por localidad (`construir_o_cargar_formalizacion_recicladores`, RURO 2022).
   - Capacidad diaria real por ASE y año (`construir_o_cargar_capacidad_ase_por_anio`, RBL consolidado).
4. **Por cada una de las 112 UPZ** (`modelo.py:115-199`):
   1. Crea `EntornoUPZ` (`entorno.py:64`) con los atributos demográficos/estrato reales de esa fila.
   2. Fija `infraestructura_index` = snapshot SIGAB real más cercano al año, **× `multiplicador_infraestructura`**
      (control de escenario, default 1.0 = dato real sin cambios; tope 1.0 aunque el multiplicador sea mayor).
   3. Fija `factor_incentivo` (tarifa CRA real ponderada por composición de estrato) — **descriptivo, no causal**:
      se calcula y se muestra, pero no entra en ningún cálculo de probabilidad de separación (ver §6).
   4. Fija `pct_participacion_comunitaria`, `pct_vivienda_propia_localidad`, `pct_informal_localidad`
      (EM2021, real a nivel localidad, Sumapaz excluida).
   5. Fija `pct_registro_activo_reciclador`, `pct_formalizacion_laboral_reciclador` (RURO 2022).
   6. Asigna recicladores de esa localidad a la UPZ, proporcional a población (evita doble conteo).
   7. Crea `PoblacionRecicladoresUPZ` (`agentes_reciclador.py:18`) — una por UPZ.
   8. **Por cada categoría de estrato** (Baja/Media/Alta) con hogares > 0:
      - Calcula `n_agentes = max(1, round(hogares_categoria × 3%))` — `FRACCION_MUESTREO_HOGARES`.
      - Calcula `prob_separa_base_cohorte`: si viene de un año anterior encadenado
        (`estado_previo_cohortes`, ver §4), usa ese valor tal cual; si no, usa
        `prob_separa_upz_real (EM2021, §8.1.6 de la tesis) × factor_brecha_intencion_accion`
        (0.63, valor final tras la recalibración de la ronda 5 — actualizado 2026-07-19, antes
        decía 0.60/ECA2021, ya reemplazado por la fuente EM2021/UPZ).
      - Instancia `n_agentes` de `HogarAgente` (`agentes_hogar.py:62`), cada uno con:
        - `prob_separa_base` = el valor de la cohorte, ajustado por odds ratio (×2.48) si el
          agente "participa comunitariamente" (sorteo Bernoulli con la tasa real de su localidad —
          en la práctica solo ~0.4% de los agentes).
        - `piso_escalado` = `PROB_SEPARA_PISO × factor_brecha` (mismo factor que arriba).
        - `factor_heterogeneidad_hogar` = 1.0 × (factor por vivienda propia, si el sorteo de esa
          localidad lo asigna) × (factor por informalidad, si el sorteo lo asigna) — ver §6.
      - **Normaliza la cohorte** (`agentes_hogar.normalizar_factor_heterogeneidad`): reescala
        `factor_heterogeneidad_hogar` de todos los agentes de esa cohorte para que su promedio
        ponderado por población quede exactamente en 1.0 — la heterogeneidad no mueve el
        promedio ya calibrado, solo agrega varianza real alrededor de él.
5. **Operadores formales** (`modelo.py:204-212`): crea 5 `OperadorUAESP` (`agentes_infraestructura.py:11`),
   uno por ASE, con `capacidad_dia_ton` = capacidad real del RBL consolidado **× `multiplicador_capacidad_formal`**
   (control de escenario, default 1.0). Suma total → `capacidad_formal_total_dia_ton`.

Al terminar la inicialización existen: 112 `EntornoUPZ`, 112 `PoblacionRecicladoresUPZ`, 5
`OperadorUAESP`, y **75,273 `HogarAgente`** (sobre 204 cohortes UPZ×estrato reales).

---

## 2. Ciclo diario — se repite 365 veces por año (`ModeloResiduosBogota.step`, `modelo.py:321`)

```
2.1  reiniciar_paso_diario()        →  cada EntornoUPZ pone en 0 sus contadores del día
2.2  HogarAgente.step()             →  GENERACIÓN + DECISIÓN DE SEPARACIÓN     (§2.2)
2.3  PoblacionRecicladoresUPZ.step()→  RECOLECCIÓN INFORMAL (por UPZ)          (§2.3)
2.4  _recoleccion_formal()          →  RECOLECCIÓN FORMAL (techo de ciudad)    (§2.4)
2.5  cálculo de rechazo             →  lo no recuperado → Doña Juana           (§2.5)
2.6  datacollector.collect()        →  registra las series del día
2.7  dia_actual += 1; running = (dia_actual < 365)
2.8  si dia_actual % 7 == 0: _actualizar_actitudes_hogares()   (§3, semanal)
```

### 2.2 Generación y decisión de separación — `HogarAgente.step()` (`agentes_hogar.py:150`)

Cada hogar (en orden aleatorio, `shuffle_do`) genera una cantidad fija de residuos ese día
(`generacion_diaria`, proporcional a la población que representa) y decide qué fracción separa:

```
prob_efectiva = min(prob_separa_actual × infraestructura_index × factor_heterogeneidad_hogar, 1.0)
material_separado = generacion_diaria × prob_efectiva × pct_calidad_separacion
```

- `prob_separa_actual`: la actitud del hogar HOY (arranca en `prob_separa_base`, la modifica el
  ciclo semanal de §3 — es la única variable de estado que persiste día a día).
- `infraestructura_index`: real (SIGAB), 0-1, por UPZ — mecanismo causal verificado.
- `factor_heterogeneidad_hogar`: real (vivienda propia/informalidad, EM2021), normalizado a
  promedio 1.0 por cohorte — cada hogar separa una cantidad distinta según sus covariables reales.

El material separado entra al `material_pool_disponible` de su `EntornoUPZ` — un fondo común por
UPZ, no asignado todavía a nadie.

### 2.3 Recolección informal — `PoblacionRecicladoresUPZ.step()` (`agentes_reciclador.py:63`)

Cada población de recicladores (una por UPZ, en orden aleatorio) reclama del pool **de su propia
UPZ**, hasta su capacidad diaria (`n_recicladores_asignados × 15 kg/día`, supuesto acotado — ver
`Justificacion_Metodologica_Comite.md` §3):

```
reclamado = min(capacidad_total_dia_ton, entorno.material_pool_disponible)
```

Esto es el mecanismo #2 de la hipótesis: los recicladores de oficio compiten, SIN coordinación
explícita entre ellos, por el material ya separado — el orden aleatorio de `shuffle_do` en cada
día es justamente la ausencia de una asignación coordinada.

### 2.4 Recolección formal — `_recoleccion_formal()` (`modelo.py:269`)

Lo que el pool de CADA UPZ deja sin reclamar los recicladores informales se suma a un pool total
de CIUDAD. Los 5 operadores ASE no reclaman por UPZ individual (no hay dato real de qué UPZ
atiende cada ASE) — recogen contra un techo agregado único:

```
recolectado_formal = min(pool_total_restante_ciudad, capacidad_formal_total_dia_ton)
```

Ese volumen se reparte de vuelta a cada UPZ **proporcional a cuánto pool le quedaba** (ninguna UPZ
se queda sin atender por el orden de recorrido). En la práctica esta capacidad casi nunca se
satura (evidencia real del EDA: el RBL nunca muestra señales de saturación en 8 años).

### 2.5 Rechazo — lo que ningún actor recuperó

```
material_rechazo_dia = max(material_generado_dia - material_aprovechado_dia, 0.0)
```

Conceptualmente es lo que termina en el Relleno Sanitario Doña Juana — el modelo lo trata como un
acumulador de balance de masa (no simula el relleno como agente con capacidad propia, ver
`Reglas_Negocio_v2_y_Modelado_Agentes.md` §4quater).

### 2.6 Cierre del día

`EntornoUPZ.cerrar_paso_diario()` (`entorno.py:116`) suma lo del día a los acumuladores del año
(`acumulado_generado`, `acumulado_aprovechado`, `acumulado_rechazo`) — son estos acumulados, no
los valores del día, los que alimentan el % de aprovechamiento acumulado que muestra el
dashboard. `self.running` pasa a `False` en el día 365 (tope real del año simulado, respetado
nativamente por `ModelController` de Mesa).

---

## 3. Ciclo semanal — actualización de actitud (`_actualizar_actitudes_hogares`, `modelo.py:301`)

Cada 7 días (`CADA_CUANTOS_DIAS_ACTUALIZA_ACTITUD`), el mecanismo #1 de la hipótesis
(free-riding / bajo impacto percibido) se ejecuta en dos pasadas O(n):

1. Promedio de `prob_separa_actual` por cada cohorte (UPZ, estrato).
2. Para cada cohorte, promedio de ESE valor entre ella y sus UPZ vecinas de red (misma
   categoría de estrato) → `promedio_vecinos`.
3. Cada hogar de la cohorte ejecuta `actualizar_actitud_separacion(promedio_vecinos)`
   (`agentes_hogar.py:173`):

```
si promedio_vecinos < (prob_separa_base − umbral_percepcion_impacto):
    # el entorno separa sensiblemente MENOS que mi propia base → decae
    piso_efectivo = min(piso_escalado, prob_separa_base)
    prob_separa_actual = max(piso_efectivo, prob_separa_actual − beta_decaimiento)
si no:
    # el entorno mejora o está a la par → se recupera hacia la base (nunca por encima)
    prob_separa_actual = min(prob_separa_base, prob_separa_actual + beta_recuperacion)
```

El umbral es RELATIVO a la propia base del agente (no absoluto). **Actualizado 2026-07-19**: el
valor final calibrado es 0.07 (antes 0.035, valor de un episodio de calibración ya reemplazado —
ver `abm/config_abm.py::UMBRAL_PERCEPCION_IMPACTO`); la cifra de "~17% de las cohortes disparan
decaimiento desde el arranque del año" corresponde a ese valor anterior y no se ha revalidado
contra 0.07 — no debe citarse como vigente sin recalcularla. Este mecanismo opera sobre el
`prob_separa_base` UNIFORME de la cohorte (no sobre la heterogeneidad de vivienda/informalidad de
§6) — es exactamente la dinámica que la calibración final ajustó, sin alteración.

---

## 4. Cierre de año y encadenamiento multi-año

- `pct_aprovechamiento_anual()` (`modelo.py:377`): Σ`acumulado_aprovechado` / Σ`acumulado_generado`
  de las 112 UPZ — el número que se compara contra la serie real UAESP.
- `estado_final_por_cohorte()` (`modelo.py:352`): promedio de `prob_separa_actual` ponderado por
  población, por cada una de las 204 cohortes — es la "memoria" que un año le deja al siguiente.
- **Simulación encadenada** (`abm/calibracion.py::correr_serie_anios`, `calibracion.py:38`): corre
  año por año, pasando `estado_final_por_cohorte()` del año N como `estado_previo_cohortes` del
  año N+1 (§1, paso 4). Sin este encadenamiento, cada año reiniciaría desde la misma foto fija de
  la encuesta EM2021/ECA2021 y no habría ningún mecanismo capaz de producir una tendencia real
  año a año — es lo que le da al modelo memoria genuina, no solo un promedio anual repetido.
- 2018 es año-ancla (no se calibra contra él, no hay año anterior del cual heredar estado); las 5
  transiciones reales 2019-2023 son el objetivo de calibración (`calibracion.py::_error_cuadratico`).

---

## 5. Dónde entran los controles de escenario del dashboard

Panel "Escenarios y política" (`abm/dashboard.py`), dos multiplicadores, ambos aplicados en la
inicialización (§1), default 1.0 = dato real sin cambios:

- `multiplicador_infraestructura`: escala `infraestructura_index` real — mecanismo causal
  verificado (multiplica `prob_efectiva` en §2.2).
- `multiplicador_capacidad_formal`: escala `capacidad_dia_ton` de cada `OperadorUAESP` — mecanismo
  causal verificado (techo real de §2.4).

Ambos, con multiplicador=1.0, reproducen EXACTAMENTE la calibración confirmada (RMSE≈1.15pp) —
verificado como no-regresión antes de exponerlos como sliders.

---

## 6. Lo que se calcula pero NO participa en ningún cálculo (descriptivo, no causal)

Para que quede explícito y no se confunda con un mecanismo activo: `factor_incentivo` (tarifa
CRA/VIAT real por composición de estrato de cada UPZ, §1 paso 3) se calcula y se muestra en el
mapa "Cómo funciona el sistema", pero **nunca** entra en el cálculo de `prob_efectiva` ni de
ningún flujo de material — es contexto real, no un mecanismo simulado (decisión explícita del
usuario: solo se muestran variables trazables Y dinámicas en el panel de escenarios; el incentivo
económico es real pero estático, así que se queda como panel descriptivo — ver
`Justificacion_Metodologica_Comite.md`).

---

*Documento generado 2026-07-14, a pedido explícito del usuario tras confirmar que los cambios de
heterogeneidad y vista dual UPZ/localidad quedaron aplicados: "hazme el flujo completo con la
lógica que correrá el ABM". Complementa a `Diseno_ABM.md`, `Reglas_Negocio_v2_y_Modelado_Agentes.md`
y `Justificacion_Metodologica_Comite.md` sin reemplazarlos.*
