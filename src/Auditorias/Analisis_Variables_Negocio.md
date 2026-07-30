# Análisis de Contexto de Negocio e Inventario de Variables
### Comité de tesis — reconciliación de documentos oficiales vs. lo ya construido
**Autores:** Manuel Alejandro González Gallego, Gloria Inés Robledo Ulloa — CUN
**Documentos fuente de este análisis:**
1. `ACA1_Analítica de Datos para la toma de decisiones .docx` (Drive, fase de avance intermedio)
2. **"Análisis de las dinámicas emergentes del sistema socio-técnico de gestión de residuos sólidos urbanos en Bogotá mediante un enfoque integrado de análisis exploratorio de datos y simulación basada en agentes"** — proyecto de grado formal, Especialización en Analítica de Datos, director Mariano Esteban Romero Torres, Bogotá, febrero de 2026 (documento compartido directamente, el más completo y autoritativo de los dos).

> Este documento **no modifica código ni toma decisiones de implementación**. Es un análisis de
> reconciliación entre lo que los documentos oficiales del proyecto dicen que se debe lograr, y
> lo que efectivamente existe hoy en el pipeline (`src/`, `abm/`, `data/processed/`). El siguiente
> paso lo define el usuario después de leer esto.

---

## 1. Contexto de negocio reformulado

### 1.1 Qué es el proyecto, en sus propias palabras

El proyecto de grado formal define el problema así (cita textual, Resumen):

> "La gestión de residuos sólidos urbanos en Bogotá representa un desafío propio de los sistemas
> socio-técnicos complejos, en los que el comportamiento del sistema no puede explicarse
> únicamente a partir del análisis aislado de sus componentes, sino de las interacciones
> dinámicas entre hogares, recicladores, operadores del servicio público, infraestructura,
> regulación y decisiones institucionales."

Y la **pregunta de investigación formal** (cita textual, §2.1):

> "¿Cómo las interacciones entre los actores y sus reglas de comportamiento dentro del sistema
> urbano de gestión de residuos sólidos de Bogotá generan las dinámicas emergentes que
> condicionan el aprovechamiento de los residuos y bajo qué escenarios de intervención dichas
> dinámicas podrían modificarse para mejorar el desempeño del sistema?"

**Objetivo general** (cita textual, §3.1):

> "Analizar las dinámicas emergentes del sistema socio-técnico de gestión de residuos sólidos
> urbanos en Bogotá mediante la integración del análisis exploratorio de datos y la simulación
> basada en agentes, con el fin de comprender cómo los comportamientos e interacciones entre los
> actores influyen en la persistencia de bajos niveles de aprovechamiento."

**Objetivos específicos** (cita textual, §3.2) — estos 4 puntos son la hoja de ruta real del proyecto de grado:
1. Analizar la información histórica mediante EDA para identificar patrones espaciales/temporales, relaciones entre variables e indicadores críticos de generación, separación, aprovechamiento y disposición final.
2. Identificar y caracterizar los principales actores del sistema, sus comportamientos, interacciones y reglas de decisión, a partir de datos y literatura.
3. Construir un modelo ABM simplificado, con reglas fundamentadas en evidencia empírica y supuestos explícitos.
4. Analizar mediante escenarios de simulación el efecto de cambios en comportamiento/variables estratégicas sobre el aprovechamiento.

### 1.2 El documento ACA1 (avance intermedio) — decisión de negocio complementaria

El ACA1, redactado en una fase anterior del mismo proyecto, formula la decisión de negocio de forma más acotada (cita textual):

> "identificar qué variables sociales, económicas, demográficas y territoriales presentan mayor
> relación con las prácticas de separación de residuos en los hogares de Bogotá, permitiendo
> orientar futuras estrategias de educación ambiental, focalización territorial e implementación
> de políticas públicas."

Y aclara explícitamente el orden de las fases:

> "El objetivo principal del proyecto no consiste en desarrollar un modelo predictivo
> tradicional, sino construir la base de información necesaria para implementar una futura
> Modelación Basada en Agentes... La fase predictiva será desarrollada posteriormente, una vez
> concluya el análisis exploratorio y se definan formalmente las variables objetivo y las
> relaciones causales."

**Ambos documentos son coherentes entre sí**: el ACA1 es una foto de un momento más temprano del mismo proyecto que hoy tiene el proyecto de grado formal como versión madura. No hay contradicción real, solo distinto nivel de detalle — el proyecto de grado formal es la fuente autoritativa para todo lo que sigue en este análisis.

### 1.3 El problema y qué se busca lograr, en términos simples

- Bogotá genera ~7.000 toneladas de residuos al día; solo se aprovecha ~15% (cita: UAESP 2021, Contraloría de Bogotá 2022); el resto va al Relleno Sanitario Doña Juana.
- Existen normas, infraestructura y actores especializados, pero el aprovechamiento sigue bajo — el proyecto de grado sostiene que esto pasa porque el sistema es socio-técnico complejo: el resultado agregado no se explica por un solo componente, sino por cómo interactúan los hogares, los recicladores, los operadores y el gobierno.
- **La fase actual (donde estamos)** es explícitamente de análisis exploratorio + preparación de datos + identificación de variables explicativas — el ABM es el objetivo específico #3, la última pieza a construir, no la primera.

---

## 2. Reconciliación con lo que ya se construyó (hallazgos, no correcciones)

Esta sección señala discrepancias entre los documentos oficiales y el trabajo técnico ya hecho (notebook de EDA, `Diseno_ABM.md`, MVP del ABM). Son **hallazgos para que el usuario decida**, no se corrige nada aquí.

### 2.1 Actores del modelo: 4 (tesis formal) vs. 5 (notebook / Diseño_ABM.md)

El proyecto de grado formal declara explícitamente **4 tipos de actores** (cita textual, §6.3.4 y §5.1, repetido en Tabla 2 del marco conceptual):

> "Hogares, como generadores primarios... Recicladores de oficio... Operadores del servicio de
> aseo, responsables de la recolección y el transporte... Gobierno local, encargado de la
> regulación, planeación, monitoreo y diseño de políticas públicas."

El notebook de EDA (celda de markdown inicial) y `Diseno_ABM.md` (ya construido en la fase anterior de esta conversación) declaran **5 agentes**, agregando "puntos de entrega limpia y bodegas de reciclaje" como un tipo de actor propio, y tratando el Relleno Sanitario Doña Juana como un agente-sumidero explícito en vez de solo infraestructura de destino.

**Esto no es necesariamente un error** — el proyecto de grado formal trata la infraestructura de puntos limpios como una variable/condición del sistema, no como un actor con reglas de decisión propias, mientras que el diseño técnico ya hecho la elevó a agente para poder representar el mecanismo de inequidad territorial. Es una decisión de modelado válida en ambos sentidos, pero **hoy hay una discrepancia real entre el documento formal del proyecto y el diseño técnico ya construido**, que conviene resolver explícitamente (¿se ajusta el ABM a los 4 actores formales, o se documenta por qué el ABM amplía a 5?).

### 2.2 La hipótesis del "mecanismo triple" no aparece, tal cual, en ningún documento oficial

El notebook de EDA cita una hipótesis específica de tres mecanismos (free-riding, recicladores sin coordinación, infraestructura inequitativa) apoyada en Ostrom (1990), Calvo-Salazar et al. (2005) y Fiksel (2012). **Ninguno de los dos documentos de negocio revisados aquí cita esas tres fuentes ni formula esa hipótesis de tres mecanismos textualmente.** El proyecto de grado formal sí cita a Ostrom, pero la referencia real en su lista bibliográfica es "Ostrom, 2009" (no 1990), y aparece solo una vez, de forma general, sin la hipótesis de tres mecanismos.

Esto sugiere que la hipótesis del "mecanismo triple" es una **operacionalización propia de los autores**, hecha al construir el notebook, más específica que lo que el documento de grado formal exige — no necesariamente incorrecta, pero **no está textualmente respaldada por las fuentes citadas en el documento oficial del proyecto**, lo cual un comité de tesis normalmente señalaría y pediría sustentar con las citas correctas o replantear con las fuentes que sí están en la bibliografía oficial (Geels 2004, Holland 2006, Bonabeau 2002, Gilbert 2008, An et al. 2021, Wilson et al. 2015, Cervantes & Palacios 2019, entre otras).

### 2.3 Punto de alineación real (no todo son discrepancias)

El proyecto de grado formal, en su sección de población y muestra (§7.4.3), describe la estrategia de muestreo del ABM así (cita textual):

> "la muestra no corresponde a individuos reales específicos, sino a una **población sintética**,
> construida a partir de parámetros empíricos derivados del análisis de datos... lo que permite
> reproducir comportamientos plausibles sin necesidad de modelar exhaustivamente a cada actor
> real."

Esto **coincide exactamente** con la decisión de diseño ya tomada en `Diseno_ABM.md` (muestra representativa de hogares con peso de escalamiento, no un agente por cada hogar real ni tampoco 3 cohortes agregadas). Vale la pena que el usuario sepa que esa decisión técnica ya está respaldada textualmente por su propio documento de grado.

### 2.4 Variables clave que el documento formal exige — Tabla 2 y §6.2.4

El marco teórico identifica 6 categorías de variables explicativas (cita textual, §6.2.4):

> "(i) nivel de separación en la fuente y calidad de la separación; (ii) estructura y eficiencia
> de la recolección y la logística; (iii) capacidad y formalización de los recicladores de
> oficio; (iv) gobernanza institucional y coordinación intersectorial; (v) incentivos económicos
> y condiciones del mercado para materiales reciclables; y (vi) factores socio-demográficos y
> territoriales (estrato, densidad, hábitos)."

Estas 6 categorías, junto con las categorías de variables de la Encuesta Multipropósito que el ACA1 dice haber seleccionado (características socioeconómicas, composición del hogar, condiciones habitacionales, prácticas de separación, percepción ambiental, participación comunitaria, educación, ingresos laborales, informalidad, condiciones territoriales, pago del servicio de aseo), son la base del inventario de la sección 3.

---

## 3. Inventario de variables por categoría

**Leyenda:** ✅ Ya integrado en `df_modelo` / pipeline actual — 🟡 Disponible en `data/raw/` (verificado en el diccionario oficial y en el header real de `em2021.csv`) pero **no extraído** por `src/carga_datos.py` — ❌ No existe en ninguna fuente disponible localmente.

| Categoría (según ACA1 / marco teórico) | ✅ Ya tenemos | 🟡 Disponible, no extraído | ❌ No existe |
|---|---|---|---|
| **Separación en la fuente y calidad** | `pct_separa_en_fuente`, `pct_calidad_separacion`, `prob_separa` (de `05_actores.csv`, agregado por localidad); serie histórica de aprovechamiento 2018-2025 | — | Separación **por estrato dentro de una misma UPZ** (solo existe a nivel localidad, ver Revisión de Fase 1) |
| **Composición del hogar** | `Total`, `HOGARES`, pirámide demográfica por edad/sexo (`df_modelo`) | `NHCCPCTRL2` (número de personas del hogar) — nombrada en el `select()` original del notebook, no extraída hoy | — |
| **Condiciones habitacionales** | `estrato_promedio`, `pct_estrato_bajo/medio/alto`, `clasificacion_social` | `NVCBP10` (tipo de vivienda), `NVCBP4` (vivienda en conjunto residencial), `NVCBP9` (espacio de negocio en la vivienda), `NHCCP35` (número de cuartos) — todas nombradas en el `select()` original, no extraídas hoy | — |
| **Recicladores de oficio** | `num_recicladores_ruro`, `edad_promedio_reciclador` (de RURO, agregado por localidad) | — | Rutas, volumen recogido, ingresos individuales de recicladores (ni siquiera el RURO los trae) |
| **Operadores del servicio de aseo** | Ninguna variable a nivel de agente | `03_recoleccion_por_concesionario.csv` (toneladas/mes por concesionario ASE) y `cantidad-entregada-por-ases.xlsx` — ya copiados a `data/raw/`, **nunca cargados por ningún loader** | Capacidad de camión, rutas, viajes/día (no existen en ninguna fuente) |
| **Gobernanza institucional / coordinación intersectorial** | — | — | No hay ninguna fuente de datos sobre coordinación entre entidades — es un concepto del marco teórico sin variable cuantitativa disponible |
| **Incentivos económicos / mercado de reciclables** | RN001-RN009 de `03_reglas_negocio.csv` (precios/tasas agregadas anuales, ciudad) | — | Precio de materiales reciclables por tipo, márgenes de intermediación |
| **Percepción ambiental** | — | `NHCLP9C/E/F` (percepción de mejora en recolección/reciclaje/educación ambiental), `NHCLP10`, `NHCLP11` (ingresos suficientes, se considera pobre) — todas nombradas en el `select()` original, no extraídas hoy | — |
| **Participación comunitaria** | — | `NPCJP1F` (pertenece a organización ambientalista), `NPCJP1I` (Junta de Acción Comunal) — nombradas en el `select()` original, no extraídas hoy | — |
| **Educación** | — | `NPCHP4` (nivel educativo más alto), `NPCHP1` (sabe leer y escribir) — nombradas en el `select()` original, no extraídas hoy | — |
| **Ingresos laborales / informalidad** | `indice_socioeconomico` (proxy simple = estrato/6) | `NPCKP23` (ingreso mensual laboral), `NPCKP44a` (dónde trabaja), `NPCKP17` (posición ocupacional), `OINFORMAL` (ocupado informal) — nombradas en el `select()` original, no extraídas hoy | Ingreso real de los recicladores de oficio |
| **Condiciones territoriales** | `densidad_poblacional`, `indice_fragmentacion_social`, `heterogeneidad_social`, geometría UPZ | — | — |
| **Pago del servicio de aseo** | — | `NHCDP5` (¿paga por recolección?), `NHCDP6` (cuánto pagó) — ya nombradas y parcialmente usadas para la recodificación de NA, pero **no exportadas como variable propia del modelo** | — |

---

## 4. Hallazgo de regresión de alcance (ya identificado, no corregido aquí)

El notebook original (antes del refactor de la Fase 1 de esta conversación) tenía un `select()` de PySpark que **sí nombraba** casi todas las columnas de la tabla anterior (`NPCJP1F`, `NPCJP1I`, `NPCKP23`, `NPCKP17`, `OINFORMAL`, `NHCLP9C/E/F`, `NHCLP10`, `NHCLP11`, `NPCHP4`, `NPCHP1`, `NHCCPCTRL2`, `NVCBP10`, `NVCBP4`, `NVCBP9`, `NHCCP35`, entre otras). Cuando se reemplazó PySpark por pandas (por la incompatibilidad de Java 8 con PySpark 4.x, documentada en la Fase 1), la nueva lista `COLUMNAS_MULTIPROPOSITO` en `src/carga_datos.py` **solo conservó las ~15 columnas relacionadas directamente con separación de residuos**, dejando fuera todas las demás categorías que el propio notebook original y el ACA1 ya habían identificado como relevantes.

**Esto no es un hueco de datos que nunca existió — es una reducción de alcance real ocurrida durante el refactor**, verificada contra el diccionario oficial de la encuesta (`20230620_diccionario_variables_encuesta_em2021.xlsx`, 1,594 filas, 13 capítulos A-M) y el header real de `em2021.csv` (1,552 columnas). Todas las columnas listadas en la tabla del inventario como "🟡 disponible, no extraído" están confirmadas presentes en ambas fuentes.

---

*Fin del análisis. No se ha decidido si se amplía `COLUMNAS_MULTIPROPOSITO`, si se ajusta el ABM a 4 o 5 actores, ni cómo reconciliar la hipótesis del notebook con las fuentes oficiales del proyecto de grado — esas decisiones y el siguiente paso quedan para que el usuario los defina.*
