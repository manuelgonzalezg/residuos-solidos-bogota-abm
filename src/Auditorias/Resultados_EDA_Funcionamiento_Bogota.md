# Qué nos dijeron los datos: cómo funciona realmente el sistema de residuos de Bogotá
### Síntesis completa de resultados del EDA, organizada por tema (no por notebook)
**Autores:** Manuel Alejandro González Gallego, Gloria Inés Robledo Ulloa — CUN
**Fecha:** 2026-07-11

---

## 0. Qué es este documento y cómo se construyó

Este documento junta **todos los resultados descriptivos** que arrojaron las fuentes de datos del
proyecto — la auditoría completa (`Auditoria_Completa_Datos_Limpieza_EDA.md`), la investigación
del salto de aprovechamiento (`Investigacion_Salto_Aprovechamiento.md`) y la calibración del ABM
(`Reglas_Negocio_v2_y_Modelado_Agentes.md` §7) — pero **reordenados por tema**, no por el orden en
que aparecen en el notebook. La pregunta que organiza todo es: *si tuviera que explicarle a
alguien, en una conversación, cómo funciona de verdad el sistema de manejo de residuos de
Bogotá, ¿qué le diría, con qué evidencia, y con qué nivel de confianza?*

Cada hallazgo trae: **qué fuente lo produjo**, **qué dijo exactamente** (con el número real, no
una paráfrasis vaga), **qué significa en términos de negocio**, y **qué tan confiable es** (la
misma escala de la auditoría: 🟢 evidencia sólida, 🟡 evidencia con matices/limitaciones, 🔴
supuesto sin confirmar todavía). No se repite aquí el detalle metodológico de cada prueba
estadística (chi-cuadrado, regresión, etc.) — eso está en la auditoría completa, con glosario
incluido; aquí el foco es **qué dicen los datos sobre Bogotá**, no cómo se calculó.

---

## 1. El tamaño del problema: cuánta basura genera Bogotá y qué le pasa

**Fuente:** `Residuos generados bogota.xlsx` (serie oficial 2018-2025) + `caracterizacion_residuos`
(composición mensual 2015-2026) + reconciliación externa (UAESP/OAB vs. Superservicios/SUI).

🟢 Bogotá generó, en 2023 (el último año con cifra confiable, ver sección 9), **2,667,955
toneladas de residuos** en el año — alrededor de 7,300 toneladas cada día. De eso, solo
**495,238 toneladas (18.56%)** se aprovecharon; el resto, más de 2.1 millones de toneladas,
terminó en el Relleno Sanitario Doña Juana.

🟢 La composición física de esa basura (promedio de 133 meses de datos, 2015-2026) muestra que la
**materia orgánica es, con diferencia, el componente más grande** de lo que se bota — más que
plástico, papel, vidrio y metales juntos. Esto importa porque la materia orgánica es exactamente
el tipo de residuo que más fácil se pierde si no hay separación en la fuente (no se puede
"rescatar" de la mezcla después, como sí se puede hacer parcialmente con plástico o vidrio en una
planta de clasificación).

🟢 La serie 2018-2023 muestra una tendencia **real pero lenta y gradual**: 15.38% → 15.70% →
17.28% → 19.18% → 18.27% → 18.56%. No es una línea perfectamente recta (2021 tiene un pico que
2022 corrige), pero la dirección general es de mejora lenta, no de estancamiento total ni de
un salto repentino.

🔴 **2024 y 2025 son un caso aparte** — la cifra oficial salta a 43.88% y 48.50% respectivamente.
La sección 9 de este documento explica por qué esas dos cifras no deben tratarse como continuación
de la misma serie.

---

## 2. ¿Quién es Bogotá? La base demográfica y territorial

**Fuente:** proyecciones DANE de población por UPZ (2018-2024), estratificación oficial por
manzana catastral (44,260 manzanas), proyección de hogares por UPZ (2018-2035).

🟢 Bogotá se organiza, para efectos de este proyecto, en **112 UPZ** (Unidades de Planeamiento
Zonal, como "barrios grandes" oficiales) agrupadas en **20 localidades**. El estrato
socioeconómico (0 a 6) se asigna oficialmente a nivel de **manzana** — la unidad más pequeña y
precisa disponible, más fina que la UPZ.

🟢 **El estrato es, de lejos, la variable individual con más poder explicativo de todo el
proyecto** — aparece relacionado con la separación de residuos, la presencia de recicladores, y
el incentivo económico. No es una sola prueba la que lo confirma: aparece en el chi-cuadrado de
la ECA2021, en la regresión logística de la EM2021, y en el mapa de incentivo económico. Tres
métodos distintos, mismo patrón — eso es lo que le da solidez al hallazgo.

🟡 La estructura de edad (pirámide poblacional por UPZ) está disponible pero **no está conectada
a nivel individual con quién separa o no separa** — se sabe cuántas personas de cada edad viven en
cada UPZ, pero no se puede cruzar directamente "esta persona de tal edad, en tal UPZ, separa o
no". El vínculo edad-separación que sí existe (sección 3) viene de la encuesta individual (ECA
2021), no de esta fuente demográfica agregada.

---

## 3. ¿Quién separa basura en el hogar, y por qué (o por qué no)?

Esta es la pregunta central del proyecto — la que más evidencia estadística formal tiene detrás,
combinando dos encuestas independientes (ECA2021 y EM2021) que llegan a conclusiones
consistentes entre sí.

### 3.1 Lo que la gente dice que la motiva y la detiene (evidencia cualitativa real, no supuesta)

**Fuente:** ECA2021, microdato individual (2,282 encuestas), preguntas abiertas de motivación y
dificultad.

🟢 La razón principal para separar es, de lejos, **"porque es bueno para el ambiente"** — muy por
encima de razones económicas ("para vender el material") o sociales ("para ayudar a los
recicladores"). La motivación de quien sí separa es mayormente de conciencia ambiental, no
económica.

🟢 La dificultad principal para separar es **"que todas las personas del hogar separen"** y
**"no hay espacio suficiente para varias canecas"** — es decir, el obstáculo típico no es "no
querer", es un problema práctico de **coordinación dentro del hogar** y de **espacio físico en la
vivienda**.

**Qué significa para el negocio:** esto es evidencia real (no un supuesto de diseño) de que la
separación de residuos se comporta como un fenómeno **social y de coordinación**, no como una
decisión puramente individual o económica — apoya directamente la idea de modelarla con un
mecanismo de imitación/contagio social entre vecinos, más que con un cálculo de costo-beneficio
individual.

### 3.2 Qué variables realmente predicen la separación (la pieza más sólida del EDA)

**Fuente:** regresión logística multivariada sobre 234,043 hogares de la Encuesta Multipropósito
2021, con 13 variables simultáneas y usando el factor de expansión oficial (`FEX_C`) — es decir,
las cifras que siguen representan a la población real de Bogotá, no solo a la muestra encuestada.

Una regresión multivariada estima el efecto de cada variable **aislado de las demás** — por
ejemplo, separa el efecto propio del estrato del efecto de la educación, aunque ambas suban
juntas en la realidad. El resultado (odds ratio) dice cuánto se multiplican las probabilidades de
separar por cada variable, manteniendo todo lo demás constante:

| Variable | Odds ratio | Lectura de negocio |
|---|---|---|
| 🟢 Participación en Junta de Acción Comunal (JAC) | **2.63** | Más que duplica la probabilidad de separar — el predictor más fuerte de todo el proyecto |
| 🟢 Participación en organización ambiental | **2.33** | También más que duplica la probabilidad — segundo predictor más fuerte |
| 🟢 Vivienda propia (vs. arrendada) | 1.40 | Ser dueño aumenta 40% la probabilidad |
| 🟢 Estrato | 1.37 | Cada estrato adicional, +37% |
| 🟢 Personas por hogar | 1.13 | Hogares más grandes separan un poco más |
| 🟢 Nivel educativo | 1.13 | Cada nivel educativo adicional, +13% |
| 🟢 Informalidad laboral | **0.85** | Tener empleo informal REDUCE 15% la probabilidad |
| 🟡 Ingreso mensual laboral | 1.00 | **Sin efecto real** una vez controlado por estrato/educación/formalidad — no es "tener más plata", es la combinación de condición estructural + integración social |

**El hallazgo más importante de todo el EDA**: la participación comunitaria (JAC o ambiental)
pesa **más que el estrato o la educación**. Estar conectado con la comunidad predice mejor quién
separa que la condición socioeconómica misma. Y el ingreso, que uno intuitivamente esperaría que
importara mucho, **no aporta nada extra** una vez ya se sabe el estrato, la educación y la
formalidad laboral — este resultado se confirmó dos veces (con 8 variables primero, con 13
después), así que no es un accidente del primer modelo.

### 3.3 Otros hallazgos de la misma regresión, agregados en la ronda de auditoría

🟢 **Vivir en conjunto residencial aumenta la probabilidad de separar** — posible efecto de reglas
u organización propias de los conjuntos (administración, portería, contenedores compartidos).

🟢 **Vivir cerca de un basurero/botadero reduce la probabilidad de separar** — primera evidencia
real a favor de la idea de que un entorno físico degradado desmotiva el esfuerzo individual
("¿para qué separo si igual el barrio está lleno de basura?").

🟡 **Matiz importante, no una confirmación limpia**: vivir en un entorno con "disposición
inadecuada de basuras" en general (una pregunta distinta a "cerca de un basurero específico") se
asoció con **MÁS** separación, no menos — el resultado contrario al anterior. El EDA no fuerza una
sola narrativa cuando dos variables del mismo mecanismo apuntan en direcciones distintas; queda
documentado como un hallazgo con matiz, para investigar más, no para esconder.

🟡 **Sentirse pobre** (percepción subjetiva, más allá del estrato oficial) también reduce un poco
la probabilidad de separar — la percepción propia aporta información que el estrato objetivo por
sí solo no captura.

### 3.4 La edad, sí importa (hallazgo agregado en la auditoría final)

**Fuente:** ECA2021, variable de edad individual que existía en la encuesta pero nunca se había
cruzado contra separación.

🟢 Por cada año adicional de edad, las probabilidades de separar suben **4%** (odds ratio 1.04,
altamente significativo). Acumulado, la diferencia entre una persona de 20 años y una de 60 años
sería, aproximadamente, **4.8 veces más probable de separar**, si todo lo demás fuera igual. Las
personas mayores parecen tener más disposición a separar que las más jóvenes.

### 3.5 ¿El estrato influye? (confirmado por partida doble)

🟢 Con la Encuesta de Cultura Ambiental (chi-cuadrado, ponderado): la relación entre estrato y
separación es estadísticamente significativa (p=0.0156) — es decir, la relación que se ve en los
datos es demasiado fuerte para ser puro azar de la muestra.

🟢 Con la Encuesta Multipropósito (regresión, sección 3.2): estrato con odds ratio 1.37,
consistente con el chi-cuadrado. Dos encuestas distintas, dos métodos distintos, mismo resultado.

### 3.6 Un caso extremo que casi nadie usa: no tener servicio de recolección

🟡 Solo **1.41% de los hogares de Bogotá** no usa el servicio formal de recolección — un grupo
muy pequeño. De ese grupo, **enterrar la basura es la forma más común de deshacerse de ella,
seguida de quemarla**. Es un problema real pero de escala muy acotada, no representativo del
comportamiento general de la ciudad.

### 3.7 El mapa: la separación varía por zona, no es uniforme

🟢 Un mapa coroplético del % de separación por las 112 UPZ muestra variación real y visible, sin
un patrón perfectamente uniforme — confirma que la separación **no es igual en toda la ciudad**,
justo el tipo de desigualdad territorial que la pregunta de investigación del proyecto busca
explicar.

---

## 4. ¿Cómo se recolecta la basura? La logística operativa real

**Fuentes:** RBL consolidado (97 archivos, 2017-2026, toneladas mensuales por operador), SIGAB
(puntos críticos, 4 cortes en el tiempo 2020-2026), Macrorutas de recolección y barrido (datos
reales de zonas operativas).

### 4.1 La recolección formal no parece ser el cuello de botella

🟢 Los 5 operadores de aseo (ASE: Promoambiental, LIME, Ciudad Limpia, Bogotá Limpia, Área Limpia)
mantienen un volumen de recolección relativamente estable a lo largo de 8 años, sin caídas
abruptas. Al calibrar el ABM con la capacidad real (después de corregir un error de cálculo que
la había sobreestimado ~12 veces, ver sección 9), la capacidad conjunta real es de
**~3,339 a ~4,900 toneladas/día** — comparable a la generación diaria real de la ciudad
(~7,300-10,900 ton/día), pero en la práctica **rara vez se satura** en los datos históricos.

**Qué significa para el negocio:** el problema del bajo aprovechamiento **no parece estar en la
capacidad de recoger** — está en otro punto de la cadena, probablemente en la separación en la
fuente (lo que la gente separa o no separa antes de que el camión pase), no en que el sistema
formal no dé abasto.

### 4.2 Los puntos críticos de acumulación de basura son un problema territorial persistente

🟢 Comparando 4 cortes en el tiempo (2020, 2022, 2024, 2026), el **mismo grupo de UPZ** (una zona
del centro-norte de la ciudad) aparece consistentemente como el de más puntos críticos en los 4
momentos. El coeficiente de variación entre zonas es alto (1.19) — hay mucha diferencia entre
UPZ, y esa diferencia **no cambia mes a mes ni año a año**: es un patrón estructural, no un evento
pasajero.

🟡 Al cruzar estrato y puntos críticos en un mismo mapa (mapa bivariado), aparecen zonas de
**estrato alto que también tienen puntos críticos altos** — la relación no es tan simple como
"estrato bajo = más problemas de infraestructura". El supuesto original más simple (solo estrato y
densidad explican la infraestructura) no se sostiene completamente frente al dato real.

### 4.3 La frecuencia de recolección varía geográficamente (dato real, antes no existía)

🟢 Las macrorutas reales de recolección (125 zonas) y de barrido (179 zonas) muestran que la
frecuencia semanal con la que pasa el camión **varía según la zona** — no es uniforme en toda la
ciudad. Es la primera vez que el proyecto tiene la estructura operativa real, más allá de solo
saber cuántas toneladas se recogen en total.

---

## 5. ¿Quiénes son los recicladores de oficio, y cómo operan?

**Fuentes:** RURO (Registro Único de Recicladores de Oficio, 24,196 personas), RURO oficial
2012-2021 y 2022 por localidad (afiliación a salud, tipo de vivienda, afiliación ARL).

### 5.1 El registro está razonablemente actualizado

🟢 De los recicladores que se han registrado históricamente (2012-2021), **89.9% siguen activos**
en el sistema; el 10.1% se retiró por razones documentadas (cédula no encontrada, fallecimiento,
etc.).

### 5.2 La población recicladora es mayoritariamente informal y precaria — confirmado con dato oficial, no supuesto

🟢 En afiliación a salud: **~20,401 recicladores están en régimen Subsidiado** (el que reciben las
personas sin capacidad de pago) contra solo **~1,412 en régimen Contributivo** (el de un empleo
formal). En tipo de vivienda, "Arrendada" domina claramente, con categorías de alta precariedad
(Calle, Cambuche, Invasión) también presentes.

### 5.3 El hallazgo más importante de esta fuente: "registrado" no significa "formalizado laboralmente"

🟢 **14 de 18 localidades con datos tienen 0% de afiliación a ARL** (el seguro de riesgos
laborales, el indicador más directo de un trabajo formal real) entre sus recicladores; el máximo
observado en cualquier localidad es 14.3%.

**Por qué esto es un matiz importante:** el 89.9% de "activos en el RURO" (sección 5.1) podría
hacer pensar que la mayoría de recicladores está en una situación relativamente estable — pero
"estar registrado" y "tener protección laboral real" son dos cosas completamente distintas. Casi
nadie tiene la segunda, aunque casi todos tienen la primera. El modelo de agentes necesita
representar estos dos hechos por separado, no como un solo número de "formalización".

### 5.4 Un hallazgo que va contra la intuición: más recicladores no significa más separación

🟢 Comparando el número de recicladores por localidad contra el % de separación de esa misma
localidad: correlación muy débil y **estadísticamente no significativa** (r=-0.14, p=0.548).

**Qué significa:** contrario a lo que se podría suponer, **no hay evidencia de que más
recicladores en una zona se traduzca en más separación** en esa misma zona — a nivel de
localidad, ambos fenómenos parecen ser prácticamente independientes entre sí. Es un hallazgo
honesto: evita que el modelo asuma una relación causal directa entre presencia de recicladores y
comportamiento de separación de los hogares, que los datos disponibles no respaldan.

🟢 Sí se confirma, en cambio, que **los recicladores se concentran más en zonas de estrato más
bajo** (correlación negativa, r≈-0.23, entre estrato de la UPZ y número de recicladores) —
coherente con lo que se sabe del oficio del reciclaje en Colombia.

---

## 6. ¿Cómo funciona la gobernanza institucional?

**Fuente:** SIGAB — PQRS (peticiones, quejas, reclamos, sugerencias) de aseo por localidad, 2020 y
diciembre 2022 (único proxy cuantitativo disponible de gobernanza en todo el proyecto).

🟢 Comparando 2020 contra diciembre de 2022, **todas las localidades muestran una caída** en el
número de quejas de aseo.

🟡 **Advertencia de interpretación honesta**: 2020-2021 fue el período de aislamiento por
COVID-19, que pudo afectar tanto la generación de residuos como la forma de reportar quejas — esta
caída podría reflejar, al menos en parte, un efecto pandémico temporal, no necesariamente una
mejora real y sostenida del servicio de aseo. Se documenta el hallazgo, pero con esta reserva
explícita, no como una conclusión limpia de "el servicio mejoró".

---

## 7. ¿Quién paga y quién recibe? El mapa económico real

**Fuente:** tarifas CRA / Ciudad Limpia (diciembre 2025) — primer dato económico real que entró al
proyecto (antes de esto, el modelo no tenía ningún mecanismo económico basado en dato real).

🟢 El **VIAT** (Valor del Incentivo al Aprovechamiento y Tratamiento) es de **$11,388 por
tonelada** — el pago real que reciben quienes aprovechan material.

🟢 El sistema de tarifas redistribuye recursos de forma significativa por estrato: estratos 1 y 2
reciben un subsidio de hasta **-70% y -40%** respectivamente sobre la tarifa; estratos 5 y 6
**contribuyen +50% y +60%** de más.

🟢 Al combinar esta tarifa con la composición real de estratos de cada UPZ, el mapa resultante
muestra que las **zonas del norte y noreste** (estratos altos) contribuyen más de lo que reciben,
y las del **sur** (estratos bajos) reciben más subsidio del que pagan — un patrón geográficamente
coherente con lo que ya se sabe de la estructura socioeconómica de Bogotá. Que el cálculo
reproduzca un patrón geográfico ya conocido es, en sí mismo, una señal de que el número tiene
sentido, no es ruido.

---

## 8. Cómo interactúan los actores entre sí (más allá de cada uno por separado)

**Fuente:** matriz de correlación entre estrato, densidad poblacional, separación, calidad de
separación, número de recicladores, y fragmentación social — todas a nivel UPZ.

🟢 Estrato y separación: correlación positiva moderada (r≈0.28).

🟢 Estrato y número de recicladores: correlación negativa (r≈-0.23) — confirma, con otro método,
el hallazgo de la sección 5.4.

🟢 (Repetido de la sección 5.4 porque es demasiado importante para no repetirlo): recicladores y
separación, prácticamente sin relación (r=-0.14, no significativo).

**Qué significa en conjunto:** el estrato es el "eje" alrededor del cual se organizan varias de
estas relaciones — más que la presencia de recicladores, que parece operar de forma bastante
independiente del comportamiento de separación de los hogares.

---

## 9. El hallazgo más importante para la credibilidad del proyecto: la "mentira" del 43-48%

Esta sección resume, para quien lea solo este documento, la investigación completa que ya está en
`Investigacion_Salto_Aprovechamiento.md` (y su extensión con el ABM en
`Reglas_Negocio_v2_y_Modelado_Agentes.md` §7) — porque es un resultado que cambia cómo se debe
leer TODO lo demás de este documento si se usa el año equivocado como referencia.

### 9.1 El problema que se detectó

🔴 La serie oficial de aprovechamiento salta de **18.56% (2023)** a **43.88% (2024)** — un salto
de 25.3 puntos porcentuales en un año, y el total de residuos generados también salta **48.7%** en
el mismo período (2,667,955 → 3,967,682 toneladas). Una ciudad no genera de repente 1.3 millones
de toneladas adicionales de basura de un año a otro sin que cambie algo en cómo se está contando.

### 9.2 La evidencia documental de que es un cambio de medición, no de comportamiento

🟢 El % de aprovechamiento oficial de Bogotá **no es una medición directa** — es la salida de un
"Modelo Macro Econométrico" de la UAESP (confirmado en fuentes oficiales del Observatorio
Ambiental de Bogotá), que combina supuestos de crecimiento poblacional, verificación de flujo de
materiales, y tasas del PGIRS. Cualquier recalibración de ese modelo puede mover el resultado sin
que nada haya cambiado en el comportamiento real de los hogares.

🟢 Dos fuentes oficiales del Distrito (UAESP/OAB y Superservicios/SUI) reportan cifras que
**difieren en un factor de ~2x** para el mismo concepto, el mismo año — evidencia de que ni las
propias entidades distritales coinciden entre sí sobre "el % real de aprovechamiento de Bogotá".

🟢 2024 fue, de forma confirmada y documentada, un año de **reforma regulatoria profunda**: el
Decreto 1381 de 2024 obliga a los municipios a actualizar y publicar cada año el censo de
recicladores conforme al PGIRS (cambia mecánicamente cuánto material "cuenta" como aprovechamiento
formal), y entró en vigencia el nuevo PGIRS 2024-2028 — cambios administrativos reales, no una
transformación repentina del comportamiento de 2.7 millones de hogares bogotanos.

### 9.3 La evidencia cuantitativa independiente: qué dice un modelo construido desde cero

Más allá de la evidencia documental, se calibró el ABM de este proyecto **únicamente contra los 6
puntos reales 2018-2023** (sin usar ningún dato de 2024/2025) y se le pidió que proyectara 2024
por su cuenta, sin ningún mecanismo que representara la reforma regulatoria:

| Año | Real oficial | Simulado por el ABM (calibrado 2018-2023) |
|---|---|---|
| 2018 | 15.38% | 17.35% |
| 2019 | 15.70% | 17.46% |
| 2020 | 17.28% | 17.54% |
| 2021 | 19.18% | 17.61% |
| 2022 | 18.27% | 18.11% |
| 2023 | 18.56% | 18.16% |
| **2024** | **43.88%** (oficial) | **18.29%** (contrafactual) |

🟢 El modelo, con mecanismos 100% basados en dato real (población real, infraestructura real por
año, capacidad de recolección real por año, comportamiento calibrado contra la serie real),
proyecta que 2024 habría cerrado alrededor de **18.3%** si el sistema hubiera seguido su dinámica
orgánica — una brecha de **~25.6 puntos porcentuales** frente a la cifra oficial, que ninguno de
los mecanismos reales del modelo logra generar.

**Qué significa en conjunto:** son **tres líneas de evidencia independientes** (documental,
comparación entre fuentes oficiales, y modelo mecanicista propio) apuntando en la misma
dirección. Ninguna por sí sola es una prueba estadística cerrada, pero la convergencia de las tres
es un argumento defendible: **el aprovechamiento real de Bogotá en 2023-2024 está mucho más cerca
de 18-19% que de 43-48%** — la cifra alta es, con evidencia razonable, un artefacto de la reforma
metodológica de 2024, no una mejora real del comportamiento ciudadano.

### 9.4 Dos bugs de datos reales que se encontraron y corrigieron en el camino de esta investigación

🟢 3 archivos de la carpeta RBL de 2020 se estaban descartando en silencio por un fallo del
"detector" de formato de archivo — la cobertura real de 2020 pasó de 155,088 a 616,761
toneladas/año al corregirlo.

🟢 La capacidad formal de recolección estaba sobreestimada **~12 veces** (38,913 ton/día en vez de
~3,339-4,900 reales) por un error de unidades (dividir un total anual entre 30 en vez de entre
365) — con el valor incorrecto, la capacidad formal nunca podía saturarse, aunque el número en sí
no tuviera sentido frente al tamaño real de la ciudad.

---

## 10. Síntesis final: qué sabemos con certeza vs. qué sigue siendo un supuesto

### Con evidencia real y sólida (🟢, confirmado por más de un método cuando fue posible):

- El estrato influye en la separación (dos encuestas, dos métodos distintos, mismo resultado).
- La participación comunitaria (JAC u organización ambiental) es el predictor más fuerte de
  separación de todos los medidos — más que el estrato o la educación.
- La informalidad laboral reduce la separación.
- El ingreso, por sí solo, no tiene efecto adicional una vez se controla por estrato/educación/
  formalidad — confirmado dos veces, con dos especificaciones distintas del modelo.
- La edad tiene un efecto positivo real (+4% de probabilidad por año adicional).
- Vivir en conjunto residencial aumenta la probabilidad de separar; vivir cerca de un
  basurero/botadero la reduce.
- La recolección formal tiene capacidad real (~3,300-4,900 ton/día) que rara vez se satura — el
  cuello de botella del sistema no parece estar ahí.
- Los puntos críticos de acumulación son un patrón territorial persistente, no aleatorio.
- Los recicladores están registrados oficialmente en su mayoría (90%), pero casi ninguno tiene
  protección laboral real (0-14% con ARL) — dos cosas distintas, no una.
- Más recicladores en una zona NO se traduce en más separación en esa zona — sin relación
  estadística significativa.
- El % de aprovechamiento oficial 2024-2025 (43.88%/48.50%) no es comparable con la serie
  2018-2023 — tres líneas de evidencia independientes lo respaldan.

### Con matices, no conclusión limpia (🟡):

- Vivir en un entorno de "disposición inadecuada de basuras" en general se asoció con MÁS
  separación (contrario al efecto de "cerca de un basurero específico").
- La caída de PQRS de gobernanza 2020→2022 puede estar mezclada con el efecto de la pandemia.
- La capacidad formal, aunque corregida, sigue basada en años con cobertura mensual parcial en
  2018-2020 (extrapolación desde pocos meses disponibles).

### Lo que sigue siendo un supuesto o un hueco real, documentado sin disimular (🔴):

- Qué tan rápido cambia la actitud de un hogar hacia la separación (sin dato longitudinal
  disponible en ninguna fuente).
- La capacidad de recolección individual de un reciclador de oficio (nadie lo mide).
- El efecto real del incentivo económico sobre el comportamiento — existe el dato de la tarifa,
  pero falta evidencia de que efectivamente cambie comportamiento (es hipótesis a probar con el
  modelo, no un hecho confirmado).
- Camiones individuales, rutas óptimas, y capacidad remanente del Relleno Doña Juana — sin
  ninguna fuente de datos disponible.

---

*Este documento se apoya en, y no reemplaza, `Auditoria_Completa_Datos_Limpieza_EDA.md` (detalle
metodológico completo + glosario de términos técnicos + inventario de cada fuente de datos) y
`Investigacion_Salto_Aprovechamiento.md` (la investigación completa del salto de aprovechamiento,
con las fuentes primarias citadas). Ante cualquier duda sobre CÓMO se calculó un número específico
de este documento, esos dos son la referencia.*
