# Justificación Metodológica para Comité — Resolución Espacial, Origen de Parámetros y Heterogeneidad

### Documento único de referencia: de dónde sale cada número que hay que poder defender

---

## 0. Propósito de este documento

Este documento no reemplaza a `Diseno_ABM.md`, `Reglas_Negocio_v2_y_Modelado_Agentes.md` ni
`Investigacion_Salto_Aprovechamiento.md` — los referencia y **conecta explícitamente** hallazgos
que hoy viven dispersos entre esos tres documentos y comentarios de código, para que exista un
solo lugar que responda, con evidencia citada, las preguntas que un comité de tesis de posgrado
va a hacer:

1. ¿Por qué UPZ y no localidad, o no hogar individual?
2. ¿De dónde sale cada beta/parámetro del modelo?
3. ¿Cómo se calibró el modelo y contra qué?
4. ¿Cómo se calculó la sensibilidad de parámetros, y por qué ese método?
5. ¿Qué representa exactamente un "agente" en este ABM, y en qué se parece y en qué NO se parece
   a un ABM de referencia como MATSim?

Motivado por una auditoría de fondo pedida explícitamente el 2026-07-14, después de que el
usuario compartiera el caso de MATSim (Zúrich) como estándar de rigor y preguntara directamente
si UPZ fue la unidad espacial correcta.

---

> **⚠️ Nota de actualización (2026-07-14, ronda 5 — el mismo día, más tarde):** el hallazgo
> central de este documento (§2: "UPZ NO es la unidad de medición real para comportamiento")
> quedó **resuelto para el canal principal**. El usuario compartió el diccionario completo de
> EM2021 y se encontró que trae `COD_UPZ_GRUPO`/`NOMBRE_UPZ_GRUPO` — geografía real a nivel UPZ
> (o grupo de 2-4 UPZ fusionadas por diseño muestral), nunca antes extraída. Verificado: **112 de
> 112 UPZ reales cubiertas**, cada una con 600-1,300+ hogares de muestra (`NHCCP38`, EM2021,
> ponderado por `FEX_C`) — comparado con ECA2021, real solo a localidad (20), con localidades
> sostenidas por 1 o 3 encuestas (Los Mártires, Santa Fe). `prob_separa` ahora se construye desde
> esta fuente (`abm/datos_reales.py::construir_o_cargar_separacion_upz_em2021`), reemplazando el
> valor heredado de localidad. El razonamiento original de §1/§2 se conserva abajo sin reescribir
> (fue correcto en su momento y explica por qué se buscó esta fuente), pero las tablas y
> conclusiones se actualizaron para reflejar el estado real vigente — ver §5bis para el detalle
> completo de la fuente nueva, el crosswalk, y la recalibración resultante.

---

## 1. Granularidad real de cada fuente de datos

UPZ (112 unidades) es la unidad de trabajo del ABM, pero **no es la resolución real de todas las
fuentes que alimentan el modelo** — cada una tiene su propio techo de finura, y usar UPZ en todas
partes por defecto puede sobre- o sub-representar la precisión real del dato, según la fuente:

| Fuente | Granularidad real EN EL ORIGEN | Techo de finura real del proyecto | Uso en el pipeline |
|---|---|---|---|
| Manzanas con estrato (`manzanaestratificacion.gpkg`) | **Manzana** (44,260 polígonos) | Sí, la más fina de todo el proyecto | Colapsada a UPZ a propósito (ver §2) |
| Población/hogares (DANE, proyección UPZ) | **UPZ** | Sí, es el nivel en que el DANE publica esta cifra | Usada tal cual |
| Encuesta Multipropósito (EM2021, socioeconómica, ~234,000 hogares/107,119 hogares únicos) | Microdato de hogar individual. Geografía utilizable: **UPZ real** (vía `COD_UPZ_GRUPO`, 112/112 UPZ cubiertas, ver §5bis) para separación (`NHCCP38`); **localidad** (20) para participación comunitaria/vivienda/informalidad (`NPCJP1F/I`, `NVCBP10`, `OINFORMAL` — no traen geografía UPZ útil) | **Sí, para separación** (desde 2026-07-14) — es ahora la fuente MÁS FINA de comportamiento de todo el proyecto | `prob_separa` (nivel UPZ, ver §5bis — reemplaza a ECA2021); `pct_participacion_comunitaria`, `pct_vivienda_propia`, `pct_informal` (nivel localidad, ver §5) |
| Encuesta de Cultura Ambiental (ECA2021, ~2,282 personas) | Microdato individual, geografía utilizable = **localidad** (20, algunas con n=1/n=3) | No | **Legado** — usada hasta 2026-07-13 para `prob_separa`; reemplazada por EM2021/UPZ (ver §5bis). Se conserva `05_actores.csv` sin tocar, por trazabilidad, pero ya no alimenta el modelo activo |
| RURO (recicladores de oficio) | **Localidad** (columna `LOCALIDAD VIVIENDA`, sin dirección) | No | Repartido a UPZ proporcional a población (supuesto declarado, no medición) |
| RBL consolidado (recolección formal) | **Ninguna geografía** — solo operador/ASE y mes, a nivel ciudad | No aplica | Techo agregado de ciudad, igual para todas las UPZ que atiende cada ASE |
| SIGAB (puntos críticos, contenedores, grandes generadores) | **Punto real** (lat/lon) | Sí — es la fuente puntual más precisa de todo el proyecto | Agregada a conteo por UPZ (podría explotarse más fino, no se hace hoy) |
| Macrorutas UAESP | Polígono real por zona operativa | Sí | Solo usada como tabla de equivalencia nombre→localidad, geometría no explotada |
| VIAT, subsidios por estrato (CRA) | Tarifa normativa, sin geografía propia | No aplica | Aplicada por composición de estrato de cada UPZ |

**Conclusión (actualizada 2026-07-14):** UPZ es ahora la resolución real de comportamiento
también, gracias a EM2021 (§5bis) — ya no es una unidad heredada de localidad para esa variable.
Sigue siendo cierto que UPZ se queda corta frente a la fuente más fina del proyecto (manzana, que
se descarta a propósito por la misma razón de siempre: ninguna variable conductual tiene dato a
esa resolución, ver §2) y que participación comunitaria/vivienda/informalidad (EM2021, pero sin
`COD_UPZ_GRUPO` útil para esas preguntas específicas) siguen siendo reales solo a localidad.

---

## 2. Por qué UPZ, con sus límites declarados explícitamente

**UPZ es la unidad correcta para infraestructura y demografía** (dato real por UPZ o por punto,
agregable a UPZ sin pérdida) — este uso ya está bien fundamentado y documentado en
`Diseno_ABM.md` §2.

**Historia (hasta 2026-07-13) — por qué se buscó esta fuente.** `prob_separa_base` — el parámetro
que más mueve el modelo — venía de ECA2021, real solo a **localidad** (20 unidades, algunas con
muestra de 1 o 3 encuestas tras excluir los casos degenerados). Cuando el modelo asignaba un valor
de `prob_separa` a cada una de las 112 UPZ, **heredaba** el valor de su localidad padre — no lo
medía de forma independiente. Un ranking o mapa por UPZ del % de aprovechamiento aparentaba 112
mediciones de comportamiento independientes, cuando en realidad eran ~20 valores reales repetidos
hacia las UPZ que pertenecen a cada localidad.

**Estado vigente (desde 2026-07-14, ver §5bis).** `prob_separa` ahora viene de EM2021
(`NHCCP38`, "¿este hogar clasifica los residuos?"), agregado a nivel **UPZ real** vía
`COD_UPZ_GRUPO` — 112 de 112 UPZ cubiertas, cada una con 600-1,300+ hogares de muestra propia (no
heredada). Un ranking o mapa por UPZ del % de aprovechamiento ahora SÍ refleja 112 mediciones de
comportamiento independientes. La variación entre UPZ de una misma localidad ya no viene solo de
infraestructura/estrato — también hay variación conductual real medida.

Sigue sin migrarse a hogar individual (no existe geolocalización de hogares reales en Bogotá para
este proyecto). El dashboard mantiene el selector "UPZ / Localidad" del panel "Panorama en vivo"
(`abm/dashboard.py::_agregar_por_localidad`) — ya no porque el comportamiento sea heredado, sino
porque sigue siendo una vista útil de agregación (participación comunitaria/vivienda/informalidad,
que sí siguen siendo reales solo a localidad, y para comparar contra la serie histórica de
`05_actores.csv`, que queda como referencia legada).

¿Por qué no usar manzana (la fuente más fina real, 44,260 polígonos con estrato)? Porque el
comportamiento no tiene ningún dato a esa resolución — usar manzana solo para geometría, con un
`prob_separa` heredado de una localidad de 20, sería una falsa sensación de precisión aún mayor
que la de UPZ. `Diseno_ABM.md` §2 ya declara esto explícitamente y no se repite aquí.

---

## 3. De dónde sale cada parámetro del ABM

| Parámetro | Categoría | Evidencia |
|---|---|---|
| `PROB_SEPARA_PISO=0.4399` | **Real** (actualizado 2026-07-14) | Mínimo real observado de `pct_separa_upz` (EM2021, UPZ 95 Las Cruces, n=939 hogares) entre las 112 UPZ reales — ya no hace falta excluir muestras degeneradas, el mínimo real de EM2021 viene de una UPZ con muestra sólida. Antes: 0.5916 (ECA2021, Kennedy n=191, con Los Mártires n=1/Santa Fe n=3 excluidas por degeneradas) — ver §5bis |
| `VIAT_PESOS_POR_TONELADA`, `FACTOR_SUBSIDIO_POR_ESTRATO` | **Real** | Tarifa oficial CRA / Ciudad Limpia, dic-2025 |
| `ODDS_RATIO_PARTICIPACION_COMUNITARIA=2.48` | **Real** | Promedio de 2 odds ratios de una regresión logística multivariada ponderada sobre EM2021 (JAC=2.63, ambiental=2.33), Sección 8/9 del EDA — ver §5 |
| `ODDS_RATIO_VIVIENDA_PROPIA=1.40`, `ODDS_RATIO_INFORMAL=0.85` | **Real** | Misma regresión, agregados 2026-07-14 — ver §5 |
| `BETA_DECAIMIENTO_SEPARACION=0.02`, `UMBRAL_PERCEPCION_IMPACTO=0.07`, `FACTOR_BRECHA_INTENCION_ACCION=0.63` | **Calibrado** (recalibrado 2026-07-14, ronda 5) | Búsqueda en rejilla de 3 etapas contra la serie real UAESP 2018-2023, confirmada a resolución completa — RMSE=1.1961pp, ver §5bis. `data/processed/24_sensibilidad_parametros.csv` queda como referencia de la calibración ANTERIOR (ECA2021/localidad) — no se regeneró para esta ronda, pendiente como trabajo futuro |
| `BETA_RECUPERACION_SEPARACION=0.02` | **Calibrado, pero sin efecto medible** | Rango de RMSE al variarlo en la rejilla: 0.000pp — se conserva en su valor de partida porque no hay ninguna combinación de la rejilla que lo distinga de otro valor. No es un bug, es una limitación de identificabilidad honesta (ver §4) |
| `FRACCION_MUESTREO_HOGARES=0.03`, `CADA_CUANTOS_DIAS_ACTUALIZA_ACTITUD=7`, `CAPACIDAD_RECOLECCION_KG_DIA_POR_RECICLADOR=15.0` | **Arbitrario, acotado** | Sin dato real directo. `CAPACIDAD_RECOLECCION...` está acotado por orden de magnitud (15 kg/día × recicladores activos ≈ 7% del RBL formal, un valor implausible se saldría de ese rango) — los otros dos son decisiones de cómputo/cadencia sin sustento empírico, declaradas como supuestos, no como hallazgos |
| `log_ingreso` (EM2021, `NPCKP23`) | **Probado y descartado** | OR≈1.00-1.01, p=0.33 — no significativo, no se incluye en el modelo. Es una decisión de rigor, no un hueco |

---

## 4. Metodología de calibración, sin eufemismos

**Objetivo**: `SERIE_REAL_PCT_APROVECHAMIENTO` 2018-2023 (`abm/calibracion.py`), reconciliada de
`Residuos generados bogota.xlsx`. **Advertencia que hay que decir en voz alta ante un comité**:
esa serie **no es una medición física** (no es una báscula pesando residuos) — es la salida de un
modelo macro econométrico propio de la UAESP (ver `Investigacion_Salto_Aprovechamiento.md` §1).
Es decir: **se está calibrando un modelo contra la estimación de otro modelo**, no contra ground
truth. Esto es una práctica aceptada en investigación aplicada cuando no existe una medición
física mejor disponible — pero se declara así, explícitamente, en vez de dejar que se lea como
una validación contra dato duro.

**Método**: búsqueda EXHAUSTIVA en rejilla (`itertools.product`, no un optimizador de caja
negra), 2 etapas (gruesa → fina), 80 combinaciones totales sobre 4 parámetros libres, a
resolución reducida por tractabilidad (90 días/año, 1% de muestreo) con confirmación final a
resolución completa (365 días, 3% de muestreo). 2018 es año-ancla (no se calibra contra él, no
hay año anterior del cual heredar estado); se calibra contra las 5 transiciones reales 2019-2023.
Métrica: RMSE en puntos porcentuales. Resultado confirmado a resolución completa: **RMSE≈1.15pp**
(recalibrado 2026-07-13 tras corregir 2 bugs reales de mecanismo, ver
`Investigacion_Salto_Aprovechamiento.md` §8; re-confirmado 2026-07-14 tras agregar heterogeneidad
real de hogar, ver §5 y §6 de este documento).

Con solo 6 puntos reales y 4 parámetros libres, el problema es formalmente subdeterminado — se
reporta el ranking completo de combinaciones plausibles, no "el" óptimo falso (ver
`Diseno_ABM.md` §8 y `data/processed/24_sensibilidad_parametros.csv`).

---

## 5. Heterogeneidad real dentro de cada cohorte (agregado 2026-07-14)

La Sección 8/9 del EDA (`EDA_Dirigido_Fase3.ipynb`) corrió una regresión logística multivariada
ponderada (por `FEX_C`, factor de expansión de la encuesta; n=60,235 hogares en la muestra,
representando 2,061,804 hogares-equivalentes reales; McFadden Pseudo R²=0.055) con 6 predictores
de si un hogar separa residuos, controlando todos entre sí:

| Variable | Odds ratio (ponderado) | Significativo | ¿Conectado al ABM? |
|---|---|---|---|
| Participación en JAC | 2.63 | Sí | Sí (promediado con ambiental → 2.48) |
| Participación en organización ambiental | 2.33 | Sí | Sí (idem) |
| Vivienda propia (`NVCBP10==1`, "Casa" — proxy de tenencia usado en el EDA, no la variable legal) | 1.40 | Sí | **Sí, agregado 2026-07-14** |
| Estrato | 1.37 | Sí | Estructural (los agentes ya están segmentados por estrato) |
| Personas por hogar | 1.13 | Sí | No — continua, requiere una forma de aplicación más delicada, documentado como trabajo futuro |
| Educación | 1.13 | Sí | No — idem |
| Informalidad laboral (`OINFORMAL`) | 0.85 | Sí, dirección negativa | **Sí, agregado 2026-07-14** |
| Ingreso (log) | 1.00-1.01 | **No** (p=0.33) | No — probado y descartado (ver §3) |

Hasta 2026-07-14, el ABM solo usaba 1 de estos 6 predictores reales y significativos
(participación comunitaria). Dentro de una misma cohorte UPZ×estrato, todos los agentes
arrancaban con `prob_separa_base` prácticamente idéntico — la causa técnica exacta de que "todos
los hogares se comporten igual" dentro de una UPZ.

### Cómo se conectó (y un hallazgo de diseño encontrado al verificar, no asumido)

**Primer intento (descartado tras verificar)**: aplicar los odds ratios de vivienda propia e
informalidad directamente sobre `prob_separa_base` de cada agente —igual que ya hacía
participación comunitaria— y corregir el promedio ponderado de la cohorte de vuelta al valor
calibrado. Al verificar numéricamente (re-correr la serie 2018-2023 a resolución completa), el
RMSE subió de 1.15pp a **4.25pp**, con una divergencia sistemática (la trayectoria simulada bajaba
año a año mientras la real sube). Causa raíz: `prob_separa_base` también gobierna el disparador
de decaimiento por imitación/free-riding (`agentes_hogar.py::actualizar_actitud_separacion`), una
regla NO LINEAL (un umbral). Agregar varianza a `prob_separa_base` —aunque se preserve su
promedio exacto— cambia cuántos agentes cruzan el umbral, lo cual sí mueve la dinámica agregada
aunque el nivel inicial no se haya movido. Es un efecto real de varianza sobre una regla no
lineal, no un error de aritmética.

**Diseño final (verificado, RMSE re-confirmado)**: la heterogeneidad de vivienda propia e
informalidad se aplica como un **multiplicador de salida separado**
(`factor_heterogeneidad_hogar`, `abm/agentes_hogar.py`), normalizado por cohorte para que su
promedio ponderado por población sea exactamente 1.0
(`agentes_hogar.normalizar_factor_heterogeneidad`). El mecanismo de decaimiento/recuperación
calibrado queda **intacto**, operando sobre el `prob_separa_base` uniforme de la cohorte, exactamente
como en la calibración confirmada — la heterogeneidad real solo determina cuánto material separa
CADA hogar en su salida diaria (`step()`), no la dinámica agregada de actitud. Verificado
numéricamente: 0 de 75,273 agentes activa el clip de seguridad (`prob_efectiva` no puede superar
1.0); el promedio ponderado del factor es exactamente 1.0 en las 199 cohortes con más de 1
agente; la dispersión real del factor dentro de cohorte tiene una desviación estándar promedio de
0.079 (heterogeneidad genuina, antes era ~0).

### Corrección adicional encontrada en el camino (documentada, no escondida)

`abm/datos_reales.py::construir_o_cargar_participacion_comunitaria()` promediaba la muestra
CRUDA de EM2021 sin ponderar por `FEX_C`, pese a que la Sección 8bis del EDA ya había demostrado
que la muestra sin ponderar sobrerrepresenta personas muy participativas. Corregido 2026-07-14
para ponderar igual que la nueva función de vivienda/informalidad — el efecto es pequeño (la
tasa de participación real es baja, ~0.4% ponderado vs. ~0.8% crudo) y no afecta materialmente el
resultado agregado, pero es la cifra correcta de citar.

---

## 5bis. Separación en la fuente a nivel UPZ real (EM2021) — reemplaza a ECA2021/localidad (2026-07-14)

El usuario compartió el diccionario completo de EM2021 (todas las secciones: vivienda, hogar,
pago de servicios, persona) y pidió validar si el proyecto aprovechaba al máximo cada fuente
disponible, específicamente preguntando si EM2021 se podía desagregar por UPZ. Se encontró que
sí: `COD_UPZ_GRUPO`/`NOMBRE_UPZ_GRUPO` existen en `em2021.csv` desde siempre y nunca se habían
extraído (no estaban en `COLUMNAS_MULTIPROPOSITO`).

**Verificación de calidad del dato (no especulativa, sobre el archivo crudo de 1.2GB, 292,281
filas, 107,119 hogares únicos por `DIRECTORIO_HOG`):**
- `FEX_C` y `COD_UPZ_GRUPO` son constantes dentro de un mismo hogar (0 excepciones) — confirma
  que son campos de nivel hogar, seguros para deduplicar por `DIRECTORIO_HOG`.
- 95 grupos geográficos reales, 600-1,300+ hogares cada uno. 21.3% de hogares sin este dato,
  explicado limpiamente: 100% de Sumapaz (ya excluido en todo el proyecto) y filas fuera de
  Bogotá (Soacha, sin `NOMBRE_LOCALIDAD`) — el resto de localidades de Bogotá tiene 0-14% de
  huecos, sin patrón sistemático.
- **Crosswalk contra las 112 UPZ reales** (`carga_datos.cargar_upz_limites()`): muchos códigos
  `COD_UPZ_GRUPO` coinciden EXACTAMENTE con `CODIGO_UPZ` real (son UPZ individuales); los códigos
  ≥800 son grupos de 2-4 UPZ reales fusionadas por diseño muestral (ej. `803` = "USAQUÉN: Country
  Club + Santa Bárbara" = UPZ reales 15+16). Resultado verificado: **112 de 112 UPZ reales
  cubiertas**, 0 conflictos.
- `NHCCP38` ("¿este hogar clasifica los residuos?") está limpio, sin NA (74.9% Sí / 25.1% No
  sobre 292,281 respuestas).
- Comparación de nivel de ciudad (ponderada): ECA2021 = 71.87%, EM2021 = 74.5% — una diferencia
  moderada (~2.6pp), no un salto brusco.

**Spot-check de las 2 localidades con muestra ECA2021 degenerada**: Los Mártires (antes 100%,
n=1) ahora tiene UPZ reales entre 55.4% y 67.5%; Santa Fe (antes 33.33%, n=3) ahora tiene UPZ
reales entre 44.0% y 74.9% — rangos creíbles, con variación real UPZ a UPZ, en vez de un único
valor heredado sostenido por 1 o 3 encuestas.

**Implementación** (`abm/datos_reales.py::construir_o_cargar_separacion_upz_em2021`, mismo patrón
de las demás fuentes reales de este proyecto: calcular desde el crudo, cachear, sobrescribir el
valor legado de `df_modelo.csv` al construir cada `EntornoUPZ` en `modelo.py` — no se reescribe
`df_modelo.csv`): `prob_separa` y `pct_calidad_separacion` (breadth de 6 tipos de material,
`NHCCP38AA-AG`) ahora vienen de esta fuente, ponderada por `FEX_C`, por UPZ real.

**Recalibración obligatoria**: el nivel de ciudad cambió ~2.6pp y la estructura espacial cambió
de raíz (de 20 valores heredados a 112 medidos), así que los parámetros calibrados el 2026-07-13
no se asumieron válidos sin volver a correr la búsqueda en rejilla completa.

**Metodología (3 etapas, no 2 — la rejilla tuvo que ampliarse 2 veces porque el óptimo caía
repetidamente en el borde)**: búsqueda exhaustiva a resolución reducida (90 días/año, 1%
muestreo), primero en un rango centrado en los valores previos (45 combinaciones), luego ampliada
hacia donde la tendencia señalaba mejora (36 combinaciones), luego una tercera rejilla angosta de
confirmación (36 combinaciones) — convergencia clara en un interior: `factor_brecha=0.63,
umbral_percepcion_impacto=0.07`, con `beta_decaimiento` insensible entre 0.03-0.05 (RMSE
idéntico dentro de 0.01pp, mismo patrón de no-identificabilidad ya documentado para este
parámetro). RMSE a resolución reducida: 1.21pp.

**Hallazgo metodológico nuevo, no visto en las 2 recalibraciones anteriores**: al confirmar ese
combo a RESOLUCIÓN COMPLETA (365 días/año), el RMSE subió a 2.10pp — la resolución reducida NO
fue, esta vez, un proxy confiable. Hipótesis (verificada probando variantes): el ciclo semanal de
actualización de actitud corre solo ~12 veces en un año de 90 días simulados, pero ~52 veces en
un año completo — un `beta_decaimiento` que se ve bien con 12 ciclos de decaimiento puede
sobre-acumular con 52. Se probaron 4 variantes adicionales DIRECTAMENTE a resolución completa
(más caro pero definitivo, dado que la búsqueda reducida ya no era confiable):

| Variante (a resolución completa) | RMSE |
|---|---|
| `brecha=0.63, decay=0.04, umbral=0.07` (el "óptimo" de la búsqueda reducida) | 2.10pp |
| `brecha=0.63, decay=0.04, umbral=0.035` (umbral viejo) | 6.07pp |
| **`brecha=0.63, decay=0.02, umbral=0.07`** | **1.20pp** |
| `brecha=0.70, decay=0.04, umbral=0.035` | 5.36pp |
| `brecha=0.60, decay=0.04, umbral=0.035` | 6.62pp |

**Resultado final**: `factor_brecha_intencion_accion=0.63, beta_decaimiento=0.02,
umbral_percepcion_impacto=0.07, beta_recuperacion=0.02` (sin cambios) — **RMSE=1.1961pp a
resolución completa**, prácticamente igual al 1.15pp confirmado el 2026-07-13 con la fuente
anterior (ECA2021/localidad). El cambio de fuente de datos (más real, más granular) no empeoró el
ajuste — y confirma, de paso, que el umbral de percepción de impacto (0.07, no 0.035) es
sensible al nivel de base de `prob_separa`, algo intuitivo: con una base más alta (EM2021, ~74.5%
vs. ECA2021 ~71.87%), hace falta un margen relativo más ancho para que el mecanismo de
decaimiento se active de forma realista.

---

## 6. Sensibilidad de parámetros — método y por qué es válido a esta escala

El análisis (`data/processed/24_sensibilidad_parametros.csv`) es **uno-a-la-vez (OAT)**: para
cada uno de los 4 parámetros libres, se fijan los otros 3 en su valor óptimo y se muestra cómo
cambia el RMSE — es un corte de la propia rejilla de calibración ya corrida, no una búsqueda
nueva. No es un método global (Sobol, Morris/MOAT) que capture interacciones entre parámetros.
Según la literatura metodológica revisada para este documento, OAT es un método válido y estándar
para "screening" de parámetros con presupuesto computacional limitado (exactamente el caso de un
ABM de tesis de posgrado corrido en una máquina personal); métodos globales como Sobol son
preferidos cuando se sospechan interacciones fuertes entre parámetros, a costa de un presupuesto
computacional mucho mayor. Declarar esto explícitamente —"es OAT, no un método global, por
restricción de cómputo, y Sobol/Morris quedan como trabajo futuro"— es honestidad metodológica,
no una debilidad a esconder.

Fuentes revisadas (2026-07-14):
- [Parameter estimation and sensitivity analysis in an agent-based model of Leishmania major infection](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2789658/)
- [An efficient and flexible framework for inferring global sensitivity of agent-based model parameters](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12435692/)
- [Dealing with uncertainty in agent-based models for short-term predictions](https://royalsocietypublishing.org/doi/10.1098/rsos.191074)

---

## 7. Contraste de escala, honesto, con MATSim

El usuario trajo MATSim (Zúrich) como referencia de rigor en ABM sociotécnicos. Vale la pena
poder decir con precisión en qué se inspira este proyecto y en qué NO es comparable, para no
sobrevender la analogía ante un comité que conozca MATSim:

| | MATSim (Zúrich) | Este ABM |
|---|---|---|
| Agentes | Millones (muestra sintética del 10% de la población real) | 75,273 (muestra del 3% de hogares reales por cohorte UPZ×estrato) |
| Qué representa un agente | Una persona real, con plan de actividades diario de 24h | Una fracción muestreada de una cohorte UPZ×estrato, con un peso de escalamiento poblacional |
| Aprendizaje/adaptación | Iterativo, basado en utilidad (algoritmo genético sobre planes, 100-200 iteraciones hasta equilibrio) | Ninguno explícito por agente — la dinámica de actitud (decaimiento/recuperación) es una regla fija calibrada, no una optimización de utilidad individual |
| Infraestructura | Red vial real, horarios reales de transporte público | Red de vecindad UPZ (contigüidad geográfica), sin red vial ni rutas reales |
| Calibración | Contra conteos de tráfico y encuestas de movilidad de alta frecuencia | Contra una serie ANUAL (6 puntos), que a su vez es la salida de otro modelo (ver §4) |
| Heterogeneidad individual | Alta — atributos socioeconómicos completos por persona | Moderada — 3 covariables reales (participación, vivienda, informalidad) aplicadas de forma estocástica dentro de cada cohorte, ver §5 |
| Escala de proyecto | Equipos de investigación, años de cómputo | Tesis de posgrado, una máquina personal |

**Conclusión**: este proyecto se inspira en el espíritu de un ABM sociotécnico basado en dato
real (agentes con atributos reales, mecanismos de comportamiento calibrados, no supuestos
inventados) pero opera a una escala y con un nivel de detalle muy distintos — no hay aprendizaje
iterativo por utilidad, no hay red vial real, y la calibración es anual, no de alta frecuencia.
Es una diferencia de escala, no un defecto: el estándar de "modelo sociotécnico riguroso" no
exige igualar la escala de MATSim, exige que cada mecanismo y cada parámetro tenga una fuente
declarada (dato real, calibración, o supuesto acotado) — que es exactamente lo que este
documento, junto con `Diseno_ABM.md`, `Reglas_Negocio_v2_y_Modelado_Agentes.md` e
`Investigacion_Salto_Aprovechamiento.md`, ya cubre en conjunto.

---

## 8. Qué representa un "agente hogar", en una frase defendible

Un `HogarAgente` es una **muestra ponderada de una cohorte real UPZ×estrato** (no un hogar real
individual, no una cohorte agregada sin varianza): 75,273 agentes sobre 204 cohortes reales con
datos, cada uno con un peso de escalamiento poblacional (`poblacion_representada`) para que los
agregados del modelo extrapolen a la población total. La dinámica de actitud (decaimiento por
free-riding/recuperación) opera sobre el valor calibrado y uniforme de la cohorte — es el
mecanismo que la calibración de 80 combinaciones ajustó, y no se altera por la heterogeneidad
individual. La heterogeneidad individual real (participación comunitaria, vivienda propia,
informalidad — 3 de los 6 predictores reales y significativos encontrados en el EDA) determina
cuánto material separa cada hogar específico en su salida diaria, sin mover el promedio agregado
que la calibración fijó.

---

*Documento generado 2026-07-14, en respuesta a una auditoría de fondo pedida explícitamente por
el usuario tras compartir el caso MATSim (Zúrich) y preguntar si UPZ fue la unidad espacial
correcta. Complementa, sin reemplazar, a `Diseno_ABM.md`, `Reglas_Negocio_v2_y_Modelado_Agentes.md`
e `Investigacion_Salto_Aprovechamiento.md`.*
