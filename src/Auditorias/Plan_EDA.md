# Plan del Análisis Exploratorio de Datos (EDA) — Fase 3
### Qué preguntas responde, qué patrones busca, y dónde encajan las reglas de negocio
**Autores:** Manuel Alejandro González Gallego, Gloria Inés Robledo Ulloa — CUN
**Fecha de diseño:** 2026-07-10
**Insumos de esta fase:** `Analisis_Variables_Negocio.md` (inventario de variables) y
`Recoleccion_Datos_Fase2.md` (datos recolectados y limpiados)

> Este documento **es solo diseño** — no contiene código. El objetivo es decidir, antes de
> escribir una sola celda, qué preguntas debe responder el EDA, con qué datos, y en qué orden,
> para que el resultado sea la base real de las decisiones de modelado que vienen después (qué
> variables entran al ABM, qué reglas de negocio se necesitan) — en vez de un EDA genérico que
> describe los datos sin conectarse con la pregunta de investigación.

---

## 1. Punto de partida: el EDA no es un fin en sí mismo, es el Objetivo Específico 1

El proyecto de grado formal (`Analisis_Variables_Negocio.md` §1.1) define la pregunta de
investigación así:

> "¿Cómo las interacciones entre los actores y sus reglas de comportamiento dentro del sistema
> urbano de gestión de residuos sólidos de Bogotá generan las dinámicas emergentes que
> condicionan el aprovechamiento de los residuos y bajo qué escenarios de intervención dichas
> dinámicas podrían modificarse para mejorar el desempeño del sistema?"

Y el **Objetivo Específico 1** es, literalmente, este EDA:

> "Analizar la información histórica mediante EDA para identificar patrones espaciales/temporales,
> relaciones entre variables e indicadores críticos de generación, separación, aprovechamiento y
> disposición final."

Esto fija dos cosas que no se pueden perder de vista al diseñar el EDA:

1. **No basta con "describir" cada variable por separado.** La pregunta de investigación es sobre
   *interacciones entre actores* — así que el EDA tiene que buscar explícitamente relaciones
   **entre** categorías (¿la presencia de recicladores se relaciona con el aprovechamiento?
   ¿el estrato se relaciona con la separación, y esa relación cambia según la infraestructura de
   la zona?), no solo tendencias dentro de una sola categoría.
2. **El EDA es el insumo, no el resultado final.** Sus hallazgos son los que después deciden qué
   variables entran al ABM y qué supuestos hay que ajustar — en ese orden, no al revés.

---

## 2. Dónde encajan las reglas de negocio (respuesta directa a la pregunta planteada)

El usuario preguntó explícitamente en qué fase debe entrar el tema de las reglas de negocio. La
respuesta, con el estado actual del proyecto, es:

**Las reglas de negocio van DESPUÉS del EDA, no antes — y el EDA es exactamente el mecanismo que
las debe producir/validar.**

Razón concreta: escribir reglas de negocio (porcentajes, costos, productividad) antes de tener el
ecosistema de datos completo lleva a suponer números sin sustento. En cambio, el EDA que se
diseña en este documento va a producir, con datos reales:

- El % de aprovechamiento real por año, ya verificado (`RESIDUOS_PER_CAPITA_TON_ANIO`,
  `APROVECHAMIENTO_GROUND_TRUTH_PCT` — ambos vienen de series de datos reales).
- Relaciones cuantificadas entre variables (ej. "¿cuánto más bajo es el aprovechamiento en zonas
  de estrato bajo, controlando por densidad?") que son exactamente el tipo de evidencia que debe
  sostener una regla de negocio, en vez de un número puesto a mano.
- Qué tan dispersos/inciertos son los datos que alimentarían cada regla (ej. la muestra de
  encuesta de Los Mártires n=1 y Santa Fe n=3, ya señalada como poco confiable en
  `Diseno_ABM.md` §8) — información que el propio EDA debe cuantificar para saber qué reglas se
  pueden sostener con confianza y cuáles no.

**Entonces, la secuencia queda:** EDA (este documento, Fase 3) → con sus hallazgos, se construye
una versión trazable de "reglas de negocio", ancladas a evidencia real → esas reglas alimentan
los parámetros del ABM.

---

## 3. Preguntas del EDA, por categoría (con las fuentes ya verificadas que las responden)

### 3.1 Separación en la fuente y calidad de la separación

- ¿Cómo ha evolucionado el % de aprovechamiento a nivel ciudad, año a año (2018-2025)? ¿Dónde
  están los quiebres (el salto 2023→2024, 18.56%→43.88%, ya señalado como posible cambio
  metodológico) y se sostienen al cruzarlos con la serie RBL recién consolidada?
- ¿La probabilidad de separar (`pct_separa_en_fuente`, `05_actores.csv`) varía por localidad? ¿Y
  por estrato, ahora que hay más variables de vivienda/ingreso/educación disponibles en
  `em2021.csv` (40 columnas, antes 16)?
- Usando el **microdato individual crudo de ECA 2021** (~2,282 encuestas, hoja `NUM`, hoy sin
  explotar): ¿cuáles son las razones más frecuentes para NO separar? ¿Qué materiales se separan
  más/menos? ¿Estas razones varían por localidad o estrato?
- Con las nuevas columnas de entorno (`NVCBP14B`/`NVCBP14I`/`NVCBP15F`/`NVCBP15K` — cercanía a
  botaderos, disposición inadecuada en el entorno): ¿un entorno ya degradado se asocia con menor
  separación del propio hogar (evidencia a favor o en contra del mecanismo de "free-riding")?

### 3.2 Estructura y eficiencia de la recolección y la logística

- Con el **RBL consolidado** (2,240 filas, 2017-2026, por operador y tipo de residuo): ¿qué ASE
  recoge más/menos por tipo de residuo? ¿Hay estacionalidad dentro del año? ¿La proporción de
  residuos domiciliarios vs. mixtos/escombros cambia con el tiempo?
- Con las **macrorutas reales** (125 zonas de recolección, 179 de barrido, con horario y
  frecuencia): ¿la frecuencia de recolección varía por localidad? ¿Coincide la cobertura
  geográfica de las macrorutas con las localidades de estrato bajo, o hay zonas con menor
  frecuencia?
- Con los **snapshots de SIGAB** (puntos críticos, contenedores, grandes generadores — 2020,
  dic-2022, dic-2024, jun-2026): ¿los puntos críticos de acumulación se concentran en alguna
  localidad/estrato en particular? ¿Cambia su número/ubicación entre los 4 cortes disponibles?
- ¿Se sostiene, con estos datos nuevos, la idea de que la infraestructura formal de recolección
  **no** es el cuello de botella (supuesto de `Diseno_ABM.md` §4, basado en que la cobertura
  formal es "históricamente casi universal")? Esto se puede probar ahora con datos reales en vez
  de asumirlo.

### 3.3 Capacidad y formalización de los recicladores de oficio

- Con el **RURO oficial 2012-2021**: ¿cómo ha evolucionado el número de recicladores
  registrados por año? ¿Qué proporción está Activa vs. Retirada (24,895 vs. 2,785)? ¿Cuáles son
  las causas de retiro más comunes?
- Con el **RURO 2022 por localidad** (18 archivos, variables de formalización nunca antes
  disponibles): ¿qué proporción de recicladores tiene ARL (afiliación a riesgos laborales, el
  indicador más directo de formalización)? ¿Cómo se relaciona el tipo de afiliación de salud
  (subsidiado vs. contributivo) con la localidad? ¿Hay diferencias entre localidades en
  composición (cabeza de hogar, analfabetismo, habitante de calle)?
- Cruzando conteo de recicladores por localidad (ya en `05_actores.csv`) con el nuevo detalle de
  formalización: ¿las localidades con más recicladores tienen también mayor o menor
  formalización?

### 3.4 Gobernanza institucional y coordinación intersectorial

- Con las **PQRS de aseo por localidad/estrato/concesionario** (dentro de los snapshots de
  SIGAB 2020 y dic-2022, los dos con este archivo completo): ¿qué localidades/estratos generan
  más quejas? ¿Se concentran en algún concesionario en particular? ¿El volumen de PQRS se
  relaciona con el % de aprovechamiento de esa zona?
- Es la categoría con menos datos cuantitativos (documentado ya en `Recoleccion_Datos_Fase2.md`)
  — el EDA aquí debe ser honesto sobre esa limitación, no forzar relaciones sobre una muestra
  débil.

### 3.5 Incentivos económicos (sin condiciones de mercado de reciclables — exclusión que se mantiene)

- Con la tabla de tarifas real (`Tarifas_ASE3_202512.pdf`): ¿cómo se compara el VIAT
  ($11,388/ton) y el factor de subsidio/contribución por estrato con la distribución real de
  estratos por UPZ que ya se tiene en `df_modelo`? Es decir, traducir la tabla de tarifas (hoy un
  PDF) en una estimación de cuánto subsidio/incentivo recibe cada UPZ según su composición de
  estratos.
- ¿Existe alguna relación observable entre el nivel de subsidio (mayor en estratos bajos) y el
  nivel de separación de esos mismos estratos? Esto es exactamente el tipo de pregunta que debe
  sostener (o no) una regla de negocio del ABM, en vez de asumir un efecto.

### 3.6 Factores socio-demográficos y territoriales

- Ya es la categoría mejor cubierta (`densidad_poblacional`, `indice_fragmentacion_social`,
  `heterogeneidad_social`, estratificación a nivel manzana). El EDA aquí debe consolidar lo que
  ya existe en mapas/tablas claras, más que buscar datos nuevos — y usarla como variable de
  control al analizar las demás categorías (ej. "¿la relación entre recicladores y
  aprovechamiento se mantiene controlando por densidad?").

### 3.7 Preguntas de interacción entre categorías — el corazón de la pregunta de investigación

Esta es la sección que **no puede faltar** porque es literalmente lo que pregunta el proyecto de
grado (interacciones entre actores, no variables aisladas):

- Hogares × Recicladores: ¿zonas con más recicladores activos tienen mayor aprovechamiento
  efectivo, o son independientes?
- Hogares × Infraestructura: ¿la relación entre estrato y separación se debilita o se sostiene al
  controlar por la nueva evidencia de puntos críticos/contenedores de SIGAB (en vez del índice
  sintético usado hasta ahora)?
- Recicladores × Operadores formales: ¿hay alguna señal, aunque sea indirecta, de competencia por
  el mismo material (el "mecanismo 2" de la hipótesis original del notebook)? Con RBL + RURO por
  localidad se puede al menos mirar correlación temporal/espacial, aunque no exista un dato
  directo de competencia.
- Gobernanza × Resultado: ¿las localidades con más PQRS tienen peor desempeño de aprovechamiento?

---

## 4. Patrones y tendencias específicos a buscar (transversal a todas las categorías)

- **Temporales:** series 2017-2026 (RBL), 2018-2025 (aprovechamiento/disposición), 2012-2022
  (RURO) — buscar tendencias, quiebres estructurales, estacionalidad dentro del año.
- **Espaciales:** por localidad (20), por UPZ (112), y ahora también por zona operativa
  (macrorutas) — buscar dónde se concentran los problemas, no solo promedios de ciudad.
- **Distribucionales:** dispersión entre localidades/UPZ (no solo el promedio de ciudad, que
  puede esconder desigualdad territorial — justamente el tema central de la hipótesis original).
- **De confiabilidad de la fuente:** tamaño de muestra por localidad en encuestas (ya se sabe que
  hay localidades con n=1 o n=3), cobertura temporal real de cada fuente (algunas empiezan en
  2018, otras en 2020), y granularidad real (localidad vs. UPZ) — esto debe quedar explícito en
  cada hallazgo, no solo al final.

---

## 5. De las preguntas del EDA a "qué variables entran al modelo" — criterios, no una lista a priori

El usuario señaló correctamente que esto "lo dirá el EDA". Para que esa decisión no termine
siendo subjetiva, se proponen 3 criterios explícitos que el EDA debe reportar para cada variable
candidata, y que la siguiente fase (selección de variables) usará para decidir:

1. **Relevancia estadística**: ¿la variable muestra una relación (correlación, diferencia entre
   grupos) con el aprovechamiento o con el comportamiento de separación, dentro de este EDA?
2. **Relevancia teórica**: ¿está conectada con alguno de los mecanismos del marco conceptual
   (Tabla 2 del proyecto de grado, o las 6 categorías) — no basta con que esté disponible, tiene
   que tener un porqué?
3. **Calidad/confiabilidad del dato**: ¿a qué nivel de agregación es real (localidad vs. UPZ), qué
   tan grande es la muestra que la sostiene, y qué tan completa está?

El EDA debe dejar, para cada categoría, una tabla corta con estas 3 columnas — así la elección de
variables del ABM queda trazable a evidencia, no a preferencia.

---

## 6. La discrepancia de actores (4 vs. 5) — el EDA puede aportar evidencia, no la resuelve solo

`Analisis_Variables_Negocio.md` §2.1 dejó abierta la discrepancia entre los 4 actores del proyecto
de grado formal y los 5 del notebook/`Diseno_ABM.md` (que separa "puntos limpios/bodegas" como
actor propio). El EDA no puede decidir esto por sí solo (es una decisión de diseño conceptual),
pero sí puede aportar el insumo que falta: con los datos de SIGAB (puntos críticos, contenedores)
y las macrorutas, se puede ver **qué tanto varía la infraestructura entre UPZ** — si varía mucho,
eso apoya tratarla como un actor/mecanismo propio (como hace el notebook); si es prácticamente
uniforme, apoya la simplificación del proyecto de grado formal (tratarla como condición, no
actor). Esta pregunta específica debe quedar como uno de los resultados explícitos del EDA.

---

## 7. Estructura propuesta del entregable

Un notebook nuevo, `EDA_Dirigido_Fase3.ipynb` (separado del notebook de la Fase 1, que ya cerró
como "construcción del ecosistema de datos" — este es un EDA dirigido por preguntas, no una
segunda pasada de limpieza), organizado en las mismas 6 categorías de la sección 3 más la
sección 3.7 de interacciones, cada una terminando en una tabla de hallazgos con los 3 criterios
de la sección 5. Reutiliza `src/eda.py` (paletas/mapas ya establecidos) y todas las fuentes ya
verificadas en `data/processed/` y `data/raw/externo_fase2/` — no requiere descargar nada nuevo.

---

## 8. Explícitamente fuera de alcance de este documento

- No se escribe código todavía — es la siguiente conversación, una vez se apruebe este diseño.
- No se decide todavía la lista final de variables del ABM — el EDA la informa, no la reemplaza.
- No se resuelve la discrepancia de 4 vs. 5 actores — el EDA solo aporta evidencia para esa
  decisión (sección 6).

---

*Fin del diseño. El siguiente paso, si se aprueba, es implementar `EDA_Dirigido_Fase3.ipynb`
siguiendo esta estructura.*
