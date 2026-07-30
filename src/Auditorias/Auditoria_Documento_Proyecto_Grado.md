# Auditoría sección por sección — Documento escrito del Proyecto de Grado
### Especialización en Analítica de Datos — CUN
**Documento auditado:** `Proyecto de Grado - Residuos Sólidos Bogotá (6).pdf` (81 páginas)
**Autores:** Manuel Alejandro González Gallego, Gloria Inés Robledo Ulloa
**Fecha de esta auditoría:** 2026-07-15 (o fecha posterior de sesión)

> **Qué es esto:** una revisión sección por sección del documento escrito, comparando cada
> parte contra el proyecto EDA+ABM real que efectivamente se construyó (ver
> `Auditoria_Final_Comite_Tesis.md` y `Resultados_EDA_Funcionamiento_Bogota.md` para el
> estado verificado del trabajo técnico). Convención de semáforo: 🟢 sólido y alineado, 🟡
> correcto pero necesita ajuste, 🔴 requiere corrección antes de entregar.

---

## 0. Veredicto general

Este documento es un **anteproyecto / propuesta metodológica**, no la tesis con resultados.
La tabla de contenido (págs. 3-4) termina en "9. Anexos" — no hay capítulo de Resultados,
Discusión ni Conclusiones. Todo lo que el proyecto EDA+ABM realmente encontró (odds ratios,
Engativá, el hallazgo del subsidio, la calibración del ABM, los bugs corregidos, el 43-48%) no
está escrito todavía. Ese es el trabajo más grande pendiente, no un defecto de lo que ya existe.

Dentro de lo que sí existe, el documento es metodológicamente sólido (7.1-7.6 describen con
precisión lo que de hecho se hizo) pero tiene tres problemas concretos que hay que resolver
antes de que esto llegue a un comité: (1) la cifra de aprovechamiento citada está desactualizada
frente a tu propio EDA, (2) la bibliografía tiene fuentes citadas que no existen en la lista de
referencias, y (3) hay párrafos duplicados por edición.

---

## 1. Introducción (págs. 11-14)

**Qué dice:** contexto global de residuos (Banco Mundial, Kaza et al.), aterriza en Bogotá
("~7.000 ton/día... aprovechamiento ~15-16%"), plantea la pregunta de por qué un sistema con
regulación e infraestructura sigue con bajo desempeño, justifica EDA+ABM como enfoque.

**Evaluación:** 🟡 Bien escrita y con buena progresión argumentativa (global → Bogotá →
pregunta → enfoque). El problema es la cifra: "15-16%" viene de citas secundarias (UAESP 2021;
Ministerio de Ambiente 2023), pero tu propio EDA ya estableció **18.56% para 2023** con una
serie completa 2018-2023, y descubrió que la cifra oficial más reciente (43-48%) es
metodológicamente incomparable. Esta introducción es el lugar natural para sembrar ese giro
("la cifra que usamos para justificar este problema resultó ser más matizada de lo que parecía"),
y hoy no lo hace.

**Citas:** Kaza et al. citado "2021" — la referencia real es de 2018 (ver §8 de esta auditoría).
Geels 2004, Cervantes & Palacios 2019 y Silva et al. 2022 no están en la bibliografía.

---

## 2. Planteamiento del problema (págs. 14-16)

### 2.1 Formulación o Pregunta de Investigación

**Qué dice:** repite el diagnóstico de la Introducción (~15%, UAESP 2021, Contraloría 2022),
argumenta que el problema es sistémico, no solo normativo/operativo. La pregunta de
investigación (2.1) es: *"¿Cómo las interacciones entre los actores y sus reglas de
comportamiento... generan las dinámicas emergentes que condicionan el aprovechamiento... y
bajo qué escenarios de intervención dichas dinámicas podrían modificarse...?"*

**Evaluación:** 🟡 La pregunta de investigación en sí (2.1) está **muy bien formulada** — es
fiel a lo que realmente se construyó (un ABM que sí explora escenarios de intervención vía los
multiplicadores de infraestructura/capacidad en el dashboard). No le cambiaría una palabra. El
problema es, otra vez, la cifra de 15% repetida como ancla del diagnóstico, y la cita a
"Contraloría de Bogotá, 2022" que en la bibliografía aparece fechada 2025.

---

## 3. Objetivos (pág. 17)

**Qué dice:** objetivo general (analizar dinámicas emergentes vía EDA+ABM) y 4 objetivos
específicos: (1) EDA de la información histórica, (2) caracterizar actores y sus reglas de
decisión, (3) construir el ABM, (4) analizar escenarios de simulación.

**Evaluación:** 🟢 **Esta es de las secciones mejor alineadas de todo el documento.** Los 4
objetivos específicos se cumplieron todos, y de forma verificable:
- Objetivo 1 (EDA histórico) → cumplido ampliamente, documentado en
  `Resultados_EDA_Funcionamiento_Bogota.md` (10 secciones de hallazgos reales).
- Objetivo 2 (caracterizar actores) → cumplido, cada actor tiene reglas de decisión
  documentadas y trazables a dato real (ver tabla de origen de parámetros en
  `Auditoria_Final_Comite_Tesis.md`).
- Objetivo 3 (construir el ABM) → cumplido, con calibración verificada (RMSE≈1.20pp).
- Objetivo 4 (escenarios de simulación) → cumplido, el dashboard expone escenarios reales
  (multiplicador de infraestructura y de capacidad formal).

No hay nada que corregir aquí. Cuando escribas la sección de Resultados, esta es la lista contra
la que debes trazar cada hallazgo, uno por uno, para que el comité vea la correspondencia
explícita.

---

## 4. Justificación (págs. 18-21)

**Qué dice:** justificación teórica (sistemas socio-técnicos, Geels/Holland), internacional
(ONU/OCDE), metodológica (EDA+ABM como enfoques complementarios), práctica, social/ambiental,
académica y formativa.

**Evaluación:** 🟡 Argumentación correcta y completa en su estructura (cubre las 6
dimensiones esperadas en una justificación de posgrado), aunque en un par de párrafos se
siente genérica — frases como *"proporciona un marco analítico que puede contribuir a reducir
la incertidumbre"* son válidas pero no dicen nada que no diría cualquier proyecto de este tipo.
Cuando reescribas esta sección, vale la pena anclar al menos un párrafo a algo específico y ya
comprobado de tu proyecto (por ejemplo: *"la integración EDA+ABM permitió, en este caso
concreto, detectar y corregir tres errores reales en los datos base — un factor per cápita
subestimado en 20%, una capacidad de recolección sobreestimada 12 veces, y 3 archivos de 2020
descartados en silencio — que habrían quedado invisibles en un análisis puramente descriptivo"*).
Eso es mucho más persuasivo que la justificación genérica actual.

**Citas:** Mitchell 2009 no está en la bibliografía; Creswell & Creswell 2018 y Hernández
Sampieri & Mendoza 2018 tampoco (aparecen más adelante, en §5).

---

## 5. Alcances y Limitaciones del Proyecto (págs. 20-24)

### 5.1 Alcance del proyecto

**Qué dice:** alcance analítico/exploratorio/explicativo, no prescriptivo; los 4 actores
(hogares, recicladores, operadores, gobierno); resultados como apoyo a la comprensión, no como
recomendaciones definitivas de política.

**Evaluación:** 🟢 Bien alineado y honesto sobre lo que el proyecto es y no es.

### 5.2 Limitaciones del proyecto

**Qué dice:** dependencia de datos secundarios con vacíos/inconsistencias; el ABM es una
simplificación, no reproduce el sistema real; los escenarios simulados **no son predicciones**,
son "escenarios plausibles derivados de los supuestos"; no hay validación mediante piloto o
experimento real; conclusiones delimitadas al contexto de Bogotá.

**Evaluación:** 🟢 **Esta es probablemente la sección mejor alineada de todo el documento con
la forma en que realmente hemos tratado los resultados del ABM en la práctica.** La frase
"escenarios plausibles, no predicciones determinísticas" es exactamente el lenguaje que hemos
usado consistentemente toda la sesión al hablar de los resultados de simulación. Nada que
cambiar aquí en cuanto a honestidad metodológica — es un ejemplo real de rigor, no un lugar
común de plantilla.

**Citas:** Grimm et al. 2006 / Grimm et al. 2010 no coinciden con la bibliografía (que solo
tiene Grimm & Railsback 2005).

---

## 6. Marco Referencial (págs. 24-53)

### Introducción a la sección (págs. 24-26)

🟡 Framing correcto, mismos problemas de citas ya señalados (Kaza et al. 2021/2018, OCDE
2024/2022).

### 6.1 Antecedentes

- **6.1.1 Internacionales** (pág. 26-27): Banco Mundial, ONU, OCDE, UE. 🟡 Correcto, pero
  aquí aparece por primera vez **Wilson et al., 2015**, citada más adelante más de 10 veces en
  todo el documento — y no está en la bibliografía en ningún lugar. Es la ausencia más notoria
  de todo el documento.
- **6.1.2 América Latina** (pág. 27): BID 2020 (coincide), Cervantes & Palacios 2019 (no
  está en bibliografía). 🟡
- **6.1.3 Nacional** (pág. 27-28): PGIRS, Política Nacional de Economía Circular, MinAmbiente
  2016/2019 (coinciden). Contraloría 2022 (bibliografía dice 2025), Superintendencia SSPD 2022
  (no está en bibliografía). 🟡
- **6.1.4 Locales: Bogotá** (pág. 28-29): repite "~15%". Buenas citas locales que sí
  coinciden con la bibliografía: Universidad de los Andes 2004, Secretaría de Cultura 2023,
  Universidad EAN 2024, Observatorio Ambiental 2022, UAESP 2021, Molano Camargo 2019. 🟡 (por
  la cifra, no por las citas locales, que están bien).
- **6.1.5 Metodológicos** (pág. 29-30) + **Tabla 1** (pág. 30-31): buena tabla-resumen que
  conecta cada antecedente con una variable analítica y su contribución al modelo — es un
  recurso genuinamente útil, vale la pena conservarlo así. 🟢 la tabla en sí; 🟡 Silva et al.
  2022 no está en bibliografía.
- Párrafo de cierre (pág. 31-32): identifica el vacío real — *"son escasas las
  investigaciones que integran ambas metodologías... particularmente en Bogotá"* — esto es
  honesto y es, de hecho, tu aporte real. 🟢

### 6.2 Marco teórico

- **6.2.1** (pág. 32-33) y **6.2.6** (pág. 36-39) **se solapan de forma notable**: ambas
  secciones vuelven a narrar, casi desde cero, la transición de "modelo lineal de disposición"
  a "gestión integral / economía circular", con ejemplos y citas parcialmente distintos. Esto
  se lee como si fueran dos borradores del mismo argumento que quedaron ambos en el documento
  final. 🟡 Vale la pena fusionar 6.2.1 y 6.2.6 en una sola narrativa, o diferenciar
  explícitamente qué aporta cada una (una podría quedarse con el marco global/regional y la
  otra profundizar específicamente en Bogotá).
- **6.2.2** (pág. 33) y **6.2.3** (pág. 34): brechas regionales/nacionales y el caso Bogotá.
  Buena mención a la inversión real de $980 millones de la Alcaldía en tecnificación de
  recicladores (2023) — esto es un dato real que además es consistente con el VIAT/subsidios
  que ya tenemos verificados en el EDA. 🟢
- **6.2.4 Variables clave emergentes** (pág. 34-35): 🔴 **Esta es la sección donde vive el
  problema de alcance que ya señalé.** La categoría (v) dice *"incentivos económicos y
  condiciones del mercado para materiales reciclables"* — pero tú mismo excluiste
  explícitamente "condiciones del mercado para materiales reciclables" del alcance de este
  proyecto (reservado para un análisis futuro aparte sobre dinámica entre actores) cuando
  definimos la Fase 2 de recolección de datos. El texto necesita decir solo *"incentivos
  económicos"*, con una nota de que el mercado de reciclables se excluyó deliberadamente.
- **6.2.5 Justificación metodológica EDA+ABM** (pág. 35): describe exactamente el ciclo que
  se implementó (EDA informa la calibración del ABM; el ABM produce escenarios que
  retroalimentan al EDA). 🟢 contenido; 🟡 Silva et al. 2022, Gómez et al. 2021 y Pineda et al.
  2020 no están en bibliografía.

### 6.3 Marco Conceptual (6.3.1-6.3.8, págs. 39-45)

**Qué dice:** define GIRSU, aprovechamiento como resultado sistémico, separación en la fuente
vs. calidad de la separación, los 4 actores, sistema socio-técnico, EDA, ABM, y cierra con la
**Tabla 2** (marco conceptual operativo).

**Evaluación:** 🟢 De las secciones más sólidas del documento. Es puramente definicional, con
baja densidad de citas (así que casi no tiene el problema de bibliografía), y es internamente
coherente con el resto del proyecto. La distinción entre "separar" y "separar adecuadamente"
(calidad de la separación) es exactamente la misma distinción que se usa en el EDA real
(`pct_calidad_separacion`). La Tabla 2 es clara y bien construida.

### 6.4 Marco Contextual (6.4.1-6.4.6, págs. 45-49)

**Qué dice:** Doña Juana (ubicación, historia desde 1988, expansión de 50 a 600+ hectáreas),
contexto histórico del modelo de relleno sanitario, entorno sociocultural, económico, político-
institucional y ambiental.

**Evaluación:** 🟡 Narrativa sólida y bien escrita, pero varios datos factuales fuertes
(1988, 50→600 hectáreas, "más de 50 millones de toneladas acumuladas", crecimiento poblacional
5M→7M) **no llevan una cita inline en la misma oración** — la cita más cercana queda varios
párrafos atrás. Para un dato tan específico como "600 hectáreas" o "50 millones de toneladas",
un comité va a preguntar la fuente exacta ahí mismo. La frase "paisaje tóxico" parafrasea
claramente el título de Molano Camargo (2019), que sí está en la bibliografía, pero merece una
cita explícita en esa oración puntual, no solo en el párrafo general. Repite "~15%" una vez más
en 6.4.4.

### 6.5 Marco Legal (6.5.1-6.5.4, págs. 49-53)

**Qué dice:** jerarquía completa — Constitución (Art. 365, 8, 49), leyes (142/1994, 152/1994,
80/1993, 1259/2008), decretos (1077/2015, 1076/2015, 596/2016, 4741/2005), resoluciones
(754/2014, 2184/2019), Acuerdo Distrital 761/2020.

**Evaluación:** 🟢 **La sección mejor construida del marco referencial.** Cada norma se conecta
con una implicación concreta para el proyecto (el Decreto 596/2016 y el rol formal del
reciclador, la Resolución 2184/2019 y el código de colores, etc.) — no es solo un listado, hay
análisis real. No tiene el problema de citas de las demás secciones porque cita normas
primarias directamente (no requieren entrada en la bibliografía académica). **Única
observación:** este es el lugar natural para mencionar el Decreto 1381/2024 (el cambio
metodológico que probablemente explica el salto de 18.56% a 43-48%) — hoy no aparece en
ninguna parte del documento, y aquí es donde más rigurosamente encajaría, como parte del marco
normativo vigente.

---

## 7. Metodología (págs. 53-77)

### 7.1 Enfoque de investigación, 7.2 Tipo, 7.3 Diseño (págs. 54-59)

**Evaluación:** 🟢 Los tres describen con precisión lo que efectivamente se hizo: enfoque
cuantitativo con componentes exploratorio/explicativo, tipos exploratoria+descriptiva+
explicativa, diseño no experimental/transversal apoyado en simulación. No hay nada que
corregir en contenido.

### 7.4 Población y muestra (7.4.1-7.4.5, págs. 59-62)

**Qué dice:** población = el sistema GIRSU de Bogotá (no individuos aislados); unidades de
análisis (actores/agentes) vs. unidades de observación (registros); muestra censal-analítica
(no probabilística); para el ABM, "población sintética" con agentes calibrados a partir de
parámetros empíricos, no individuos reales.

**Evaluación:** 🟡 El contenido es correcto y, de hecho, describe con exactitud cómo se
construyó la población real de agentes del ABM (cohortes UPZ×estrato muestreadas y
ponderadas, no hogares reales geolocalizados — esto es justo lo que se documentó también en
`Auditoria_Final_Comite_Tesis.md`). **El problema es de edición, no de contenido:** el párrafo
que empieza "Desde una perspectiva operativa, la población no se limita a individuos
aislados..." aparece **tres veces seguidas** (antes de la lista de actores, después de la
lista, y de nuevo al abrir 7.4.2). Y el párrafo de cierre de 7.3 se repite como apertura de
7.4. Hay que borrar los duplicados — es edición mecánica, no reescritura.

### 7.5 Técnicas e instrumentos de recolección (7.5.1-7.5.3, págs. 62-66)

**Evaluación:** 🟢 Describe correctamente el proceso real: revisión documental de fuentes
oficiales → extracción/depuración → traducción a parámetros del ABM. Apropiadamente no
menciona herramientas específicas de código (Python/pandas) en el cuerpo del texto, lo cual es
correcto para una narrativa ejecutiva/académica — esas quedan en el Anexo A (enlaces a Colab).

### 7.6 Plan de análisis de la información (7.6.1-7.6.6, págs. 66-70)

**Evaluación:** 🟡 Igual que 7.4: contenido correcto (organización → EDA → variables clave →
parametrización → simulación de escenarios → interpretación integrada, que es exactamente el
flujo real seguido), pero el párrafo de apertura de 7.6.1 se repite dos veces seguidas. Fácil
de arreglar.

### 7.7 Cronograma (7.7.1-7.7.6, págs. 70-75) + Tabla 3

**Qué dice:** plan lineal de 16 semanas — revisión documental (sem 1-2), datos (sem 3-4), EDA
(sem 5-6), diseño ABM (sem 7-8), simulación (sem 9-10), cierre (sem 11-16).

**Evaluación:** 🟡 Es un cronograma razonable *como plan original*, pero no refleja ni de
lejos la cantidad real de iteraciones que tuvo el proyecto (múltiples rondas de recalibración,
rediseños completos del dashboard, auditorías de datos que encontraron y corrigieron errores
reales, la construcción de la presentación ejecutiva ACA como entregable paralelo). No es un
error — es normal que un anteproyecto no anticipe esto — pero cuando actualices el documento,
decide conscientemente si quieres mostrar el cronograma *planeado* (tal cual está, como
evidencia de que hubo un plan) seguido de una nota honesta de cómo evolucionó en la práctica, o
si prefieres reescribirlo para reflejar lo que realmente pasó.

### 7.8 Presupuesto (págs. 75-77) + Tabla 4

**Evaluación:** 🟡 Contenido razonable (ejercicio académico estándar de costeo por hora,
recurso humano ~87% del total, valor referencial de software open source). **Único problema
real:** la Tabla 4 (el presupuesto) tiene literalmente el mismo título que la Tabla 1
("Relación entre antecedentes, variables analíticas y enfoque de modelación") — un error de
copiar/pegar el título. Debería decir algo como "Tabla 4. Presupuesto estimado del proyecto".

---

## 8. Referencias bibliográficas (págs. 78-80)

🔴 **Esta es la sección que más trabajo necesita antes de cualquier entrega formal.**

**Problema 1 — organización:** la lista está agrupada por tema ("Colombia", "Bogotá D.C.",
"Doña Juana", "Comportamiento ciudadano", "Analítica de Datos", "Sistemas Complejos y ABM",
"Economía Circular y residuos") en vez de alfabética única, que es lo que exige APA 7.

**Problema 2 — fuentes citadas en el texto que no existen en la lista de referencias**
(verificado cruzando cada cita del documento contra las 8 páginas de bibliografía):

| Fuente citada en el texto | Dónde aparece |
|---|---|
| Wilson et al., 2015 | Citada 10+ veces — es una de las fuentes más usadas de todo el documento |
| Silva et al., 2022 | §1, §6.1.5, §6.2.4, §6.2.5 |
| Gómez et al., 2021 | §6.2.4, §6.2.5 |
| Pineda et al., 2020 | §6.2.5 |
| Geels, 2004 | §1, §4, §6 (intro) |
| Mitchell, 2009 | §4 |
| Creswell & Creswell, 2018 | §5.1 |
| Hernández Sampieri & Mendoza, 2018 | §5.1 |
| Geissdoerfer et al., 2017 | §6.2.1, §6.2.6 |
| Kirchherr et al., 2018 | §6.2.1, §6.2.6 |
| Zhang et al., 2019 | §6.2.6 |
| Macal & North, 2010 | §1, §7.7, §7.7.4 |
| Ministerio de Vivienda, Ciudad y Territorio, 2014 | §6.2.6, §7.6, §7.7 |
| DNP, 2016 | §6.2.6, §7.6, §7.7 |
| Superintendencia de Servicios Públicos Domiciliarios, 2022 | §6.1.3 |
| Comisión Europea, 2020 | §6.1.1 |
| UN-Habitat, 2010 | §6.2.6 |

**Problema 3 — el año citado en el texto no coincide con el año en la referencia:**

| Cita en el texto | Referencia real en la bibliografía |
|---|---|
| Kaza et al., **2021** (10+ veces) | Kaza, S. et al. (**2018**). *What a Waste 2.0* |
| Railsback & Grimm, **2019** (5 veces) | Grimm, V., & Railsback, S. F. (**2005**). *Individual-Based Modeling and Ecology* |
| Contraloría de Bogotá, **2022** (4 veces) | Contraloría de Bogotá D. C. (**2025**) |
| OCDE, **2024** | OECD. (**2022**). *Global Plastics Outlook* |

**Por qué importa:** tu propia "Declaración de originalidad y autonomía" (pág. 9) afirma que
*"hemos indicado clara y precisamente todas las fuentes directas e indirectas de información"*.
Esto no es un problema de fondo (el contenido citado parece genuino, no inventado), pero un
comité de posgrado revisa esto con lupa, y hoy la bibliografía no sostiene esa declaración tal
como está. Vale la pena cerrarlo antes de que alguien más lo encuentre.

---

## 9. Anexos (pág. 81)

**Qué dice:** enlaces a Google Colab y Google Drive con el código y recursos del proyecto.

**Evaluación:** 🟡 No puedo verificar el contenido de esos enlaces desde aquí. Dado que todo
el trabajo real de esta sesión (y de las anteriores) vive en el repositorio local del proyecto
(`EDA + ABM Residuos Bogota/`), vale la pena confirmar que esos enlaces de Colab/Drive están
sincronizados con la versión final del código local antes de que alguien del comité los abra y
encuentre una versión vieja o incompleta.

---

## 10. Resumen ejecutivo de lo pendiente

**Ya está bien y no hay que tocarlo:** Objetivos (§3), Alcance y Limitaciones (§5), Marco
Conceptual (§6.3), Marco Legal (§6.5), Enfoque/Tipo/Diseño de investigación (§7.1-7.3).

**Necesita ajuste de contenido (no reescritura completa):**
1. Reemplazar "~15%" por 18.56% (2023) en Introducción, Planteamiento, Justificación y Marco
   Contextual — y considerar agregar el hallazgo del salto a 43-48% como parte del
   planteamiento del problema, no solo como un dato que vive en el EDA.
2. Corregir §6.2.4: quitar "condiciones del mercado para materiales reciclables" de la
   categoría de incentivos económicos.
3. Fusionar o diferenciar claramente 6.2.1 y 6.2.6 (narrativa duplicada).

**Necesita limpieza mecánica (rápido):**
4. Borrar los párrafos duplicados en §7.4, §7.6.1 y el cierre de §6.4/apertura de §6.5.
5. Corregir el título de la Tabla 4 (§7.8).
6. Confirmar la fecha real de entrega (portada dice "Febrero de 2026", firmas dicen "3 de
   enero de 2026").

**Necesita trabajo bibliográfico real:**
7. Agregar las ~17 fuentes citadas pero ausentes de la bibliografía, o quitar las citas si no
   se puede recuperar la fuente original.
8. Corregir los 4 años que no coinciden entre cita y referencia.
9. Alfabetizar la lista completa (quitar la agrupación temática).

**El trabajo más grande, y el que realmente falta:**
10. Escribir los capítulos de Resultados, Discusión y Conclusiones — hoy no existen. Ahí es
    donde va todo lo que el proyecto EDA+ABM realmente encontró.
