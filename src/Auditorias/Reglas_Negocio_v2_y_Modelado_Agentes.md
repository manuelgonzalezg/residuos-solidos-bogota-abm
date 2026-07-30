# Reglas de Negocio v2 y Modelado de Agentes — De la Evidencia del EDA al ABM
### Reglas de negocio trazables, parámetro por parámetro, ancladas a hallazgos reales del EDA
**Autores:** Manuel Alejandro González Gallego, Gloria Inés Robledo Ulloa — CUN
**Fecha de diseño:** 2026-07-10
**Insumos:** `notebooks/EDA_Dirigido_Fase3.ipynb` (con outputs ejecutados), `Plan_EDA.md`,
`Recoleccion_Datos_Fase2.md`, `Diseno_ABM.md`, `abm/config_abm.py` (estado actual)

> Este documento **es solo diseño** — no modifica ningún archivo de `abm/` todavía. Es la
> respuesta directa a lo que pediste: mostrar, parámetro por parámetro, cómo el EDA sostiene
> cada regla de negocio con evidencia real, y cómo eso se traduce en reglas concretas para cada
> agente.

---

## 1. Revisión desde el EDA hacia atrás — ¿es consistente toda la cadena?

Antes de tocar el ABM, se revisó que las 3 fases anteriores no se contradigan entre sí:

- **Fase 1 → Fase 2**: `df_modelo` (Fase 1) y las fuentes nuevas de Fase 2 comparten las mismas
  llaves (`CODIGO_UPZ`, `codigo_localidad`) y el mismo año de referencia — verificado en el EDA
  (`gdf_upz_actual`, 112 UPZ, sin pérdidas en los merges).
- **Fase 2 → Fase 3 (EDA)**: cada fuente de Fase 2 (RBL, RURO oficial, SIGAB, macrorutas, ECA
  microdato) se usó al menos una vez en el EDA y produjo un resultado con sentido de magnitud —
  **no de forma automática**: se encontraron y corrigieron 4 bugs reales durante la construcción
  del EDA (detallados en la respuesta anterior): un error de escala ~1000x en el parseo del RBL,
  una mala clasificación de esquema de operadores (2018-2019 mezclaban nomenclatura de "zonas" y
  "ASE"), códigos numéricos de la ECA sin traducir, y un archivo de PQRS que resultó ser un
  acumulado de 59 meses en vez de un corte puntual. **Los tres documentos de fases anteriores
  (`Analisis_Variables_Negocio.md`, `Recoleccion_Datos_Fase2.md`) siguen siendo válidos** — estos
  bugs estaban en el código de consolidación, no en las conclusiones ya documentadas.
**Conclusión de la revisión: la cadena es consistente y ya está verificada con datos reales —
se puede proceder a diseñar las reglas de negocio sobre ella con confianza.**

---

## 2. Principio rector

Cada parámetro que el ABM necesita se resuelve así, en orden de preferencia:

1. **¿Hay un dato real que lo mida directamente?** → se usa ese dato, con su nivel de agregación
   declarado (UPZ, localidad o ciudad).
2. **¿Hay un dato real que lo acote (rango plausible) aunque no lo mida directamente?** → se usa
   para poner límites a un parámetro libre, en vez de un valor arbitrario.
3. **¿No hay nada?** → sigue siendo un supuesto, pero ahora *declarado como tal explícitamente*,
   nunca mezclado con los dos casos anteriores.

Toda regla de esta lista está anclada a dato real o declarada explícitamente como supuesto.

---

## 3. Reglas de negocio, parámetro por parámetro (vs. `abm/config_abm.py` actual)

### 3.1 Índice de infraestructura — de sintético a real

**Antes:** `infraestructura_index_upz` se calculaba con una fórmula inventada
(`PESO_ESTRATO_BAJO_INFRAESTRUCTURA=0.5`, `PESO_DENSIDAD_INFRAESTRUCTURA=0.5`,
`INFRAESTRUCTURA_INDEX_MINIMO=0.2`) — un supuesto **consistente con la hipótesis pero no
verificado**, como decía honestamente `Diseno_ABM.md` §4.

**Ahora:** el EDA cruzó los 4 snapshots de SIGAB (puntos críticos por UPZ) y encontró:
- **Coeficiente de variación entre UPZ = 1.19** (jun-2026) — variación territorial fuerte, no
  uniforme. Esto confirma que la infraestructura *sí* debe tratarse como una fuente real de
  heterogeneidad territorial, no una constante.
- El patrón espacial es **estable en el tiempo**: el mismo clúster de UPZ (norte-centro) aparece
  como el de mayor concentración de puntos críticos en los 4 cortes (2020, dic-2022, dic-2024,
  jun-2026) — no es ruido de un solo corte.
- El mapa bivariado (estrato × puntos críticos) muestra que la relación **no es simplemente
  "estrato bajo = más puntos críticos"** — hay zonas de estrato medio-alto con concentración
  alta también. Esto **contradice parcialmente** el supuesto original de la fórmula sintética,
  que asumía que solo estrato bajo y densidad explican la infraestructura.

**Regla de negocio v2:** reemplazar la fórmula sintética por el conteo real de puntos críticos
por UPZ (normalizado 0-1 dentro del rango observado), tomado del snapshot más reciente con datos
completos. Como hay 4 cortes disponibles, se puede promediar o usar el más reciente — se
recomienda el promedio de los 4 para suavizar variación mes a mes, documentando que sigue siendo
un proxy (puntos críticos ≠ ausencia de infraestructura formal), no una medición directa de
"puntos limpios".

### 3.2 Capacidad de recolección por reciclador — sigue siendo un supuesto, pero ahora acotado

**Antes:** `CAPACIDAD_RECOLECCION_KG_DIA_POR_RECICLADOR = 15.0` — valor de partida sin ningún
dato real detrás.

**Ahora:** sigue sin existir un dato directo de productividad individual. Pero el EDA permite
una **cota agregada de consistencia**: con ~24,895 recicladores activos (RURO oficial) y una
recolección formal real de ~30,000 ton/mes por ASE (RBL consolidado, 5 ASE ≈ 150,000 ton/mes
formales en total), cualquier valor de capacidad individual que multiplicado por el número de
recicladores activos supere ampliamente el total formal sería implausible. Esto no fija el
número, pero permite **descartar valores absurdos** al calibrar (ej. 15 kg/día × 24,895
recicladores ≈ 11,200 ton/mes — del orden de un 7% de lo recolectado formalmente, un orden de
magnitud razonable, no descabellado).

**Regla de negocio v2:** se mantiene como parámetro libre de calibración, pero ahora con una
**cota superior explícita derivada de datos** (no debería, en agregado, superar una fracción
razonable de lo que recolecta el sistema formal) — a definir el % exacto en la fase de
calibración.

### 3.3 Parámetros de decaimiento/recuperación de actitud (free-riding) — evidencia parcial, sigue siendo supuesto

**Antes:** `BETA_DECAIMIENTO_SEPARACION=0.03`, `BETA_RECUPERACION_SEPARACION=0.02`,
`UMBRAL_PERCEPCION_IMPACTO=0.15`, `PROB_SEPARA_PISO=0.05` — los 4 sin ningún dato real.

**Ahora:** el EDA no puede medir una tasa de cambio de actitud (necesitaría datos
longitudinales por hogar, que no existen), pero sí aporta dos piezas nuevas:
- **La relación estrato↔separación es real y significativa** (chi² = 18.3, p = 0.0026, microdato
  ECA 2021, n=1,969 tras excluir NS/NR) — pero con una correlación modesta (r = 0.28 a nivel UPZ
  entre `estrato_promedio` y `pct_separa_en_fuente`). Esto sugiere que el estrato **influye pero
  no determina** la separación — consistente con que el mecanismo de imitación social (no solo
  estrato) explique parte de la varianza, como propone la hipótesis original.
- **`PROB_SEPARA_PISO` puede dejar de ser arbitrario**: el mínimo real observado de
  `pct_separa_en_fuente` entre localidades (excluyendo las de muestra mínima ya señaladas, Los
  Mártires n=1 y Santa Fe n=3) da un piso empírico más informado que 0.05.

**Regla de negocio v2:** mantener como parámetros libres (siguen sin dato longitudinal que los
mida), pero fijar `PROB_SEPARA_PISO` con el mínimo real observado en vez de un número inventado,
y documentar explícitamente que `BETA_DECAIMIENTO`/`BETA_RECUPERACION`/`UMBRAL_PERCEPCION` son
los 3 parámetros con **menor respaldo de datos de todo el modelo** — candidatos prioritarios
para análisis de sensibilidad en la fase de calibración, no para un valor fijo "de una vez".

### 3.4 Recolección formal como no-cuello-de-botella — ahora con evidencia, no solo supuesto

**Antes:** `CAPACIDAD_FORMAL_NO_VINCULANTE = True` — asumido porque "la cobertura formal es
históricamente casi universal" (`Diseno_ABM.md` §4), sin serie real que lo mostrara.

**Ahora:** el RBL consolidado (2,240 filas, 2018-2026, corregido) muestra una recolección
domiciliaria **estable mes a mes por ASE** (~26,000-50,000 ton/mes según el ASE, sin caídas de
capacidad ni saturación visible a lo largo de 8 años) — el supuesto se sostiene con evidencia
real, no solo se mantiene por conveniencia.

**Regla de negocio v2:** se conserva `CAPACIDAD_FORMAL_NO_VINCULANTE = True`, ahora citando el
RBL consolidado como evidencia, no `Diseno_ABM.md` como única justificación.

### 3.5 Incentivo económico — parámetro completamente NUEVO, no existía en el ABM

El ABM actual no tiene ningún mecanismo económico. El EDA trajo, por primera vez, datos reales:

- **VIAT = $11,388/tonelada** (Ciudad Limpia, ASE 3, dic-2025) — el incentivo real al
  aprovechamiento.
- **Factor de subsidio/contribución por estrato** (real, normativo CRA): -70%/-40%/-15%/0%/+50%/+60%
  para estratos 1-6.
- **Factor de incentivo ponderado por UPZ** (calculado en el EDA combinando lo anterior con la
  composición real de estratos): rango de **-0.67 (más subsidiado) a +0.54 (más contribuyente)**,
  mediana -0.17 — es decir, la UPZ típica de Bogotá recibe subsidio neto, no lo paga.

**Regla de negocio v2 (mecanismo nuevo a proponer, no solo un ajuste):** agregar un atributo
`factor_incentivo_upz` a `EntornoUPZ`, calculado directamente de datos reales (no sintético), que
module — como hipótesis a probar, no como verdad impuesta — la probabilidad de separación o la
participación de recicladores informales, ya que un subsidio más alto podría (o no) asociarse
con mayor/menor comportamiento pro-separación. Esto es exactamente el tipo de pregunta que un
ABM puede explorar y que antes ni siquiera estaba representada.

### 3.6 Formalización de recicladores — atributo nuevo, con un hallazgo que cambia la interpretación

**Antes:** `PoblacionRecicladoresUPZ` solo tenía conteo y edad promedio — "agente
simplificado/estilizado" por falta de dato, según `Diseno_ABM.md` §1.

**Ahora, con RURO oficial:**
- **89.9% de los recicladores registrados en el RURO están "Activos"** (vs. Retirados).
- **Pero la afiliación real a ARL (riesgos laborales) es prácticamente 0%** en 14 de 18
  localidades, y nunca supera 14.3% (Los Mártires, n=7, muestra mínima) — el hallazgo más
  importante de esta sección.

**Esto es un matiz que el ABM debe representar explícitamente:** "Activo en el RURO" **no
equivale a "formalizado" en el sentido de protección laboral** — son dos cosas distintas que se
estaban tratando implícitamente como una sola. Esto en realidad **refuerza** el mecanismo #2 de
la hipótesis original del notebook (recicladores operando sin coordinación institucional
plena), con evidencia real detrás por primera vez.

**Regla de negocio v2:** agregar dos atributos distintos a `PoblacionRecicladoresUPZ`:
`pct_registro_activo` (≈90%, alto) y `pct_formalizacion_laboral` (≈0-14%, bajo) — en vez de una
sola noción de "formalización", porque los datos muestran que son cosas distintas.

---

## 4. La discrepancia de 4 vs. 5 actores — resuelta con evidencia, recomendación explícita

`Analisis_Variables_Negocio.md` §2.1 dejó esto abierto. El EDA (sección 6, `Plan_EDA.md` §6) dio
la evidencia que faltaba: **coeficiente de variación de puntos críticos entre UPZ = 1.19**, muy
por encima del umbral de 0.5 que se había propuesto como referencia de "condición uniforme".

**Recomendación:** mantener los **5 actores** del notebook original y `Diseno_ABM.md`
(agregando infraestructura/puntos limpios como mecanismo propio), no los 4 del proyecto de grado
formal — con este documento como la evidencia que sustenta la decisión, para poder defenderla
explícitamente ante el comité en vez de dejarla como una discrepancia sin resolver.

> **✅ Decisión final implementada (2026-07-11):** los 5 actores quedaron formalizados en
> código, cada uno con su fuente de datos real:
> 1. **Hogares** (`abm/agentes_hogar.py`) — 75,273 agentes, con `participacion_comunitaria` real (EM2021).
> 2. **Recicladores de oficio** (`abm/agentes_reciclador.py`) — 112 poblaciones (una por UPZ), con `pct_registro_activo` y `pct_formalizacion_laboral` reales (RURO 2022).
> 3. **Operadores del servicio de aseo** (`abm/agentes_infraestructura.py::OperadorUAESP`) — 5 agentes (uno por ASE), con capacidad diaria real (RBL consolidado) — ya no un stub sin instanciar.
> 4. **Infraestructura/puntos limpios** (`EntornoUPZ.infraestructura_index`) — ya no sintética: promedio real de puntos críticos de SIGAB en 4 cortes de tiempo.
> 5. **Relleno Sanitario Doña Juana** (`RellenoSanitarioDJ`) — sin cambios, ya usaba datos reales.
>
> Además, se agregó el mecanismo de **incentivo económico** (`EntornoUPZ.factor_incentivo`,
> VIAT + tarifas CRA reales) que no corresponde a un actor nuevo, sino a una regla de negocio
> real que modula el comportamiento de los actores existentes.

---

## 4bis. Auditoría posterior: ¿el EDA respondió realmente todo lo necesario para modelar hogares?

Después de entregar este documento, se hizo una auditoría explícita de una omisión real: el EDA
había usado la **Encuesta de Cultura Ambiental (ECA 2021)** para las preguntas de comportamiento,
pero **nunca había analizado la Encuesta Multipropósito (EM 2021)** — son dos encuestas
distintas (ECA: ~2,282 personas, específica de ambiente; EM: ~234,000 hogares, socioeconómica
general) — pese a que en la Fase 2 se había invertido trabajo en ampliar
`COLUMNAS_MULTIPROPOSITO` de 16 a 40 columnas (educación, ingreso, informalidad, tenencia,
tamaño del hogar, participación comunitaria) que nunca llegaron a usarse en ningún gráfico.

Se corrigió agregando la Sección 8 al notebook (`EDA_Dirigido_Fase3.ipynb`): una **regresión
logística multivariada** (no solo cruces de a dos variables, que confunden el efecto de una
variable con el de otra correlacionada) prediciendo si el hogar separa residuos, controlando
estrato, educación, ingreso, informalidad, tamaño del hogar, tenencia de vivienda y participación
comunitaria — todas al mismo tiempo.

**Segunda corrección, encontrada por una pregunta directa del usuario tras la primera versión de
este documento:** la primera corrida de la regresión (y del chi² de la Sección 1) **no usaba el
factor de expansión de la encuesta** (`FEX_C` en EM2021, `PONDERADOR` en ECA2021) — es decir,
describía la muestra, no la población real de Bogotá por estrato/UPZ/localidad. Se verificó que
ambos factores son reales y están bien escalados (`FEX_C` suma ~7.84 millones, consistente con
población de Bogotá) y se re-corrió **todo** con y sin ponderar para comparar. Resultado
ponderado, el que se usa de aquí en adelante (n=60,235 hogares en la muestra, representando
2,061,804 personas/hogares-equivalentes reales; McFadden Pseudo R² sin ponderar=0.055):

| Variable | Odds ratio (ponderado) | Odds ratio (sin ponderar) | ¿Influye controlando por las demás? |
|---|---|---|---|
| Participación en Junta de Acción Comunal | **2.63** | 2.05 | **Sí** — el efecto más fuerte al ponderar |
| Participación en organización ambiental | **2.33** | 2.98 | **Sí** — sigue fuerte, aunque baja al ponderar |
| Vivienda propia (vs. arrendada) | 1.40 | 1.38 | **Sí** |
| Estrato | 1.37 | 1.39 | **Sí** |
| Personas por hogar | 1.13 | 1.12 | **Sí**, modesto |
| Educación | 1.13 | 1.13 | **Sí**, modesto |
| Informalidad laboral | 0.85 | 0.81 | **Sí, en sentido negativo** |
| Ingreso (log) | 1.00 | 1.01 | **No** (p=0.33 ponderado — aún más claramente no-significativo que antes) |

**Qué cambió al ponderar (honesto, no se esconde):** las dos variables de participación
comunitaria **intercambiaron cuál es más fuerte** (JAC pasa a ser el efecto #1, no ambiental) y
ambas bajaron de magnitud — la muestra sin ponderar sobrerrepresentaba personas muy
participativas. El chi² de estrato×separación (Sección 1, ECA) también bajó de chi²=18.3/p=0.0026
a chi²=14.0/p=0.0156 al ponderar — sigue siendo significativo, pero con menos margen. **Ninguna
conclusión cualitativa cambió de dirección** (todo lo que era significativo lo sigue siendo, en
la misma dirección), pero las magnitudes exactas sí — y son las ponderadas las que hay que citar
en la tesis, no las crudas.

**Hallazgo más importante de toda esta auditoría (se sostiene tras ponderar):** la
**participación comunitaria (JAC, organizaciones ambientales) es el predictor más fuerte de
todos**, por encima incluso del estrato — algo que ni el ABM actual ni `Diseno_ABM.md`
representan de ninguna forma. Y el **ingreso por sí solo no añade nada** una vez se controla por
estrato/educación/informalidad (más claro aún al ponderar) — es decir, el mecanismo real no es
"tener más plata", sino la combinación de condición socioeconómica estructural (estrato,
educación, tenencia) **más** integración comunitaria.

**Nota de honestidad estadística que aplica a toda esta sección:** ponderar con `FEX_C`/
`PONDERADOR` corrige la representatividad de las proporciones y coeficientes, pero **no**
corrige los errores estándar por el diseño muestral complejo original (estratificación,
conglomerados) — un ajuste que requeriría el diseño muestral completo del DANE/SCRD (no
disponible) o un paquete de encuestas complejas (ej. R `survey`, Python `samplics`). Para este
EDA, los p-valores ponderados son la mejor aproximación disponible y suficientes para ver
dirección y magnitud — no se deben citar como el error estándar exacto de una encuesta
compleja.

**Sobre edad y "sector":** se buscó explícitamente una variable de edad individual en el
diccionario oficial de EM2021 y no se encontró ninguna ya extraída en `COLUMNAS_MULTIPROPOSITO`
— la estructura de edad de la población sigue existiendo en `df_modelo` (pirámide demográfica
DANE por UPZ), pero no vinculada al nivel individual de la respuesta de separación. Se deja como
hueco explícito. "Sector" se interpretó como sector ocupacional/informalidad (`OINFORMAL`), ya
cubierto arriba — si te referías a sector geográfico, ya está cubierto por estrato/UPZ/localidad
en todo el EDA.

**Regla de negocio v2 (actualiza la sección 3.3):** agregar `participacion_comunitaria` como
atributo del `HogarAgente` — con el respaldo empírico más fuerte de todo el EDA, es más
justificable que muchos de los parámetros que ya estaban en el modelo. La imitación social del
mecanismo #1 de la hipótesis puede ahora operacionalizarse, en parte, como función de esta
variable real, no solo del promedio de vecinos.

---

## 4ter. Cómo modelar a los recicladores — de un objeto agregado a heterogeneidad real

**Estado actual:** `PoblacionRecicladoresUPZ` es **un solo objeto por UPZ** (no un agente por
persona), con conteo y edad promedio como únicos atributos — deliberadamente simplificado por
falta de dato, según `Diseno_ABM.md` §1.

**Lo que cambió con RURO 2022 (Fase 2):** ahora existen datos categóricos por combinación
Estado/localidad/rango de edad/tipo de vivienda/salud/nivel educativo — no por individuo con
identificador único, pero sí agrupado en 339 combinaciones (18 localidades), suficiente para
construir una **distribución de perfiles**, no solo un promedio.

**Propuesta concreta (mantener el nivel de agregación por UPZ, pero enriquecer su composición
interna):**

No se recomienda pasar a un agente por cada uno de los ~24,895 recicladores activos — el mismo
argumento de `Diseno_ABM.md` §3 sobre hogares aplica aquí: sería computacionalmente costoso sin
beneficio real, porque el dato de RURO 2022 sigue siendo agrupado, no individual (no hay ruta,
ingreso ni productividad por persona). En cambio, se propone que `PoblacionRecicladoresUPZ`
mantenga su naturaleza de "población" pero con **una distribución interna de formalización**, no
un solo número:

- `pct_registro_activo` (~90%, real, RURO oficial) — ya en la sección 3.6.
- `pct_formalizacion_laboral` (~0-14% con ARL, real, RURO 2022 por localidad) — la variable que
  más cambia el comportamiento esperado del agente: una población con formalización casi nula se
  comporta de forma más consistente con el mecanismo #2 de la hipótesis original (competencia
  desorganizada por el material, sin coordinación institucional) que con un mercado ordenado.
- `distribucion_tipo_vivienda` y `distribucion_salud` (RURO 2022) quedan documentadas como datos
  disponibles para una extensión futura (ej. si se quisiera modelar vulnerabilidad económica del
  agente reciclador), pero **no se recomienda incluirlas en el MVP de esta ronda** — no hay
  todavía un mecanismo de comportamiento claro que las use, y agregarlas sin uso sería inflar el
  modelo sin sustento.

---

## 4quater. Cómo modelar rutas, camiones, operadores y el Relleno Doña Juana

Este es el bloque que el ABM actual **no modela en absoluto** — `OperadorUAESP` es un stub sin
instanciar, y la recolección formal es un "proceso de fondo sin restricción de capacidad"
(`Diseno_ABM.md` §4). Con los datos de Fase 2, esto puede cambiar, pero con matices importantes.

### Rutas (macrorutas reales, 125 zonas de recolección + 179 de barrido)

**Sí se puede modelar la estructura espacial real** — cada macrorruta tiene una geometría, una
localidad y una frecuencia semanal real (ej. "Lunes a Sábado", "Martes-Jueves-Sábado"). Esto
permite reemplazar el supuesto "la recolección formal siempre pasa" por una regla más fina:
**la frecuencia de paso varía por zona**, y esa variación es un dato real, no un supuesto.

**Propuesta:** agregar `frecuencia_recoleccion_upz` a `EntornoUPZ` (derivada del join espacial
macrorruta↔UPZ, mismo patrón que ya se usó para puntos críticos en el EDA), como un modulador
adicional de cuánto material se recoge por período — sin necesidad de modelar camiones
individuales.

### Camiones y operadores — la recomendación es NO modelar camiones individuales

**Por qué no:** no existe ningún dato de capacidad de camión, número de viajes/día, ni tiempo de
ruta, en ninguna fuente (interna o externa) encontrada en la Fase 2. Modelar camiones
individuales sin esos datos sería inventar una capa entera de supuestos.

**Qué sí se puede hacer con lo que hay:** el RBL consolidado da la **capacidad real agregada
mensual por ASE** (ej. ASE 2 LIME ≈ 47,000-50,000 ton/mes, estable 2018-2025) — esto es
suficiente para instanciar `OperadorUAESP` como **un agente por ASE (5 agentes, no cientos de
camiones)**, cada uno con una capacidad mensual tomada del promedio histórico real de su ASE,
en vez de "sin restricción" como hoy. Esto es una mejora real y barata: pasa de "el operador
formal nunca es cuello de botella" (supuesto) a "el operador formal tiene una capacidad medida
empíricamente, que en la práctica casi nunca se satura" (mismo comportamiento esperado, pero
ahora verificable en vez de asumido).

### Relleno Sanitario Doña Juana — ya tiene lo que necesita, solo falta conectarlo mejor

`RellenoSanitarioDJ` ya existe como sumidero único en el ABM, usando `residuos_pidj` (serie real
de disposición anual). No se propone ningún cambio estructural aquí — el EDA no encontró ninguna
fuente nueva sobre capacidad remanente, tasa de llenado ni vida útil del relleno (fuera del
alcance de lo que se buscó en la Fase 2, y no es una prioridad para la pregunta de investigación,
que es sobre aprovechamiento, no sobre disposición final). Se deja documentado como límite
conocido, no como algo que este documento resuelve.

---

## 5. Resumen: mapa de cambios implementados en `abm/` (2026-07-11)

| Archivo | Cambio | Estado |
|---|---|---|
| `abm/config_abm.py` | `PROB_SEPARA_PISO` = 0.5916 (mínimo real observado, Kennedy n=191) en vez de 0.05 | ✅ Implementado |
| `abm/datos_reales.py` (**nuevo módulo**) | Precalcula y cachea en `data/processed/16-19_*.csv`: infraestructura real (SIGAB), participación comunitaria (EM2021), formalización de recicladores (RURO 2022), capacidad real por ASE (RBL) | ✅ Implementado |
| `abm/agentes_infraestructura.py` | Fórmula sintética reemplazada por promedio real de puntos críticos SIGAB (4 cortes de tiempo) | ✅ Implementado |
| `abm/entorno.py` (`EntornoUPZ`) | Agregados `factor_incentivo` (tarifas CRA reales), `pct_participacion_comunitaria`, `pct_registro_activo_reciclador`, `pct_formalizacion_laboral_reciclador` | ✅ Implementado |
| `abm/agentes_hogar.py` (`HogarAgente`) | Agregado `participacion_comunitaria` — se muestrea por agente con la tasa real de su localidad, y ajusta `prob_separa_base` vía el odds ratio real medido en el EDA (2.48) | ✅ Implementado |
| `abm/agentes_reciclador.py` | Separados `pct_registro_activo` (~90-100%) y `pct_formalizacion_laboral` (~0-14%, ARL) | ✅ Implementado |
| `abm/agentes_infraestructura.py` (`OperadorUAESP`) | Ya no es un stub — 5 agentes (uno por ASE), capacidad diaria real (RBL): 38,913 ton/día en total | ✅ Implementado |
| `abm/modelo.py` | `_recoleccion_formal()` reemplaza `_recoleccion_formal_no_vinculante()` — usa la capacidad real como techo agregado de ciudad | ✅ Implementado |
| Relleno Doña Juana (`RellenoSanitarioDJ`) | Sin cambios — ya usaba datos reales | — |
| `abm/dashboard.py` | Reconstruido por completo: mapa real de Bogotá (112 UPZ, geometría oficial) en vez de grafo abstracto, 7 paneles reactivos en tiempo real | ✅ Implementado |

**Verificación de extremo a extremo (2026-07-11):** modelo construido en 1.5s (75,273 hogares +
112 poblaciones de recicladores + 5 operadores ASE), simulación de 365 días corrida sin errores
en 78s, balance de masa exacto (generado = aprovechado + rechazo), capacidad formal usada ~3.5%
(confirma que casi nunca se satura, tal como predijo el EDA), % de aprovechamiento sin calibrar
= 31.5% (orden de magnitud razonable frente al 48.5% real de 2025 y el ~18-20% histórico
pre-2024). Dashboard verificado corriendo (HTTP 200, sin errores en el log del servidor) —
**la verificación visual en navegador queda pendiente de que el usuario la confirme
directamente**, no se puede comprobar el renderizado real desde este entorno.

> **⚠️ Nota de actualización 2 (2026-07-11):** más allá de solo descartar el 48.5%, se calibró el
> ABM contra los 6 puntos reales 2018-2023 (RMSE≈1.1pp) y se usó para proyectar un
> **contrafactual 2024 = 18.29%** — sin ningún mecanismo de la reforma regulatoria de 2024 — frente
> al 43.88% oficial. Ver `Investigacion_Salto_Aprovechamiento.md` §7 para la metodología completa
> (decomposición shift-share, encadenamiento multi-año, brecha intención-acción, hallazgo de
> no-identificabilidad de los otros 4 parámetros libres) y dos bugs de datos reales corregidos en
> el camino (parseo RBL 2020, capacidad ASE ~12x sobreestimada por un error de unidades).

> **⚠️ Nota de actualización 3 (2026-07-13):** la "no-identificabilidad" de los 4 parámetros
> libres mencionada arriba resultó ser, en realidad, DOS BUGS de mecanismo — el disparador de
> decaimiento de `agentes_hogar.py` comparaba contra un umbral absoluto inalcanzable (ninguna de
> las 204 cohortes reales lo cruzaba nunca) y el piso de decaimiento no estaba reescalado por la
> brecha intención-acción (bloqueaba el 99.65% de los agentes). Con ambos corregidos, el modelo
> por fin tiene dinámica real día a día (antes: TODAS las series salían perfectamente planas).
> Se recalibró completo: `factor_brecha`=0.60, `beta_decaimiento`=0.04, `umbral`=0.035 (relativo).
> Contrafactual 2024 actualizado a **18.43%** (antes 18.29%, con el mecanismo roto) — la brecha
> frente al 43.88% oficial se mantiene (~25.5pp), la conclusión central no cambia, ahora está
> mejor sustentada. Ver `Investigacion_Salto_Aprovechamiento.md` §8 para el detalle completo.

> **⚠️ Nota de actualización 4 (2026-07-14):** auditoría de fondo pedida explícitamente por el
> usuario (caso MATSim como referencia), sobre unidad espacial y origen de parámetros. Dos
> hallazgos nuevos, ambos documentados a fondo en `Justificacion_Metodologica_Comite.md` (nuevo):
> (1) `prob_separa_base` es real solo a nivel LOCALIDAD (20), no UPZ — UPZ lo hereda, no lo mide;
> el dashboard ahora tiene un selector "UPZ/Localidad" para mostrar ambas resoluciones. (2) De los
> 6 predictores reales y significativos de la regresión de §4bis, solo participación comunitaria
> estaba conectada al ABM — se agregaron `vivienda_propia` (OR=1.40) e `informal` (OR=0.85) como
> heterogeneidad real dentro de cada cohorte. Nota técnica importante: el primer intento (aplicar
> los odds ratios directo sobre `prob_separa_base`, igual que participación comunitaria) rompió el
> RMSE (1.15pp→4.25pp) porque `prob_separa_base` también gobierna el disparador NO LINEAL de
> decaimiento — variar su varianza cambia cuántos agentes cruzan el umbral, aunque el promedio se
> preserve. Se corrigió aplicando la heterogeneidad como un multiplicador de SALIDA separado
> (`factor_heterogeneidad_hogar`, normalizado a promedio 1.0 por cohorte), que no toca el
> mecanismo de decaimiento calibrado. También se corrigió que
> `construir_o_cargar_participacion_comunitaria()` no ponderaba por `FEX_C` pese a que §4bis ya
> había demostrado que eso importa. Ver `Justificacion_Metodologica_Comite.md` §5 para el detalle
> completo, incluyendo la verificación numérica de que el RMSE se mantiene tras el rediseño.

> **⚠️ Nota de actualización 5 (2026-07-14, ronda 5):** `pct_separa_en_fuente` (ECA2021, real
> solo a localidad, 20, con Los Mártires n=1 y Santa Fe n=3) deja de alimentar el ABM. Se
> encontró que EM2021 trae `COD_UPZ_GRUPO` — geografía UPZ real, nunca antes extraída — y se
> construyó `abm/datos_reales.py::construir_o_cargar_separacion_upz_em2021()`: 112 de 112 UPZ
> reales cubiertas (crosswalk verificado sin conflictos), cada una con 600-1,300+ hogares de
> muestra propia (`NHCCP38`, ponderado por `FEX_C`). Spot-check: las UPZ de Los Mártires y Santa
> Fe (antes 100%/33.33% heredado de una muestra degenerada) ahora muestran 33-67%, un rango
> creíble y con variación real UPZ a UPZ dentro de la misma localidad. Se recalibró el modelo
> completo (nivel de ciudad pasó de 71.87% ECA2021 a ~74.5% EM2021, un cambio moderado) — ver
> `Justificacion_Metodologica_Comite.md` §5bis para el detalle completo y el RMSE resultante.

> **⚠️ Nota de actualización (2026-07-11):** el 48.50% (2025) citado arriba como referencia de
> orden de magnitud quedó **superado** tras `Investigacion_Salto_Aprovechamiento.md` — resultó
> ser la salida de un modelo econométrico de la UAESP, no una medición directa, con un salto sin
> explicación causal de 18.56% (2023) a 43.88% (2024) que coincide con el Decreto 1381/2024 y el
> nuevo PGIRS 2024-2028. `config.APROVECHAMIENTO_GROUND_TRUTH_PCT` (y el dashboard) ahora usan
> **18.56% (2023)** como objetivo real de calibración. Se conserva el texto original de esta
> verificación sin reescribir, para que quede trazable que la decisión cambió en este punto.

---

## 6. Lo que sigue sin poder resolverse (honesto, no se fuerza)

- Capacidad real de recolección individual de recicladores — sigue siendo supuesto, ahora acotado.
- Los 3 parámetros de decaimiento/recuperación de actitud — sin dato longitudinal, seguirán
  siendo los más débiles del modelo (aunque ahora `participacion_comunitaria` da un mejor
  fundamento empírico al mecanismo de imitación social que los sostiene).
- El efecto real del incentivo económico sobre el comportamiento (sección 3.5) es una hipótesis
  nueva a *probar* con el ABM, no un hecho ya confirmado por el EDA.
- **Edad individual del respondente**: no se encontró una columna ya extraída en EM2021 — la
  estructura de edad de la población sigue existiendo a nivel UPZ (pirámide DANE), no vinculada
  al comportamiento individual de separación.
- **Camiones individuales, rutas óptimas y viajes/día**: deliberadamente NO se modelan — ningún
  dato real los sostiene (§4quater). `OperadorUAESP` se propone a nivel de ASE (5 agentes), no
  de vehículo.
- **Capacidad remanente del Relleno Doña Juana**: sin fuente nueva encontrada; el sumidero sigue
  funcionando solo como acumulador de balance de masa, no como una restricción de capacidad.

---

*Fin del diseño. Si apruebas esta dirección, el siguiente paso es implementar la tabla de la
sección 5 en `abm/`.*
