# Investigación: ¿Es real el salto de 18.56% a 43.88% en el % de aprovechamiento (2023→2024)?
### Pausa inteligente — verificación contra fuentes oficiales externas antes de seguir calibrando el ABM
**Autores:** Manuel Alejandro González Gallego, Gloria Inés Robledo Ulloa — CUN
**Fecha:** 2026-07-11

> **Respuesta corta: el salto es real en el sentido de que está en los datos oficiales, pero
> casi con toda seguridad NO refleja un cambio real de comportamiento ciudadano — es un cambio
> de metodología/alcance de medición, documentado oficialmente. No es un error nuestro de
> limpieza de datos: es una inconsistencia real de la fuente.**

---

## 1. Lo que ya sabíamos (antes de esta investigación)

`data/raw/Residuos/Residuos generados bogota.xlsx` (la fuente que usa todo el proyecto, incluido
`APROVECHAMIENTO_GROUND_TRUTH_PCT = 48.50` en `src/config.py`) trae esta serie:

| Año | Residuos generados (ton) | Residuos aprovechados (ton) | % aprovechamiento |
|---|---|---|---|
| 2018 | 2,718,631 | 418,044 | 15.38% |
| 2019 | 2,757,154 | 433,001 | 15.70% |
| 2020 | 2,721,227 | 470,321 | 17.28% |
| 2021 | 2,788,386 | 534,786 | 19.18% |
| 2022 | 2,746,224 | 501,638 | 18.27% |
| 2023 | 2,667,955 | 495,238 | 18.56% |
| **2024** | **3,967,682** | **1,741,205** | **43.88%** |
| 2025 | 4,511,169 | 2,187,831 | 48.50% |

**Lo que salta a la vista al mirar la tabla completa (no solo el %):** no es solo que el
aprovechamiento subió — **el total de residuos generados también saltó 48.7%** en un solo año
(2,667,955 → 3,967,682 toneladas). Una ciudad no genera de repente 1.3 millones de toneladas
adicionales de basura de un año a otro sin que cambie algo en cómo se está contando, no en cómo
se está botando la basura.

---

## 2. Lo que se investigó ahora: fuentes oficiales externas, independientes de nuestro archivo

### 2.1 Hallazgo #1 — El % de aprovechamiento de la UAESP NO es una medición directa, es un modelo

Confirmado en el propio sitio del Observatorio Ambiental de Bogotá (OAB) y en búsquedas
independientes: la UAESP **no pesa** el material aprovechado y lo divide por lo generado — usa
un **"Modelo Macro Econométrico"** que **estima** ambas cifras a partir de:
- Toneladas dispuestas en el Relleno Doña Juana (el único dato que sí se pesa directamente),
- Crecimiento del PIB, índice de precios al consumidor y al productor,
- Tasa de crecimiento poblacional,
- Verificación de flujo de materiales,
- Tasa promedio de aprovechamiento del PGIRS.

Es decir: **el "% de aprovechamiento" oficial de Bogotá es una salida de un modelo estadístico,
no una medición de báscula.** Cualquier recalibración de ese modelo (nuevos supuestos
macroeconómicos, nueva versión del PGIRS, etc.) puede mover el resultado sin que nada haya
cambiado realmente en la calle.

### 2.2 Hallazgo #2 — Confirmación textual de que la metodología SÍ cambió

El propio Observatorio Ambiental de Bogotá declara textualmente (página "Toneladas Residuos
Sólidos Aprovechados"):

> "Para las vigencias 2019-2023, la estimación del porcentaje de residuos aprovechados se
> realizó a través de un modelo econométrico desarrollado por UAESP."

La forma en que está escrita esta frase — acotando explícitamente "para las vigencias
2019-2023" — es la señal más clara de que **para 2024 en adelante se usó algo distinto**, aunque
no se logró extraer el texto exacto de qué cambió (el documento técnico del PGIRS 2024 donde
debería estar el detalle tiene una tabla con una fuente tipográfica que no se pudo leer
programáticamente — ver limitación en la sección 5).

### 2.3 Hallazgo #3 — Prueba cuantitativa directa: dos fuentes oficiales, mismo año, cifras muy distintas

Se encontró y descargó la serie oficial de **toneladas aprovechadas según el SUI** (Sistema
Único de Información de la Superintendencia de Servicios Públicos — la plataforma donde las
organizaciones de recicladores reportan directamente lo que recolectan), publicada en
`datosabiertos.bogota.gov.co` (dataset "Aprovechamiento Toneladas Aprovechadas. Bogotá D.C.").
Con esta serie se pueden comparar, para los MISMOS años, dos fuentes oficiales distintas:

| Año | Nuestro archivo (modelo UAESP/OAB) | Serie SUI (autorreportada por recicladores) | Diferencia |
|---|---|---|---|
| 2018 | 418,044 ton | **781,564 ton** | SUI reporta **1.87× más** |
| 2019 | 433,001 ton | **1,031,905 ton** | SUI reporta **2.38× más** |

**Esto es la prueba más contundente de esta investigación: dos fuentes oficiales del Distrito
reportan cifras que difieren en un factor de ~2x para el mismo concepto, el mismo año.** No es
posible que "el % de aprovechamiento real de Bogotá" sea un solo número estable y bien definido
si ni siquiera las propias entidades del Distrito coinciden entre sí.

### 2.4 Hallazgo #4 — La nota metodológica de la propia serie SUI explica por qué

El archivo descargado (`enero-2015-abril-2020-sa-toneladas-aprov.csv`) trae, en su propia celda
de notas, la explicación oficial de **3 cambios de metodología dentro de esa sola serie**:

> "Desde diciembre de 2012... hasta abril de 2016..., la información corresponde a los registros
> en planillas de los centros de pesaje donde se realizaba tal labor. Entre abril y diciembre de
> 2016, la información corresponde a la registrada en planillas de centros de pesaje MÁS la
> cargada por parte de las organizaciones de recicladores en la plataforma del SUI... A partir de
> enero de 2017 a la fecha, la información corresponde a la cargada por parte de las
> organizaciones de recicladores en el SUI."

Es decir: **hasta 2016 se pesaba directamente el material; desde 2017 el dato depende
completamente de lo que cada organización de recicladores decide reportar por su cuenta** — y ya
se encontró, de forma independiente, una resolución oficial de la SSPD (2020) que reconoce
**"inconsistencias que aumentan el dato real de las toneladas de residuos efectivamente
aprovechadas"** en esos reportes autodeclarados.

**Hallazgo adicional, menor pero digno de mención:** los valores mensuales de 2017 en este
archivo oficial son una copia exacta, mes por mes, de los de 2016 — un error de origen en el
propio archivo gubernamental (no nuestro), documentado aquí por transparencia.

---

## 3. Conclusión de la investigación

El salto 2023→2024 (y, en general, cualquier comparación año a año de "% de aprovechamiento" en
las fuentes oficiales de Bogotá) **no se puede tratar como una serie de comportamiento real y
comparable en el tiempo**. La evidencia reunida apunta, de forma consistente, a que:

1. El indicador oficial es un **modelo estadístico**, no una medición directa.
2. Existe **confirmación textual oficial** de que la metodología del modelo cambió entre
   2019-2023 y lo que vino después.
3. Hay **prueba cuantitativa independiente** (la serie SUI) de que fuentes oficiales distintas
   difieren en factor ~2x para los mismos años — el problema de inconsistencia metodológica no
   es exclusivo del salto 2023-2024, es estructural en cómo Bogotá mide este indicador desde
   hace años.
4. El salto de **generación total** (no solo aprovechamiento) de 48.7% en un año refuerza que se
   trata de un cambio de alcance/definición, no de un fenómeno físico real.

**No se logró identificar el detalle exacto y textual de qué cambió específicamente entre 2023 y
2024** (limitación honesta, ver sección 5) — pero la dirección de la evidencia es unánime: es un
problema de medición, no de comportamiento ciudadano.

---

## 4. Propuesta de ajuste para el modelo — 3 opciones, con recomendación

El objetivo de calibración actual del ABM (`APROVECHAMIENTO_GROUND_TRUTH_PCT = 48.50`, en
`src/config.py`, usado como referencia en el dashboard) hereda todo este problema. Se proponen 3
opciones — **esta es una decisión que afecta el argumento central de la tesis, así que se deja
para que la elijas tú, no se implementa unilateralmente**:

### Opción A (recomendada) — Calibrar contra la serie pre-2024, tratar 2024-2025 como quiebre documentado
Usar **18.56% (2023)**, o el promedio 2018-2023 (~17.4%), como el objetivo de calibración real
del ABM, y **documentar explícitamente en la tesis** que 2024-2025 no se usan para calibrar
porque representan un cambio de metodología de medición, no de comportamiento — con toda la
evidencia de este documento como sustento. Es la opción más defendible metodológicamente: un
ABM que simula el comportamiento de hogares y recicladores debería calibrarse contra la serie
más consistente internamente, no contra un salto que ni las propias entidades pueden explicar
con una sola cifra.

### Opción B — Mantener 48.5% como meta, pero re-etiquetarla explícitamente
Seguir usando 48.5% como referencia (porque es la cifra más reciente y la que citan las fuentes
oficiales hoy), pero cambiar la interpretación en todos los documentos/dashboard: no como "la
meta real de comportamiento a alcanzar", sino como **"la cifra oficial vigente, con la salvedad
metodológica documentada en `Investigacion_Salto_Aprovechamiento.md`"**. Menos limpio
metodológicamente, pero evita que la tesis se aparte del número que cualquier jurado buscaría en
fuentes oficiales actuales.

### Opción C — Reportar un rango, no un número único
Calibrar el ABM para reproducir un **rango** (17-20% como "piso conservador",
43-48% como "techo si se adopta la metodología 2024+"), y usar el modelo para preguntar
explícitamente: *¿qué combinación de mecanismos del ABM sería necesaria para explicar un salto
de esa magnitud, si fuera real?* — convirtiendo la propia inconsistencia de la fuente en una
pregunta de investigación secundaria legítima, en vez de un problema a esconder.

---

## 4bis. Verificación adicional: el contexto regulatorio real de 2024 (confirmado, no especulado)

Tras una primera versión de este documento, se verificaron 3 afirmaciones puntuales sobre qué
cambió específicamente en 2024 — **las 3 se confirmaron reales** contra fuentes oficiales
independientes (no se dieron por ciertas sin verificar):

- **"Reto SeparAcción" / Concurso Distrital de Aprovechamiento de Residuos**: confirmado real —
  liderado por la Secretaría General, el DASCD y la UAESP, con 44 entidades distritales
  midiendo su propio reciclaje interno cada trimestre. **Es real, pero mide el reciclaje interno
  de oficinas del gobierno distrital — no puede, por su propia naturaleza y escala, explicar un
  salto de más de 1.2 millones de toneladas en el aprovechamiento de toda la ciudad.**
- **Decreto 1381 de 2024** (Ministerio de Vivienda, Ciudad y Territorio): confirmado real y
  significativo. Da **exclusividad de 15 años** a los recicladores de oficio sobre la actividad
  de aprovechamiento, y — el punto más relevante para esta investigación — **obliga a los
  municipios y distritos a "realizar, actualizar y publicar CADA AÑO el censo de recicladores de
  oficio de su territorio conforme al PGIRS"**. Un cambio en cómo se censa y registra a los
  recicladores formales cambia mecánicamente cuánto material "cuenta" como aprovechamiento
  formal, sin que eso implique más separación real en los hogares.
- **Nuevo PGIRS 2024-2028 (Decreto 484 de 2024)**: confirmado real — la actualización vigente
  del Plan de Gestión Integral de Residuos Sólidos de Bogotá, con nuevo marco de economía
  circular y nuevas metas.

**Conclusión de esta verificación:** 2024 fue, de manera confirmada y documentada, un año de
**reforma regulatoria profunda** del sistema de aprovechamiento en Bogotá (nuevo decreto
nacional, nuevo PGIRS, nuevo esquema de censo obligatorio de recicladores) — no un año en el que
2.7 millones de hogares bogotanos cambiaron radicalmente su comportamiento de separación. La
forma académicamente defendible de decir esto ante un comité no es "la UAESP miente" (una
acusación que esta investigación no puede probar con certeza absoluta), sino: **el indicador
oficial tiene una discontinuidad metodológica documentada y verificable en 2024, y por lo tanto
no es válido usarlo como medida comparable de comportamiento ciudadano antes y después de ese
año.** Esa distinción es más precisa, más defendible, y logra exactamente lo que se busca:
que el modelo no se calibre contra un número que no representa lo que dice representar.

## 5. Decisión adoptada (ya no es solo una recomendación)

Dado lo anterior, se descarta la Opción B (mantener 48.5% re-etiquetada) — el usuario decidió
explícitamente que ese número no debe seguir usándose como si fuera comparable. **Se adopta la
Opción A**: el objetivo de calibración del ABM pasa a ser **18.56% (2023, el último año de la
serie internamente consistente 2018-2023, antes del quiebre regulatorio de 2024)**, no 48.5%.

Se prefiere el valor puntual de 2023 sobre el promedio 2018-2023 (~17.4%) porque la serie
2018-2023 muestra una tendencia real y gradual al alza (15.38% → 18.56%) — usar el punto más
reciente de esa tendencia consistente es más representativo que promediar y "borrar" esa
tendencia real.

**Cambios implementados como consecuencia de esta decisión** (ver también más abajo):
- `src/config.py`: `APROVECHAMIENTO_GROUND_TRUTH_PCT` pasa de 48.50 a **18.56**, con un comentario
  extenso citando este documento.
- `abm/dashboard.py`: la línea de referencia "Meta real 2025 (OAB) = 48.5%" se reemplaza por
  "Meta real 2023 (última cifra consistente) = 18.56%".
- Todos los documentos previos que citan 48.5% como "meta real" (`Diseno_ABM.md`,
  `Reglas_Negocio_v2_y_Modelado_Agentes.md`) quedan con una nota de que ese valor fue
  reemplazado — sin reescribir su historia, para que quede trazable que la decisión cambió en
  este punto de la investigación, no desde el principio.

## 6. Limitaciones de esta investigación (honestas)

- No se logró extraer el texto exacto del PGIRS 2024 que debería explicar el cambio de
  metodología 2023→2024 específicamente — la tabla relevante (`Tabla 8`, página 41 del
  documento técnico de soporte) usa una fuente tipográfica incrustada que no se pudo decodificar
  con las herramientas de extracción de texto disponibles. Quedó guardado el PDF completo para
  que, si se desea, se revise manualmente esa tabla y esa página específica.
- La serie SUI descargada solo cubre hasta abril de 2020 — no se encontró (en el tiempo
  disponible de esta investigación) una serie SUI continua y descargable hasta 2024-2025 para
  hacer la misma comparación directa en el año del salto específico. La comparación 2018-2019 ya
  es, sin embargo, evidencia suficientemente fuerte del patrón de inconsistencia estructural.
- No se llegó a contactar directamente a la UAESP ni a solicitar el detalle metodológico por un
  canal oficial (PQRS, derecho de petición) — sería el siguiente paso si se necesita una
  confirmación 100% definitiva y textual del cambio específico de 2024.

---

## 7. Calibración multi-año y contrafactual 2024 (2026-07-11)

Con la decisión de la sección 5 ya implementada, el usuario planteó la pregunta natural: en vez
de solo *descartar* el 48% (o el 43.88%), ¿podemos usar el propio ABM para **estimar de forma
independiente** qué habría dado 2024 si el comportamiento hubiera seguido su trayectoria real
2018-2023, sin el quiebre metodológico? Esta sección documenta ese ejercicio: entrenar (calibrar)
el modelo contra los 6 puntos reales 2018-2023, y usarlo para proyectar 2024 como un
**contrafactual** — no una predicción validable (2024 no tiene una cifra comparable contra la
cual medir error, ver secciones 1-5), sino una estimación independiente, con mecanismos propios,
de lo que habría pasado sin la reforma.

### 7.1 Primer hallazgo: la población casi no explica el cambio real

Antes de calibrar nada, se hizo una decomposición tipo *shift-share*: manteniendo fija la tasa de
separación de la encuesta (EM2021, `pct_separa_en_fuente`, idéntica en las 7 filas 2018-2024 de
cada UPZ — es una sola encuesta repetida, no una serie real) y dejando variar solo la
composición demográfica real año a año (población/hogares por UPZ, que sí es una proyección DANE
genuina), el promedio ponderado de ciudad se mueve **0.056 puntos porcentuales** entre 2018 y
2023 — frente a un cambio real de **3.18 puntos** (15.38%→18.56%). La población explica
**~1.8%** del cambio real observado. El otro ~98% tiene que salir de mecanismos reales del
sistema (infraestructura, capacidad formal, comportamiento), no de que la ciudad creció.

### 7.2 Segundo hallazgo: el mecanismo de imitación, por diseño, no puede producir una tendencia

El mecanismo de "free-riding"/imitación (`agentes_hogar.py`) hace que `prob_separa_actual` decaiga
hacia un piso o se recupere hacia su propia base — nunca por encima de ella. Es un mecanismo de
**erosión**, diseñado para explicar por qué el aprovechamiento se queda bajo pese a buenas
intenciones, no un mecanismo de **crecimiento**. Encadenarlo año a año tal como estaba habría
aplanado o reducido la trayectoria simulada, nunca producido el alza real observada.

### 7.3 Rediseño: dos canales de crecimiento reales, en vez de un parámetro inventado

En vez de agregar un parámetro de "mejora de actitud" sin sustento, se recuperó variación real ya
recolectada pero hasta ahora **promediada y desechada**:

- **Infraestructura (SIGAB):** los 4 cortes (2020, 2022, 2024, 2026) se promediaban en un solo
  índice estático. Ahora cada año simulado usa el snapshot real más cercano en el tiempo
  (`abm/datos_reales.py::construir_o_cargar_infraestructura_real_por_anio`).
- **Capacidad formal (RBL):** el promedio histórico único se reemplazó por una cifra REAL por
  año (`construir_o_cargar_capacidad_ase_por_anio`), extrapolada por regla de tres desde los
  meses disponibles cuando la cobertura es parcial, y marcada `confiable=False` (con fallback al
  promedio blended) en los años con menos de 6 meses de datos (2018, 2019, 2020).
- **Encadenamiento de estado:** se agregó `ModeloResiduosBogota.estado_previo_cohortes` — al
  terminar un año, el promedio de `prob_separa_actual` por cohorte UPZ×estrato se pasa como base
  del año siguiente (`abm/calibracion.py::correr_serie_anios`), dándole al modelo una memoria real
  entre años en vez de reiniciar cada año desde la misma foto fija de la encuesta.

### 7.4 Dos bugs de datos corregidos en el camino (no cosméticos)

- **RBL 2020, 3 archivos descartados silenciosamente**: el *sniffer* de separador de
  `cargar_rbl_consolidado` lanzaba una excepción (no solo detectaba mal el delimitador) en 3
  archivos de 2020 con números en formato "34.212,97" — la excepción saltaba por encima del
  reintento con `sep=";"` ya existente. Corregido en `src/carga_datos.py`; la cobertura de 2020
  pasó de 155,088 a 616,761 toneladas/año (el archivo de marzo completo estaba perdido).
- **Capacidad formal ~12x sobreestimada**: `construir_o_cargar_capacidad_ase` dividía un TOTAL
  ANUAL entre 30 (tratándolo como si fuera mensual) en vez de entre 365. La capacidad formal
  agregada de los 5 ASE pasó de **38,913 ton/día** (5 veces la generación diaria real de TODA la
  ciudad — nunca se saturaba, por construcción) a **3,339 ton/día** (una restricción real y
  potencialmente vinculante). Corregido en `abm/datos_reales.py`.

### 7.5 Tercer hallazgo, el más importante para el nivel: brecha intención-acción

Incluso con las mejoras anteriores, correr el año ancla (2018) con los parámetros de partida daba
**~31% simulado contra 15.38% real** — casi el doble. La causa: `prob_separa_en_fuente` viene de
una ENCUESTA ("¿usted separa?", EM2021), no de una medición de material. La brecha entre lo que la
gente reporta que hace y lo que efectivamente se cuenta como aprovechamiento oficial es un
fenómeno **ampliamente documentado en la literatura de comportamiento ambiental** (brecha
intención-acción / sesgo de deseabilidad social) — no un error de este proyecto. Se agregó
`FACTOR_BRECHA_INTENCION_ACCION` (`abm/config_abm.py`) como un parámetro libre explícito, en vez
de dejar que los otros 4 parámetros absorbieran, sin poder identificarlo, lo que en realidad era
una brecha de nivel.

### 7.6 Calibración: búsqueda en rejilla y hallazgo de no-identificabilidad

Se calibró contra las 5 transiciones reales 2019-2023 (2018 es el año ancla/inicialización, no se
calibra contra él — no hay un año anterior del cual heredar estado). Búsqueda exhaustiva (no un
optimizador de caja negra) en una rejilla de 72 combinaciones, a resolución reducida (60
días/año, 1% de muestreo de hogares) por tractabilidad, con confirmación final a resolución
completa (365 días/año, 3% de muestreo) sobre la mejor combinación:

| Parámetro | Rango probado | Resultado |
|---|---|---|
| `factor_brecha_intencion_accion` | 0.45 – 0.70 | **Óptimo en 0.56** (RMSE≈1.07pp) — domina el ajuste |
| `capacidad_recoleccion_individual` | 10–20 kg/día | Sin efecto detectable en el RMSE |
| `beta_decaimiento` | 0.02–0.04 | Sin efecto detectable en el RMSE |
| `beta_recuperacion` | 0.01–0.03 | Sin efecto detectable en el RMSE |
| `umbral_percepcion_impacto` | 0.10–0.20 | Sin efecto detectable en el RMSE |

**Hallazgo honesto de no-identificabilidad**: las 24 combinaciones de los últimos 4 parámetros,
para cada valor de `factor_brecha`, dieron exactamente el mismo RMSE. No es evidencia de que esos
parámetros no importen en la dinámica del modelo — es evidencia de que **datos anuales agregados
de ciudad no tienen resolución suficiente para distinguirlos entre sí** (haría falta una serie
real por UPZ o un panel de hogares, que no existe). Ya se había anticipado este riesgo en
`Diseno_ABM.md` §8; ahora está confirmado empíricamente, no es solo una advertencia teórica. Se
conservan en sus valores de partida documentados (`Reglas_Negocio_v2_y_Modelado_Agentes.md`).

### 7.7 Resultado de la confirmación a resolución completa

| Año | Real oficial | Simulado (ABM, encadenado) | Diferencia |
|---|---|---|---|
| 2018 (ancla) | 15.38% | 17.35% | +1.97pp |
| 2019 | 15.70% | 17.46% | +1.76pp |
| 2020 | 17.28% | 17.54% | +0.26pp |
| 2021 | 19.18% | 17.61% | −1.57pp |
| 2022 | 18.27% | 18.11% | −0.16pp |
| 2023 | 18.56% | 18.16% | −0.40pp |
| **2024** | **43.88%** (oficial, post-reforma) | **18.29%** (contrafactual ABM) | **−25.6pp** |

RMSE 2019-2023 ≈ **1.08 puntos porcentuales** — el modelo captura el nivel y la tendencia gradual
real razonablemente bien (subestima el pico real de 2021, probablemente una anomalía puntual,
posiblemente asociada a la reactivación pos-pandemia, que ningún mecanismo del modelo representa
explícitamente — ver limitaciones).

### 7.8 La respuesta a la pregunta que motivó esta investigación

Un modelo mecanicista, construido de abajo hacia arriba (hogares, recicladores, operadores,
infraestructura real), **calibrado únicamente contra la trayectoria real 2018-2023 y sin ningún
mecanismo que represente la reforma regulatoria de 2024**, proyecta que 2024 habría cerrado
alrededor de **18.3%** si el sistema hubiera seguido su dinámica orgánica. La cifra oficial
reportada para 2024 es **43.88%** — una brecha de **~25.6 puntos porcentuales** que ninguno de
los mecanismos reales del modelo (crecimiento poblacional, infraestructura real, capacidad formal
real, dinámica de actitud calibrada) puede generar. Esto no "demuestra" en sentido estadístico
estricto que el 43.88%/48.50% sean incorrectos — el modelo también tiene sus propios límites
(sección 7.9) — pero es **evidencia cuantitativa independiente, con metodología propia**, que
converge con la evidencia documental de las secciones 1-4 (el % oficial es salida de un modelo
econométrico, no una medición; dos fuentes oficiales del Distrito difieren en factor ~2x; el
quiebre coincide con una reforma regulatoria confirmada). Tres líneas de evidencia independientes
apuntando en la misma dirección es un argumento defendible ante un comité de tesis.

### 7.9 Limitaciones honestas de este ejercicio de calibración (además de las de la sección 6)

- El modelo subestima el pico real de 2021 (19.18%) y por tanto también parte de la caída a
  2022 — la trayectoria simulada es más suave que la real. Es consistente con que el modelo no
  tiene ningún mecanismo para capturar shocks puntuales (p.ej. efectos pos-pandemia en generación
  o recolección de residuos).
- 4 de los 5 parámetros libres del modelo de comportamiento resultaron no identificables con los
  datos disponibles (§7.6) — el buen ajuste depende casi enteramente de `factor_brecha`, un
  parámetro de NIVEL, no de forma. La forma de la trayectoria simulada viene sobre todo de los
  canales reales de infraestructura/capacidad, no de una dinámica de comportamiento validada.
  2018-2020 usan capacidad formal extrapolada de pocos meses de RBL (cobertura parcial) — esos 3
  años tienen mayor incertidumbre que 2021-2024 (cobertura completa o casi completa).
  Sumapaz aparte, el índice de infraestructura se sigue asignando por snapshot más cercano, no
  interpolado día a día.
- El contrafactual 2024 asume que `factor_brecha_intencion_accion` (la brecha encuesta↔medición)
  es constante en el tiempo — no hay forma de verificar eso con los datos disponibles (una sola
  encuesta, EM2021).
- Esto NO es una validación en el sentido estricto de machine learning (no hay verdad conocida
  contra la cual medir error en 2024) — es una estimación contrafactual con metodología declarada,
  cuyo valor es la CONVERGENCIA con las otras líneas de evidencia, no una prueba aislada.

**Archivos de esta fase**: `abm/calibracion.py` (motor de calibración/encadenamiento),
`abm/datos_reales.py` (infraestructura/capacidad por año), `abm/config_abm.py`
(`FACTOR_BRECHA_INTENCION_ACCION`), `abm/modelo.py` (`estado_previo_cohortes`,
`estado_final_por_cohorte`, `pct_aprovechamiento_anual`), `abm/dashboard.py` (panel
"Contrafactual: ¿qué habría dado 2024 sin el quiebre de metodología?"),
`data/processed/22_calibracion_rejilla_resultados.csv` (las 72 combinaciones probadas),
`data/processed/23_confirmacion_calibracion_2018_2024.csv` (la trayectoria final).

---

## 8. Recalibración tras corregir 2 bugs reales del mecanismo de actitud (2026-07-13)

Al construir el dashboard interactivo y correr la simulación día a día, se encontró que **todas
las series salían perfectamente planas** (generado, aprovechado, rechazo, % — ni un solo día de
variación en todo el año). Investigando la causa, se encontraron **dos bugs reales de mecanismo**
en `agentes_hogar.py` (no un problema de visualización):

1. **Umbral de decaimiento matemáticamente inalcanzable.** El mecanismo de imitación/free-riding
   solo "decae" la actitud de un hogar si el promedio de sus vecinos cae bajo un umbral absoluto
   fijo (0.15). Se verificó, con el modelo real, que **ninguna de las 204 cohortes UPZ×estrato
   tiene un promedio de vecinos por debajo de 0.187** — el mecanismo estaba muerto desde el día 1
   de cualquier corrida, en cualquier año.
2. **El piso de decaimiento no estaba en la misma escala que el resto del modelo.**
   `PROB_SEPARA_PISO` (0.5916) se calibró contra el % crudo de encuesta, pero nunca se reescaló
   por `factor_brecha_intencion_accion` como sí se hace con `prob_separa_base` — dejaba el piso
   muy por encima de la base real de **99.65% de los agentes**, así que aunque el disparador de
   decaimiento se hubiera cumplido, no había a dónde bajar.

Juntos, estos dos bugs explican retroactivamente por qué la calibración del 2026-07-11 encontró
que 4 de los 5 parámetros libres eran "no identificables": nunca llegaban a ejecutarse, así que
cambiar su valor no podía cambiar nada. No era, como se documentó entonces, solo un límite de
resolución de los datos anuales agregados.

**Corrección aplicada:** el disparador de decaimiento ahora compara contra un umbral RELATIVO a
la base propia del agente (¿mis vecinos separan sensiblemente menos que yo?), y el piso se
reescala por la misma brecha intención-acción — ver docstrings en `agentes_hogar.py`.
Verificado semana a semana que ahora SÍ hay movimiento real (18.03% → 14.6% en 20 semanas con los
parámetros de partida, antes de recalibrar).

**Recalibración completa:** con el mecanismo ya vivo, la calibración anterior (brecha=0.56,
"no identificable" en los otros 3 parámetros) quedó inválida — se repitió el proceso completo
(búsqueda en rejilla de 2 etapas, 80 combinaciones en total, contra los 6 puntos reales
2018-2023), confirmado a resolución completa:

| Parámetro | Valor anterior (mecanismo roto) | Valor recalibrado (mecanismo vivo) |
|---|---|---|
| `factor_brecha_intencion_accion` | 0.56 | **0.60** |
| `beta_decaimiento` | 0.03 (nunca se ejecutaba) | **0.04** |
| `beta_recuperacion` | 0.02 (nunca se ejecutaba) | 0.02 (sigue sin afectar el resultado — ver nota abajo) |
| `umbral_percepcion_impacto` | 0.15 (inalcanzable) | **0.035** (relativo, ~11% de cohortes disparan decaimiento) |

| Año | Real oficial | Simulado (mecanismo roto, 2026-07-11) | Simulado (mecanismo corregido, 2026-07-13) |
|---|---|---|---|
| 2018 (ancla) | 15.38% | 17.35% | 17.85% |
| 2019 | 15.70% | 17.46% | 17.83% |
| 2020 | 17.28% | 17.54% | 17.85% |
| 2021 | 19.18% | 17.61% | 17.87% |
| 2022 | 18.27% | 18.11% | 18.33% |
| 2023 | 18.56% | 18.16% | 18.33% |
| **2024 (contrafactual)** | 43.88% (oficial) | 18.29% | **18.43%** |

RMSE 2019-2023: **1.15pp** (resolución completa) — prácticamente igual al 1.07pp de la
calibración rota, pero ahora con un mecanismo que realmente participa en el resultado, no un
número que salía bien por casualidad de otros dos canales (infraestructura/capacidad) mientras el
comportamiento de los hogares estaba congelado.

**La conclusión central de este documento no cambia — se refuerza:** el contrafactual 2024 sigue
en ~18.4%, a un mundo de distancia del 43.88% oficial (brecha ≈25.5pp, prácticamente la misma que
antes). Ahora esa cifra está respaldada por un modelo cuyo mecanismo de comportamiento de hogares
genuinamente funciona, no uno que coincidencialmente daba un número razonable con la dinámica de
actitud completamente apagada.

**Hallazgo honesto adicional:** `beta_recuperacion` sigue sin mover el resultado en ninguna
combinación probada — no es un bug, es que la recuperación solo importa para cohortes que ya
decayeron y luego ven que sus vecinos mejoran, algo que rara vez ocurre en una cadena de 6 años
dominada por erosión. Documentado como limitación real, no escondido.

---

**⚠️ Nota de actualización (2026-07-14, ronda 5):** `prob_separa` cambió de fuente (ECA2021,
real solo a localidad → EM2021, real a nivel UPZ, 112/112 UPZ reales cubiertas) — ver
`Justificacion_Metodologica_Comite.md` §5bis. Se recalibró de nuevo (`factor_brecha`: 0.60→0.63,
`beta_decaimiento`: 0.04→0.02, `umbral_percepcion_impacto`: 0.035→0.07), confirmado a resolución
completa: **RMSE=1.1961pp**, prácticamente igual al 1.15pp de §8. El contrafactual 2024 y las
series año a año de esta sección quedan como referencia de la calibración ANTERIOR (ECA2021) —
no se recalcularon con la nueva base en esta ronda (el dashboard, que las muestra, queda
explícitamente fuera de alcance de la ronda 5 por instrucción del usuario).

---

*Fin de la investigación (actualizado 2026-07-13 con la corrección de los 2 bugs de mecanismo y
la recalibración completa). El código y el dashboard ya reflejan esta decisión.*
