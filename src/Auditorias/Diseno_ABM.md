# Diseño del ABM — Modelo Basado en Agentes de Residuos Sólidos en Bogotá
### Fase 2 del proyecto: de los datos al modelo de simulación
**Autores:** Manuel Gonzalez, Gloria Robledo — CUN, Proyecto de Grado
**Base de datos:** `data/processed/df_modelo.csv` y tablas asociadas (Fase 1, ya cerrada y verificada)
**Fecha de diseño:** 2026-07-08

> Este documento es **solo diseño** — no contiene ni requiere código todavía. El objetivo es
> decidir, con evidencia real de los datos disponibles, qué se puede modelar con rigor, qué hay
> que simplificar honestamente, y qué queda fuera de esta primera versión. La implementación
> (paquete `abm/`) es la fase siguiente, una vez este diseño esté aprobado.

---

## 1. Resumen y alcance de v1

La pregunta de investigación y la hipótesis del "mecanismo triple" (ver notebook, celdas 0-1)
suponen 5 tipos de agentes. Verificamos contra los datos **realmente generados** en la Fase 1
cuáles de esos agentes tienen base empírica y cuáles no:

| Agente declarado | Dato real disponible | Tratamiento en v1 |
|---|---|---|
| Hogares generadores | **Rico**: pirámide demográfica, estrato, `pct_separa_en_fuente`, `clasificacion_social`, por UPZ×año | **Agente conductual completo** |
| Recicladores de oficio | **Delgado**: solo conteo por localidad (RURO) y edad promedio — sin rutas, volumen ni ingresos | **Agente simplificado/estilizado** |
| Operadores/vehículos UAESP | **Nulo**: archivos existen en Drive pero nunca se cargaron al pipeline | **No es agente en v1** — proceso de fondo |
| Puntos limpios/bodegas | **Nulo** (solo un escalar agregado anual para toda la ciudad) | **Índice sintético, no agente pleno** |
| Relleno Sanitario Doña Juana | **Adecuado** como serie agregada anual real | **Sumidero único, sin comportamiento** |

**Principio rector de todo el diseño:** no se le da a un agente más sofisticación conductual de
la que el dato puede sostener o refutar. Un ABM que "aparenta" ser rico en los 5 agentes pero en
realidad está relleno de supuestos sin etiquetar es peor, para efectos de una tesis, que un
modelo honestamente simplificado donde cada supuesto está declarado y es ajustable.

---

## 2. Representación espacial y ambiente

- **112 UPZ como nodos de una red** (`mesa.space.NetworkGrid` sobre un grafo `networkx`), **no**
  geometría fina ni mesa-geo. No existe red vial, direcciones, ni ubicación puntual de
  recicladores o vehículos — modelar movimiento geográfico continuo sería inventar precisión que
  el dato no tiene.
- La red de vecindad entre UPZ se construye **una sola vez**, offline, desde `IndUPZ.gpkg`
  (contigüidad tipo "queen", con la misma lógica de `geopandas` ya usada en `src/geoespacial.py`),
  y se guarda versionada en `data/processed/09_adyacencia_upz.csv` (`upz_origen, upz_vecina`) —
  no se recalcula en cada corrida.
- Cada nodo UPZ mantiene un objeto de ambiente (`EntornoUPZ`, **no** un agente) con los
  atributos ya calculados en `df_modelo`: `estrato_promedio`, `clasificacion_social`,
  `pct_estrato_bajo/medio/alto`, `densidad_poblacional`, `indice_socioeconomico`, `HOGARES`,
  `Total`, más el reciclador asignado (no repetido, ver §3) y el `infraestructura_index`
  sintético (§4).
- `codigo_localidad` se mantiene como atributo de agrupación, porque `pct_separa_en_fuente` y
  el conteo de recicladores **solo son reales a nivel localidad**, no UPZ — esto se declara
  explícitamente como límite de resolución del dato (ver §8), distinto de la red de vecindad
  UPZ que sí es la unidad de simulación.
- Las manzanas (44,260 polígonos) **no se usan** en v1 — son más finas que la resolución real de
  los datos conductuales, y usarlas daría una falsa sensación de precisión. Queda anotado como
  posible extensión de v2 si se quisiera clusterizar hogares dentro de una misma UPZ.

---

## 3. Agentes en alcance: clases, estado y lógica de `step()`

### `HogarAgente`
**Granularidad de población (decisión de esta sesión):** ni 3 cohortes agregadas por estrato
(muy simplificado) ni un agente por cada hogar real (~2.7 millones en Bogotá — inviable para una
simulación diaria de varios años en el tiempo de una tesis). Se usa una **muestra representativa
de hogares reales por UPZ×estrato**: agentes individuales (no cohortes agregadas), tomados como
una fracción del total real de `HOGARES` × `pct_estrato_x` de cada UPZ, cada uno con un **peso
de escalamiento** (`factor_escala = hogares_reales_upz_estrato / agentes_muestreados`) para que
cualquier suma/promedio del modelo se extrapole a la población total real.

> **Nota sobre el porcentaje de muestreo:** en la conversación se mencionó como referencia un
> muestreo de ~30% de la realidad. Con ~2.7 millones de hogares en Bogotá, un 30% son ~810,000
> agentes — computacionalmente inviable para una simulación diaria (`mesa` con cientos de miles
> de agentes × 365 días × varios años excede ampliamente lo razonable para el cronograma de una
> tesis). Se recomienda un **muestreo mucho menor (2-5%)** con el mismo peso de escalamiento —
> matemáticamente equivalente en los agregados que reporta el modelo, pero factible de correr.
> Este porcentaje queda como **parámetro configurable** (`config_abm.FRACCION_MUESTREO_HOGARES`)
> para que se pueda subir si el desempeño lo permite, sin rediseñar el modelo.

**Estado:**
- `upz`, `estrato` (1-6), `factor_escala`
- `prob_separa_base` = `prob_separa` (dato de localidad, ver limitación en §8), ponderado por
  `n_encuestas` de `05_actores.csv` como indicador de confianza (Los Mártires n=1, Santa Fe n=3
  deben marcarse como poco confiables)
- `pct_calidad_separacion` (factor de contaminación/calidad de lo separado)
- `prob_separa_actual` (dinámico, arranca en `prob_separa_base`)
- `percepcion_impacto` (variable latente 0-1, motor del mecanismo de free-riding)
- `generacion_diaria` (derivada de población representada × `RESIDUOS_PER_CAPITA_TON_ANIO`/365)

**Lógica de `step()` (prosa):** cada día, el hogar genera `generacion_diaria` de residuos. Su
tasa de separación *efectiva* se modula hacia abajo por el `infraestructura_index` de su UPZ
(un hogar dispuesto a separar pero sin acceso a un punto limpio, separa menos en la práctica).
En una cadencia más lenta (semanal/mensual, no diaria — las actitudes no cambian de un día a
otro), el hogar actualiza `prob_separa_actual` observando la tasa de separación promedio reciente
de sus vecinos de red del mismo estrato, combinada con su propia `percepcion_impacto` (que es
genuinamente pequeña para cualquier hogar individual frente al total de la ciudad). Si el entorno
es de baja participación y el hogar percibe su aporte como irrelevante, `prob_separa_actual`
decae hacia un piso bajo (operacionalizando el "mi separación no importa" del mecanismo #1). Si
los vecinos mejoran o la infraestructura mejora, se recupera. Esto permite que zonas de estrato
bajo caigan en un equilibrio de baja separación auto-reforzado — el mecanismo que plantea la
hipótesis — como resultado **emergente** de la red social, no como un número fijo por UPZ.

### `PoblacionRecicladoresUPZ` (una por UPZ)
**Estado:**
- `n_recicladores_upz` = conteo RURO de la localidad **asignado** a esta UPZ por participación
  poblacional (no el valor repetido tal cual — usarlo directo infla el total de recicladores de
  la localidad entre 6 y 9 veces, según cuántas UPZ tenga esa localidad)
- `edad_promedio_reciclador` (único diferenciador real, modificador menor de eficiencia)
- `capacidad_recoleccion_individual` (**parámetro libre de calibración**, kg/día — las reglas
  RN020-022 de productividad están todas "Pendiente" en `03_reglas_negocio.csv`, sin valor real)

**Lógica de `step()` (prosa):** cada día, la capacidad total de recicladores de la UPZ compite,
**simultáneamente y sin coordinación**, con el proceso de fondo de recolección formal (§4) por
el mismo material ya separado por los hogares. Se resuelve con una regla simple de reparto
proporcional si la demanda combinada excede el material disponible. Esta competencia sin
coordinación es la operacionalización directa del mecanismo #2 de la hipótesis — no se inventa
un mercado negociado que en la realidad tampoco existe. Sin movimiento entre UPZ en v1 (no hay
datos de rutas): cada población de recicladores opera solo en su UPZ de origen.

### `EntornoUPZ` (objeto de ambiente, no agente)
Atributos estáticos anuales de `df_modelo` + `infraestructura_index` sintético (§4) +
`material_pool_disponible` (se llena y limpia cada paso) + acumuladores de
`aprovechado`/`rechazo` para el balance de masa.

### `RellenoSanitarioDJ`
Acumulador único que recibe todo lo no separado ni recuperado informalmente. Se usa solo para
verificar el balance de masa anual contra la serie real (`residuos_pidj`) — no toma decisiones.

---

## 4. Los dos tipos de agente sin datos: qué hacer con ellos

**Operadores/vehículos UAESP → no se modelan como agente en v1.** Se representan como un
**proceso de fondo de capacidad no vinculante**: siempre recogen lo que no fue separado ni
recuperado informalmente, sin restricción de capacidad. Se pierde la posibilidad de que la
logística formal sea un cuello de botella independiente, pero (a) ninguna regla de negocio
relevante tiene valor real (capacidad de camión, viajes/día — todas "Pendiente"), (b) no es uno
de los 3 mecanismos nombrados en la hipótesis, y (c) la cobertura formal de recolección en
Bogotá es históricamente casi universal, así que asumir que no es el cuello de botella es
razonable. Se deja una clase stub documentada (`OperadorUAESP`, sin instanciar) para cuando se
integren `03_recoleccion_por_concesionario.csv` y la carpeta RBL al pipeline (hoy nunca cargados).

**Puntos limpios/bodegas → sí se representa, con un índice sintético.** A diferencia del caso
anterior, aquí se recomienda **no omitir**: este mecanismo es un tercio de la hipótesis, y
omitirlo dejaría al modelo sin ninguna forma de hablar de él, debilitando el argumento central
de la tesis desde el diseño mismo. Se construye un `infraestructura_index_upz` (0-1) como función
de `pct_estrato_bajo` y `densidad_poblacional` (UPZ más pobres y densas, asumidas con menor
cobertura — un supuesto **consistente con la hipótesis pero no verificado**), etiquetado como
SINTÉTICO en código, configuración y en el texto de la tesis. Se usa como (a) modulador de la
separación efectiva de los hogares y de la eficiencia de los recicladores, y (b) palanca de
escenario (subirlo/bajarlo para simular inversión en infraestructura). El único dato real
(`rechazo_punto_limpio` = 46,209 ton/año, agregado ciudad) se usa solo como chequeo de orden de
magnitud, nunca como verdad espacial.

---

## 5. Calendario de simulación (scheduler)

- **Paso diario** (coincide con la granularidad nativa de `ton_recolectadas_estim_dia`), en
  bloques de 365 días por año simulado. Los atributos anuales de `df_modelo` (estrato,
  población) se congelan dentro de un año y solo cambian en el corte de año si se simulan varios
  años (2018-2024).
- **Dos velocidades de dinámica:** el flujo de material (separación → recolección → reparto del
  pool) se recalcula **cada día**; la actualización de actitudes/efecto de imitación
  (`prob_separa_actual`) se recalcula en cadencia más lenta (semanal o mensual) — las actitudes
  reales no cambian de un día para otro, y actualizarlas a diario solo agregaría ruido.
- **Orden de activación:** hogares deciden primero, luego recicladores y sumidero formal compiten
  por lo generado — con orden aleatorio *dentro* de cada grupo para no introducir sesgo por el
  orden fijo de las UPZ.
- **KPI de reconciliación:** el % de aprovechamiento anual = Σ(aprovechado diario) /
  Σ(generado diario) sobre los 365 pasos — así se compara contra el ground truth anual real
  (48.50%, 2025, OAB) sin mezclar granularidades.

> **⚠️ Nota de actualización (2026-07-11):** el valor de referencia 48.50% (2025) citado en esta
> sección quedó **superado** — ver `Investigacion_Salto_Aprovechamiento.md`. Es la salida de un
> modelo econométrico de la UAESP, no una medición directa, y presenta un salto no explicado de
> 18.56% (2023) a 43.88% (2024) que coincide con un cambio regulatorio real (Decreto 1381/2024,
> nuevo PGIRS 2024-2028). El ground truth de calibración vigente ahora es **18.56% (2023)**
> (`config.APROVECHAMIENTO_GROUND_TRUTH_PCT`). El texto original de esta sección se conserva sin
> reescribir para mantener trazabilidad de que la decisión cambió en este punto.

---

## 6. Plan de calibración y validación
*(documentado ahora; se implementa en la iteración posterior al MVP, no en el primer corte)*

- **Fijo desde el dato (sin calibrar):** todos los atributos demográficos/estrato,
  `pct_separa_en_fuente`/`pct_calidad_separacion` base (marcados de baja confianza donde la
  muestra de encuesta es minúscula), el conteo de recicladores asignado, y
  `RESIDUOS_PER_CAPITA_TON_ANIO` = 0.35 *(corregido 2026-07-11, derivado de dato real —
  antes 0.28, ver `src/config.py`)*.
- **Parámetros libres/calibrables:** `capacidad_recoleccion_individual` de recicladores, las
  tasas de decaimiento/recuperación del efecto de imitación, el umbral de "percepción de
  impacto", los coeficientes del `infraestructura_index_upz` (100% sintético), y la regla de
  reparto del pool de material.
- **Objetivo de calibración:** único, a nivel ciudad, **48.50% (2025, OAB)** *(⚠️ superado —
  ver nota de actualización arriba; el objetivo vigente es 18.56%, 2023)* — no existe ground
  truth real a nivel UPZ, así que cualquier lectura UPZ del modelo es **descriptiva/direccional**
  ("el modelo produce menor aprovechamiento en UPZ de estrato bajo, consistente con la dirección
  de la hipótesis"), nunca un ajuste cuantitativo validado.
- **No forzar el quiebre 2023→2024** (18.56%→43.88%) en la calibración — el propio notebook ya
  señala que ese salto no lo explica la hipótesis del mecanismo triple por sí sola y puede
  deberse a una intervención de política/infraestructura externa. Se documenta como limitación,
  no se fuerza vía parámetros artificialmente altos. *(Esta observación resultó ser la pista
  correcta: la investigación posterior confirmó que el salto es un quiebre metodológico/regulatorio,
  no una tendencia real — por eso 2023 y no 2025 es ahora el objetivo de calibración.)*
- **Chequeos adicionales más allá de ajustar el número:**
  1. Balance de masa: generación ≈ aprovechado + rechazo + dispuesto en Doña Juana, contra
     `residuos_pidj`/`rechazo_punto_limpio` reales (orden de magnitud).
  2. Barridos de sensibilidad uno-a-la-vez: el aprovechamiento debe moverse en la dirección
     esperada al variar `infraestructura_index`, separación base, e intensidad de competencia.
  3. Réplica histórica de baja prioridad: con los insumos de 2018-2023 (antes del quiebre), el
     modelo debería quedarse aproximadamente en la banda histórica 15-20% sin recalibrar — una
     señal de alerta si se aleja mucho, aunque no es el objetivo principal.
  4. Con ~4-6 parámetros libres contra un solo número real, la calibración está subdeterminada:
     se debe reportar un **rango de combinaciones de parámetros plausibles** que cumplan el
     objetivo y los chequeos anteriores, no un único "mejor ajuste".
  5. Comparaciones de escenario (inversión en infraestructura, mejora de coordinación, etc.)
     como cambios relativos frente a la línea base calibrada, con múltiples réplicas
     (≥30 corridas con semillas distintas) reportadas como media ± dispersión.

---

## 7. Estructura de archivos propuesta (para la implementación futura)

> **⚠️ Nota (2026-07-11):** este árbol es el plan ORIGINAL, previo a la implementación — se
> conserva sin reescribir por trazabilidad. El estado REAL de cada pieza (qué se implementó, qué
> cambió respecto al plan, ej. `calibracion.py` ya existe y está calibrado, `agentes_infraestructura.py`
> ya no es sintético) está en la tabla de estado de `Reglas_Negocio_v2_y_Modelado_Agentes.md`
> ("Implementación completa del ABM con datos reales") y en `Investigacion_Salto_Aprovechamiento.md` §7.

```
EDA + ABM Residuos Bogota/
├── abm/                              ← paquete nuevo, hermano de src/ (abm/ lee de src/ y
│                                        data/processed/, nunca al revés)
│   ├── __init__.py
│   ├── config_abm.py                 ← parámetros libres, rangos plausibles, semillas,
│   │                                    FRACCION_MUESTREO_HOGARES (separado de src/config.py)
│   ├── entorno.py                    ← red de 112 UPZ, EntornoUPZ, carga de adyacencia
│   ├── agentes_hogar.py              ← HogarAgente
│   ├── agentes_reciclador.py         ← PoblacionRecicladoresUPZ
│   ├── agentes_infraestructura.py    ← infraestructura_index sintético + stub OperadorUAESP (v2)
│   ├── modelo.py                     ← ModeloResiduosBogota(mesa.Model): setup, step, colectores
│   │
│   │   --- todo lo de abajo es POST-MVP, no en el primer corte ---
│   ├── calibracion.py                ← rutina de calibración contra 48.5%
│   ├── escenarios.py                 ← define/llena 07_escenarios.csv, corridas batch
│   └── validaciones_abm.py           ← balance de masa, sensibilidad, réplica histórica
├── notebooks/
│   └── ABM_Simulacion_Residuos_Bogota.ipynb  ← notebook nuevo; el notebook de EDA queda
│                                                intacto como Fase 1 cerrada
└── data/processed/
    ├── 09_adyacencia_upz.csv         ← red de vecindad UPZ (generada una vez, versionada)
    ├── 10_resultados_abm_baseline.csv
    └── 11_resultados_abm_escenarios.csv
```

**Alcance del MVP (decisión de esta sesión):** el primer corte implementable incluye solo
`agentes_hogar.py`, `agentes_reciclador.py`, `agentes_infraestructura.py`, `entorno.py` y
`modelo.py` — corriendo un año completo y devolviendo un % de aprovechamiento agregado. Los
módulos `calibracion.py`, `escenarios.py` y `validaciones_abm.py` **no se escriben en el MVP**;
quedan para la iteración siguiente, una vez se confirme que el modelo base corre y sus resultados
tienen sentido de orden de magnitud.

---

## 8. Riesgos y límites a declarar explícitamente

- **API de `mesa`:** la versión actual instalable (3.x) usa `model.agents` (AgentSet) en vez de
  `mesa.time.RandomActivation`, distinto de la mayoría de tutoriales en internet (mesa 2.x) —
  diseñar directamente contra 3.x, no copiar patrones de tutoriales viejos.
- **Resolución localidad vs. UPZ:** `pct_separa_en_fuente`, `pct_calidad_separacion` y el conteo
  de recicladores son reales **a nivel localidad**, simplemente repetidos/asignados a las UPZ que
  la componen. Cualquier variación UPZ-a-UPZ que muestre el modelo en estas variables viene de la
  ponderación demográfica/de estrato aplicada encima, no de una diferencia observada realmente
  entre esas UPZ. Esto debe ser una limitación destacada, no una nota al pie, en cualquier mapa o
  gráfico del modelo que toque estas variables.
- **Muestras de encuesta minúsculas:** Los Mártires (n=1) y Santa Fe (n=3) sostienen un
  parámetro de localidad completo — se recomienda marcarlas explícitamente como poco confiables
  en cualquier tabla o gráfico, o aplicar un encogimiento hacia el promedio de la ciudad.
- **Sin modelado de tipo de material:** el residuo se trata como una masa homogénea en v1; se
  puede conectar opcionalmente `04_composicion_residuos.csv` (composición real anual, ciudad) como
  un techo agregado (ej. "máximo teóricamente aprovechable"), para que el modelo no pueda mostrar
  un 100% de aprovechamiento aunque el free-riding desapareciera del todo.
- **Riesgo de doble conteo:** usar el conteo de recicladores por localidad directo en cada UPZ
  sin repartir infla el total real entre 6 y 9 veces — debe implementarse la asignación
  proporcional descrita en §3, no un `merge` directo.
- **Sin validación real bajo el nivel de ciudad** — se declara como límite desde el diseño, no
  se descubre después.
- **Identificabilidad:** ~4-6 parámetros libres contra un solo número real de calibración — se
  reporta un rango de parámetros, no un ajuste único (ver §6). *(⚠️ Confirmado empíricamente,
  2026-07-11: al calibrar contra los 6 puntos reales 2018-2023, 4 de los 5 parámetros libres
  dieron el mismo error sin importar su valor — solo el parámetro de "brecha intención-acción"
  mueve el ajuste. Ver `Investigacion_Salto_Aprovechamiento.md` §7.6, ya no es solo una
  advertencia teórica.)*
- **Reproducibilidad:** fijar y reportar semillas de aleatoriedad; correr múltiples réplicas por
  escenario dado que hay componentes estocásticos (imitación social, reparto del pool).
- **El texto original del notebook** (celda 0) promete para los recicladores "rutas, volumen
  recogido, ingresos, interacción con hogares" — la verificación de esta fase confirma que nada
  de eso existe en los datos procesados. Se recomienda ajustar esa redacción antes de la
  sustentación, para que el texto de la tesis no prometa un detalle que la implementación no
  puede entregar.

---

## 9. Corrección pendiente antes de implementar (no parte de este diseño)

`src/config.py` tiene actualmente `APROVECHAMIENTO_GROUND_TRUTH_PCT = None` como valor estático;
el 48.50 real solo se fija en vivo dentro de una celda del notebook de EDA (no se persiste en el
archivo). Antes de que el paquete `abm/` importe esta constante, hay que fijarla explícitamente
en `src/config.py` (`APROVECHAMIENTO_GROUND_TRUTH_PCT = 48.50  # 2025, OAB`) — de lo contrario
cualquier script que importe `config` en frío (sin haber corrido esa celda del notebook primero)
recibirá `None`.

---

**⚠️ Nota de actualización 4 (2026-07-14):** el límite de "Resolución localidad vs. UPZ" de §8 se
desarrolla a fondo, con tabla de granularidad de TODAS las fuentes (no solo comportamiento) y
justificación explícita de por qué no se migra a localidad ni a manzana, en
`Justificacion_Metodologica_Comite.md` — documento nuevo, escrito para responder directamente las
preguntas de un comité sobre unidad espacial, origen de parámetros y heterogeneidad. El dashboard
(`abm/dashboard.py`) ahora incluye un selector "UPZ / Localidad" en el mapa principal y el
ranking, para mostrar explícitamente ambas resoluciones en vez de solo la heredada.

**⚠️ Nota de actualización 5 (2026-07-14, mismo día — ronda 5):** el límite anterior sobre
comportamiento ("`pct_separa_en_fuente` real solo a localidad, UPZ lo hereda") queda **resuelto**
para el canal principal: se encontró que EM2021 trae geografía UPZ real (`COD_UPZ_GRUPO`, nunca
antes extraída) — 112 de 112 UPZ cubiertas, 600+ hogares de muestra cada una. `prob_separa` ya no
se hereda de localidad, se mide por UPZ. Se recalibró el modelo completo con la nueva fuente. Ver
`Justificacion_Metodologica_Comite.md` §5bis para el detalle completo (crosswalk, verificación,
RMSE resultante).

---

*Fin del diseño. Este documento no crea código ni modifica el notebook o los datos de la Fase 1
— es la base para la siguiente conversación, donde se implementa el MVP descrito en §7.*
