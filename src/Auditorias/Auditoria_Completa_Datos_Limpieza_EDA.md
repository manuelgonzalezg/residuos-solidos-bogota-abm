# Auditoría Completa: Datos, Limpieza y EDA — Explicada Paso a Paso
### Todo lo que hay que saber para defender este proyecto con total seguridad
**Autores:** Manuel Alejandro González Gallego, Gloria Inés Robledo Ulloa — CUN
**Fecha:** 2026-07-10
**Para quién es este documento:** está escrito asumiendo que quien lo lee **no es programador ni
científico de datos** — eres administrador de empresas, terminando una especialización en
analítica de datos. No se da nada por sabido: cada término técnico se explica la primera vez que
aparece, y hay un glosario completo al final. El objetivo es que puedas explicar cualquier parte
de este proyecto en una sustentación sin depender de memorizar frases — que realmente lo
entiendas.

---

## 0. Cómo leer este documento

Este documento tiene 4 partes:

1. **Mapa general** — de dónde viene cada dato y para qué sirve, en una vista de conjunto.
2. **Inventario de fuentes** — archivo por archivo, qué variables trae cada uno y si sirve o no
   para el modelo (y por qué).
3. **Auditoría de la limpieza** — qué se le hizo a los datos crudos antes de poder usarlos, y por
   qué cada paso era necesario.
4. **Auditoría del EDA** — cada análisis que se hizo: qué se hizo, qué resultado dio, qué
   significa ese resultado, y cómo se debe usar (o no) para el modelo de agentes.

Al final hay un **glosario** con cada término técnico (chi-cuadrado, regresión logística, odds
ratio, p-valor, coroplético, etc.) explicado en una frase simple.

**Una idea que se repite todo el documento y que vale la pena tener clara desde ya:** un dato
"crudo" (tal como lo entrega la fuente oficial) casi nunca se puede usar directamente — trae
errores de formato, códigos numéricos sin traducir, columnas mal alineadas, y en el caso de las
encuestas, un problema más sutil (el "factor de expansión", explicado en la sección 4) que si se
ignora, hace que las conclusiones describan la muestra encuestada y no la ciudad real. Este
proyecto encontró y corrigió varios de estos problemas — se documentan todos aquí, con lo que se
veía ANTES de corregir y lo que se ve DESPUÉS, para que quede clara la diferencia.

---

## 1. Mapa general: de dónde viene cada dato y para qué sirve

El proyecto usa datos de **4 orígenes distintos**:

```
1. DANE / Secretaría de Planeación (SDP)          → quiénes son los habitantes de Bogotá
   - Proyecciones de población por edad/sexo/UPZ
   - Estratificación por manzana (la unidad más pequeña del catastro)

2. UAESP (Unidad Administrativa de Servicios       → cómo se recolectan y disponen los residuos
   Públicos, la entidad que regula el aseo)          y cómo operan los recicladores
   - Series de disposición final (Doña Juana)
   - Recolección mensual por operador (RBL)
   - SIGAB: puntos críticos, contenedores, PQRS
   - Registro de recicladores (RURO)
   - Macrorutas de recolección y barrido

3. DANE (Encuesta Multipropósito) y Secretaría     → cómo se comportan los HOGARES frente a
   de Cultura (Encuesta de Cultura Ambiental)         la separación de residuos
   - Dos encuestas DISTINTAS, con muestras y
     preguntas diferentes (se explica por qué
     importa esta distinción en la sección 4)

4. CRA (Comisión de Regulación de Agua y           → cuánto cuesta y quién paga/recibe subsidio
   Saneamiento) y las empresas de aseo                por el servicio de aseo
   - Tarifas reales, factor de subsidio por estrato
```

Todo esto se junta, a nivel de **UPZ** (Unidad de Planeamiento Zonal — Bogotá tiene 112, son como
"barrios grandes" oficiales, más chicos que una localidad pero más grandes que un barrio) o de
**localidad** (Bogotá tiene 20, son las grandes divisiones administrativas de la ciudad, como
Chapinero, Kennedy, Suba), en una tabla central llamada `df_modelo` — la base de datos ya
integrada y lista para construir el modelo de agentes.

---

## 2. Inventario completo de fuentes de datos

**Cómo leer las tablas de esta sección:** cada fila es una variable (columna) real del archivo.
La columna "Importancia" usa esta escala:

- 🟢 **Alta** — se usa directamente en el modelo o cambió una conclusión real del EDA.
- 🟡 **Media** — se usa como apoyo/control, o tiene potencial pero con limitaciones de calidad.
- ⚪ **Baja** — se revisó pero no aporta al modelo de agentes (aunque puede ser útil para otro
  análisis).
- 🔴 **Descartada** — se investigó y se decidió NO usarla, con la razón explicada.

### 2.1 Población y territorio (carpeta `Demograficas/`)

#### `poblacion_upz` — proyecciones de población DANE por UPZ (2018-2024)

| Variable | Qué es | Importancia |
|---|---|---|
| `UPZ`, `LOC` | Código de la UPZ y de la localidad a la que pertenece | 🟢 Alta — es la llave que conecta todas las demás fuentes |
| `AÑO` | Año de la proyección | 🟢 Alta — permite ver evolución en el tiempo |
| `Hombres_0-4` ... `Hombres_100+`, `Mujeres_0-4` ... `Mujeres_100+`, `Total_0-4` ... `Total_100+` | Población por grupo de edad de 5 años y sexo (la "pirámide poblacional") | 🟡 Media — da la estructura de edad de cada UPZ, pero (hallazgo importante, ver sección 4) no está conectada a nivel individual con quién sí o no separa residuos |
| `Total_Hombres`, `Total_Mujeres`, `Total` | Población total de la UPZ ese año | 🟢 Alta — base para calcular densidad poblacional y para escalar el modelo de agentes a la población real |

**¿Por qué importa?** Es la base para saber cuánta gente vive en cada UPZ — sin esto no se puede
calcular ni densidad poblacional, ni cuántos "agentes hogar" debe representar cada UPZ en el
modelo de simulación.

#### `manzanas` — estratificación oficial por manzana catastral (44,260 manzanas)

| Variable | Qué es | Importancia |
|---|---|---|
| `CODIGO_MANZANA` | Identificador único de la manzana (la cuadra) | 🟢 Alta — es la unidad más pequeña y precisa que existe en todo el proyecto |
| `ESTRATO` | Estrato socioeconómico oficial (0 a 6) | 🟢 Alta — es la variable más importante de todo el proyecto (se explica por qué en la sección 4) |
| `CODIGO_ZONA_ESTRATO`, `CODIGO_CRITERIO`, `NORMATIVA` | Códigos administrativos de cómo se asignó el estrato | ⚪ Baja — trazabilidad legal, no aporta al modelo |
| `ACTO_ADMINISTRATIVO`, `NUMERO_ACTO_ADMINISTRATIVO`, `FECHA_ACTO_ADMINISTRATIVO` | El decreto legal que fijó ese estrato y cuándo | ⚪ Baja — igual, trazabilidad legal |
| `ESCALA_CAPTURA`, `FECHA_CAPTURA`, `RESPONSABLE` | Metadatos técnicos de cómo se capturó el dato geográfico | ⚪ Baja |
| `geometry` | La forma geográfica exacta de la manzana (para dibujar mapas) | 🟢 Alta — sin esto no se pueden hacer los mapas del proyecto |

**¿Por qué importa el estrato?** En Colombia, el estrato (1=más bajo, 6=más alto) es una medida
oficial de nivel socioeconómico de la vivienda, usada para subsidios de servicios públicos.
**Este proyecto encontró que el estrato es, de lejos, la variable individual con más poder
explicativo sobre casi todo** — separación de residuos, presencia de recicladores, e incentivos
económicos, todo se relaciona con el estrato (detalle completo en la sección 4).

#### `upz_limites` — los polígonos (formas geográficas) de las 112 UPZ

| Variable | Qué es | Importancia |
|---|---|---|
| `CODIGO_UPZ`, `NOMBRE` | Identificador y nombre de la UPZ | 🟢 Alta — llave de todos los mapas |
| `EPE__m2_ha`, `EPCC`, `EPT` | Indicadores de espacio público (efectivo, complementario, total) por UPZ | 🔴 Descartada — no se usó porque no hay una hipótesis clara que conecte espacio público con gestión de residuos; queda documentado como disponible por si se necesita después |
| `SHAPE_Leng`, `SHAPE_Area`, `SHAPE_Le_1`, `SHAPE_Ar_1`, `SHAPE_Le_2`, `SHAPE_Ar_2` | Medidas de perímetro/área, repetidas 3 veces (probablemente de recálculos sucesivos del archivo original) | 🔴 Descartada — redundantes, se calcula el área directamente de `geometry` en vez de confiar en estas |
| `geometry` | La forma del polígono | 🟢 Alta — la base de TODOS los mapas del proyecto |

#### `hogares_upz` — proyección de hogares y viviendas por UPZ (2018-2035)

| Variable | Qué es | Importancia |
|---|---|---|
| `Código UPZ`, `UPZ` | Identificador de la UPZ | 🟢 Alta |
| `2018` ... `2035` (una columna por año) | Número de viviendas ocupadas proyectadas ese año | 🟢 Alta — de aquí sale la columna `HOGARES` de `df_modelo`, que determina cuántos "agentes hogar" simula el modelo por UPZ |
| `Departamento`, `Nombre Departamento`, `Municipio`, `Nombre municipio` | Siempre dicen "Bogotá" — son metadatos de la fuente nacional (el archivo cubre todo el país, se filtra solo Bogotá) | ⚪ Baja |

#### `em2021.csv` — Encuesta Multipropósito 2021 (292,282 hogares originales, 234,043 de Bogotá)

Esta es la fuente **más grande y más rica** de todo el proyecto (1,552 columnas en el archivo
original — aquí solo se explican las **40 que este proyecto extrajo**, documentadas también en
`Analisis_Variables_Negocio.md`).

| Variable | Qué pregunta responde | Importancia |
|---|---|---|
| `DIRECTORIO` | Identificador único del hogar encuestado | 🟢 Alta — necesario para no duplicar registros |
| `MPIO`, `COD_LOCALIDAD`, `NOMBRE_LOCALIDAD` | Dónde vive el hogar | 🟢 Alta |
| `FEX_C` | **Factor de expansión** — cuántos hogares reales representa esta única respuesta | 🟢 Alta — crítico (ver sección 4), se usó por primera vez correctamente en esta ronda de revisión |
| `NVCBP11AA` | Estrato para tarifa de energía | 🟢 Alta — el estrato "oficial" de esta encuesta |
| `NHCCP38`, `NHCCP38AA`...`NHCCP38AG` | Si el hogar separa residuos, y qué separa específicamente (orgánicos, vidrio, papel, plástico, metales, otros) | 🟢 Alta — es la variable objetivo central: lo que el modelo busca explicar |
| `NHCCP38B` | Razón por la que NO separa | 🟡 Media — usada en el EDA, muestra completa pero categorías dispersas |
| `NHCDP5`, `NHCDP6` | Si paga por recolección de basuras y cuánto | 🟡 Media — relevante para incentivos económicos, extraída pero no explotada a fondo todavía |
| `NPCJP1F` | Participa en organización ambiental | 🟢 Alta — **resultó ser el predictor más fuerte de separación de residuos de todo el proyecto** |
| `NPCJP1I` | Participa en Junta de Acción Comunal | 🟢 Alta — el segundo predictor más fuerte |
| `NPCKP23` | Ingreso mensual laboral | 🟡 Media — sorprendentemente, deja de ser significativo una vez se controla por estrato/educación (ver sección 4) |
| `NPCKP17` | Posición ocupacional (empleado, independiente, etc.) | ⚪ Baja — se extrajo, no se usó todavía en un análisis específico |
| `OINFORMAL` | Si la persona tiene un empleo informal | 🟢 Alta — la informalidad **reduce** la probabilidad de separar, efecto real y significativo |
| `NPCKP44A` | Relacionada con el trabajo (posiblemente dónde trabaja) | 🔴 Atención — **no está documentada en el diccionario oficial de la encuesta**, se conserva por continuidad histórica pero debe usarse con reserva |
| `NHCLP9C`, `NHCLP9E`, `NHCLP9F` | Percepción de si mejoró/empeoró la disposición de basuras, el barrido, y el reciclaje desde 2017 | ⚪ Baja — extraídas, no analizadas todavía |
| `NHCLP10` | Si los ingresos del hogar alcanzan para los gastos | ⚪ Baja — extraída, no analizada todavía |
| `NHCLP11` | Si se considera pobre | ⚪ Baja — extraída, no analizada todavía |
| `NPCHP4` | Nivel educativo más alto alcanzado | 🟢 Alta — significativo en la regresión, aumenta modestamente la probabilidad de separar |
| `NPCHP1` | Si sabe leer y escribir | ⚪ Baja — extraída, no analizada todavía (esperable alta correlación con NPCHP4) |
| `NHCCPCTRL2` | Número de personas del hogar | 🟢 Alta — significativo, hogares más grandes separan un poco más |
| `NVCBP10` | Tipo de vivienda (casa/apartamento/cuarto/otro) | 🟢 Alta — usada como proxy de tenencia ("vivienda propia"), uno de los efectos más fuertes |
| `NVCBP4` | Si la vivienda está en conjunto residencial | ⚪ Baja — extraída, no analizada todavía |
| `NVCBP9` | Si hay un negocio en la vivienda | ⚪ Baja — extraída, no analizada todavía |
| `NHCCP35` | Disponibilidad de baño | ⚪ Baja — extraída, no analizada todavía (más relevante para pobreza estructural que para residuos) |
| `NVCBP11D` | Acceso a servicio de recolección de basuras | 🟡 Media — relevante para infraestructura, extraída, no analizada todavía |
| `NVCBP14B` | Vivienda cerca de basureros/botaderos | 🟡 Media — relevante para el mecanismo de "entorno degradado", extraída, no analizada todavía |
| `NVCBP14I` | Vivienda cerca de caños de aguas residuales | ⚪ Baja — más relacionada con saneamiento que con residuos sólidos |
| `NVCBP15F` | Entorno con disposición inadecuada de basuras | 🟡 Media — relevante, extraída, no analizada todavía |
| `NVCBP15K` | Entorno con disposición inadecuada de residuos hospitalarios | ⚪ Baja — caso específico, poco relevante para el modelo general |
| `NHCCP37` | Cómo elimina la basura el hogar (recolección formal, tirar a río/lote, quemar, etc.) | 🟢 Alta — variable de "peor escenario" (más grave que simplemente "no separa"), extraída, no analizada todavía en detalle |

**Nota importante sobre esta tabla:** varias variables están marcadas ⚪ "extraídas, no
analizadas todavía" — significa que ya están limpias y disponibles, pero el EDA no alcanzó a
cruzarlas todas contra la separación de residuos. Es trabajo pendiente explícito, no un error.

### 2.2 Residuos y logística (carpeta `Residuos/`)

#### `residuos_dj` (`Residuos generados bogota.xlsx`) — serie histórica 2018-2025

| Variable | Qué es | Importancia |
|---|---|---|
| `año` | Año de la medición | 🟢 Alta |
| `Residuos_Generados_ton` | Toneladas generadas ese año en toda la ciudad | 🟢 Alta — el "tamaño total del problema" |
| `Residuos_Aprovechados_ton`, `Pct_Aprovechamiento` | Cuánto se aprovechó, en toneladas y en % | 🟢 Alta — es LA variable que el proyecto entero busca explicar |
| `Residuos_No_Aprovechados_ton`, `Pct_Disposicion_Final` | Lo que no se aprovechó y terminó en el relleno | 🟢 Alta |
| `Residuos_DJ_ton`, `Residuos_DJ_pc_ton` | Toneladas que llegaron al Relleno Doña Juana (total y per cápita) | 🟢 Alta — el destino final |

#### `caracterizacion_residuos` — composición mensual de los residuos (2015-2026, 133 meses)

| Variable | Qué es | Importancia |
|---|---|---|
| `año` | Año/mes de la medición | 🟢 Alta |
| `Cartón`, `Caucho`, `Cenizas`, `Cerámica`, `Cuero`, `Hueso`, `Ladrillo`, `Madera`, `Materia Orgánica`, `Metales`, `Minerales`, `Papel`, `Plástico`, `Textil`, `Vidrio`, `Otros` | Proporción de cada material en la basura total | 🟡 Media — da un techo teórico de cuánto se podría aprovechar, pero es un dato agregado de ciudad, no por UPZ |
| `Total` | Suma de todas las categorías (debería dar 1.0 = 100%) | 🟢 Alta — usado para verificar que los datos cuadran (y se encontró y corrigió un error real de suma en la Fase 1) |

#### `tipo_residuos_localidad` — composición por localidad (sin fecha, 19 de 20 localidades)

| Variable | Qué es | Importancia |
|---|---|---|
| `localidad` | Nombre de la localidad | 🟢 Alta |
| `organicos_ton_dia`, `plasticos_ton_dia`, `celulosas_ton_dia`, `vidrio_ton_dia`, `metales_ton_dia`, `textiles_ton_dia` | Toneladas por día de cada tipo de material | 🟡 Media — dato real y territorial (mejor que el agregado de ciudad), pero sin fecha clara y le falta Sumapaz |

#### `recicladores_ruro` — Registro Único de Recicladores de Oficio (24,196 personas)

| Variable | Qué es | Importancia |
|---|---|---|
| `Nº` | Consecutivo del registro | ⚪ Baja |
| `LOCALIDAD VIVIENDA` | Dónde vive el reciclador | 🟢 Alta — permite contar recicladores por localidad |
| `GENERO` | Género (14,041 hombres / 10,155 mujeres) | ⚪ Baja — no se usó en el modelo, disponible si se necesita |
| `EDAD` | Edad del reciclador | 🟡 Media — se usa como "edad promedio" por localidad, dato delgado (un solo número, no una distribución) |
| `NIVEL EDUCATIVO` | Nivel educativo alcanzado | 🔴 Descartada por ahora — categorías duplicadas por errores de mayúsculas/espacios (ej. "PRIMARIA" aparece 3 veces distinto), necesitaría limpieza adicional antes de usarse |
| `QUE MEDIO DE RECOLECCION UTILIZA` | Cómo recoge el material (a pie, carretilla, camión, etc.) | 🔴 Descartada por ahora — mismo problema de categorías duplicadas |

#### `grandes_generadores` — puntos geolocalizados de grandes generadores (7,456 puntos)

| Variable | Qué es | Importancia |
|---|---|---|
| `CONCESIONARIO` | Qué empresa de aseo lo atiende | 🔴 Descartada — 96% de las filas no tienen este dato (nulo) |
| `ID LOCALIDAD` | Localidad del punto | 🟡 Media |
| `DIRECCION`, `NOMBRE` | Dirección y nombre del establecimiento | ⚪ Baja — texto libre, no estructurado para análisis |
| `FECHA VIG` | Mes de vigencia del registro | ⚪ Baja — solo 7 valores distintos, cobertura temporal limitada |
| `LONGITUD`, `LATITUD` | Coordenadas geográficas | 🟢 Alta — permiten ubicar los puntos en el mapa y contarlos por UPZ |

#### `superservicios_residuos` — reporte nacional de Superservicios (filtrado a Bogotá: 42 de 2,760 filas)

| Variable | Qué es | Importancia |
|---|---|---|
| `NOMBRE_EMPRESA` | Empresa prestadora | 🟡 Media |
| `AÑO_DEL_CARGUE` | Año del reporte (2016-2024) | 🟢 Alta — serie temporal real |
| `MUNICIPIO_ÁREA_DE_PRESTACIÓN` | Municipio — **hay que filtrar explícitamente "BOGOTA"**, el archivo es nacional | 🟢 Alta (como filtro, no como variable en sí) |
| `TONELADAS_DE_RESIDUOS_APROVECHABLES`, `TONELADAS_DE_RESIDUOS_NO_APROVECHABLES`, `TONELADAS_DEL_RECHAZO_DE_APROVECHAMIENTO` | Toneladas por categoría | 🟡 Media — otra fuente independiente para verificar los números de aprovechamiento |
| `TONELADAS_DE_LIMPIEZA_URBANA`, `TONELADAS_DE_BARRIDO_Y_LIMPIEZA_URBANA` | Toneladas de barrido/limpieza | ⚪ Baja |
| `VALOR_PEAJE`, `SISTEMA_DE_MEDICIÓN` | Detalles operativos del sitio de destino | ⚪ Baja |

#### La carpeta RBL — Recolección, Barrido y Limpieza (97 archivos, 2017-2026) → ya consolidada

| Variable (del archivo consolidado) | Qué es | Importancia |
|---|---|---|
| `anio`, `mes` | Cuándo se recolectó | 🟢 Alta — serie mensual real, la más larga del proyecto |
| `esquema` | Si el operador usa el esquema antiguo de "zonas" (2017-2019) o el nuevo de "ASE" (2018-2026, con solapamiento real encontrado) | 🟢 Alta — necesario para no mezclar operadores incomparables |
| `operador` | Cuál de los 5 ASE (o el esquema antiguo) recolectó | 🟢 Alta |
| `tipo_residuo` | Domiciliario, barrido, corte de césped, grandes generadores, mixtos, poda de árboles, voluminosos | 🟢 Alta |
| `toneladas` | Cantidad recolectada | 🟢 Alta — es la base para calcular la capacidad real de cada operador |

### 2.3 Cultura y comportamiento ambiental (carpeta `Cultura/`)

#### `cultura_ambiental_localidad` — agregado de 20 filas, una por localidad

| Variable | Qué es | Importancia |
|---|---|---|
| `localidad`, `cod_localidad` | Identificador | 🟢 Alta |
| `n_encuestas` | Cuántas personas de esa localidad fueron encuestadas | 🟢 Alta — **crítico**: hay localidades con n=1 (Los Mártires) y n=3 (Santa Fe) — cualquier estadística de esas localidades es prácticamente anecdótica, no confiable |
| `pct_separa_en_fuente`, `pct_calidad_separacion` | % que separa y qué tan bien separa | 🟢 Alta — usada en todo el proyecto, pero recordar el problema de `n_encuestas` |
| `estrato_promedio` | Estrato promedio de la localidad | 🟢 Alta |

#### `cultura_ambiental_crudo` (Encuesta de Cultura Ambiental — ECA 2021) — 2,282 encuestas individuales

Encuesta específica de comportamiento ambiental (no socioeconómica como EM2021). Columnas clave
usadas en el EDA:

| Variable | Qué es | Importancia |
|---|---|---|
| `a. LOCALIDAD` | Localidad del encuestado | 🟢 Alta |
| Pregunta de estrato (energía eléctrica) | Estrato del encuestado | 🟢 Alta |
| `¿Cuántos años cumplidos tiene usted? (Mayor)` | **Edad** — encontrada en esta auditoría, antes sin usar | 🟢 Alta — significativa: cada año adicional de edad aumenta ~4% la probabilidad de separar (controlando por estrato) |
| `4. En general, ¿usted separa sus residuos?` | Variable objetivo de esta encuesta | 🟢 Alta |
| `8. ¿Cuál es la principal razón...?` | Motivación para separar | 🟢 Alta — "porque es bueno para el ambiente" domina claramente |
| `12. ¿Cuál es la principal dificultad...?` | Obstáculo para separar | 🟢 Alta — "que todos en el hogar separen" y "falta de espacio" son las más comunes |
| `FACTOR PERSONAS`, `FACTOR HOGARES`, `PONDERADOR` | Factores de expansión de la encuesta | 🟢 Alta — críticos, usados solo en esta última ronda de revisión |
| Las demás ~100 columnas (fauna silvestre, animales de compañía, espacios naturales, etc.) | Preguntas de otros temas ambientales, no de residuos | 🔴 Descartadas para este proyecto — la encuesta es multitemática, solo la parte de residuos aplica aquí |

#### `diccionario_em2021` — el diccionario oficial de la Encuesta Multipropósito

No es un dato en sí — es la "traducción" de todos los códigos de `em2021.csv`. **Esencial**: sin
él, sería imposible saber qué significa cada código numérico de las respuestas.

### 2.4 Otras fuentes puntuales (carpeta `Otros/`)

| Fuente | Qué es | Importancia |
|---|---|---|
| `puntos_limpios` (`dataset-gestion-residuos-punto-limpio-2020.xlsx`) | Un solo "punto limpio", mayo-diciembre 2020, con 2 de 5 columnas completamente vacías | 🔴 Descartada — dato demasiado incompleto para usarse |
| `cantidad_entregada_ases` | Distribución % de material entregado por ASE, sin fecha clara | ⚪ Baja — activada en el código, pero de uso limitado por falta de fecha |

### 2.5 Fuentes externas nuevas (carpeta `externo_fase2/`, traídas en la Fase 2)

#### SIGAB (Sistema de Información para la Gestión de Aseo de Bogotá) — 4 cortes en el tiempo

| Variable (puntos críticos) | Qué es | Importancia |
|---|---|---|
| `CONCESIONARIO`, `IDLOCALID`, `DIRECCION` | Quién opera y dónde está el punto crítico | 🟢 Alta |
| `FRECUENCIA` | Con qué frecuencia se atiende ese punto | 🟡 Media |
| `LONGITUD`, `LATITUD` | Coordenadas — permiten contar puntos críticos por UPZ | 🟢 Alta — dato central del análisis geoespacial avanzado de este proyecto |
| Variable (PQRS por localidad/estrato/concesionario) | Qué es | Importancia |
| `PERIODO` | Mes del reporte, formato AAMM — **hallazgo importante**: cada archivo es un acumulado de hasta 59 meses, no un solo mes (se corrigió tomando solo el último período) | 🟢 Alta |
| `LOCALIDAD`/`ESTRATO`/`CONCESIONARIO`, `CANTIDAD` | Cuántas PQRS de aseo hubo | 🟢 Alta — único proxy cuantitativo de gobernanza institucional que existe en todo el proyecto |
| `contenedores`, `grandes_generadores` (dentro de SIGAB) | Ubicación y capacidad de contenedores y grandes generadores | 🟡 Media — extraídas, exploradas parcialmente |

#### Macrorutas de recolección y de barrido (125 + 179 zonas reales)

| Variable | Qué es | Importancia |
|---|---|---|
| `NOMLOCALID` / `Nombre_Localidad` | Localidad de la zona | 🟢 Alta |
| `NOMFRECUEN` | Frecuencia semanal real (ej. "Lunes a Sábado") | 🟢 Alta — primera vez que el proyecto tiene la estructura operativa real, no solo toneladas agregadas |
| `HORAINICIO`, `HORAFIN` | Horario de la ruta | 🟡 Media |
| `geometry` | Forma geográfica de la zona | 🟢 Alta |

#### RURO oficial 2012-2021 (8 mini-tablas) y RURO 2022 por localidad

| Variable | Qué es | Importancia |
|---|---|---|
| Serie anual de registros (2012-2021) | Cuántos recicladores se registraron cada año | 🟡 Media |
| **Estado: Activo (24,895) vs. Retirado (2,785)** | Si sigue vigente en el registro | 🟢 Alta |
| Causas de retiro (cédula no encontrada, fallecido, etc.) | Por qué salió del registro | ⚪ Baja — informativo, no se usa en el modelo |
| Discapacidad por tipo | Composición de la población recicladora | ⚪ Baja |
| **Nivel de afiliación a salud (Subsidiado ~20,401 vs. Contributivo ~1,412)** | Proxy de informalidad laboral | 🟢 Alta — hallazgo central: casi nadie está en el régimen formal |
| Tipo de vivienda (Arrendada, Propia, Calle, Invasión...) | Proxy de precariedad económica | 🟢 Alta |
| **`#ARL`** (RURO 2022, afiliación a riesgos laborales) | El indicador MÁS directo de formalización laboral real | 🟢 Alta — **hallazgo más importante de esta fuente**: entre 0% y 14.3% según localidad, prácticamente inexistente |
| `Rangos_Edad`, `Nivel Educativo`, `#Cabeza_Hogar`, `#Analfabetas`, `#HabCalle`, `#Pensionados` (RURO 2022) | Composición social de los recicladores por localidad | 🟡 Media — documentadas, no analizadas todavía en detalle |

#### Tarifas CRA / Ciudad Limpia (diciembre 2025)

| Variable | Qué es | Importancia |
|---|---|---|
| **VIAT** ($11,388/tonelada) | Valor del Incentivo al Aprovechamiento y Tratamiento | 🟢 Alta — primer dato económico real del proyecto |
| Factor de subsidio/contribución por estrato (-70% a +60%) | Cuánto paga de más o de menos cada estrato | 🟢 Alta — combinado con la composición de estratos por UPZ, da un mapa real de incentivo económico |
| Costos de referencia (CBL, CLUS, CRT, CDF, CCS, CTL, VBA) | Estructura de costos del servicio | ⚪ Baja — informativo, no se usa directamente en el modelo |

#### PGIRS (Plan de Gestión Integral de Residuos Sólidos) — documento, no tabla

🟡 Media — marco normativo/institucional citable en el texto de la tesis, no es una variable
cuantitativa para el modelo.

#### "Consolidado PQRS" genérico — 🔴 Descartada

Se descargó y se verificó a fondo: **resultó ser exclusivamente del IDU** (obras viales), no de
aseo/UAESP. Se descarta explícitamente como fuente de gobernanza de residuos.

---

## 3. Auditoría de la limpieza — qué se le hizo a los datos y por qué era necesario

Los archivos de Excel/CSV oficiales casi nunca vienen "listos para usar" — tienen títulos antes
del encabezado real, columnas con nombres inconsistentes entre meses, códigos numéricos que
significan cosas distintas para cada pregunta, etc. Esta sección explica, en español simple,
cada "arreglo" que se le tuvo que hacer a los datos antes de poder analizarlos.

### 3.1 "Encontrar dónde empieza realmente la tabla" (`detectar_fila_encabezado`)

**El problema:** muchos archivos de Excel oficiales tienen 1, 2 o hasta 8 filas de título antes
de la fila que realmente tiene los nombres de columna (ej. la primera fila de un archivo de RBL
de diciembre 2023 dice literalmente "DICIEMBRE 2023" en vez de "ASE y Concesionario"). Si el
programa asume que la fila 0 siempre es el encabezado, mezcla el título con los datos y todo se
rompe.

**Qué se hizo:** en vez de asumir una posición fija, el programa **busca** en las primeras
filas cuál de ellas contiene ciertas palabras clave esperadas (ej. "ASE" o "CONCESIONARIO"), y
usa esa como el encabezado real. Es como si, al abrir un documento, en vez de asumir que el
título está siempre en la línea 3, se buscara la línea que dice "Nombre, Apellido, Edad" y se
empezara a leer desde ahí.

**Por qué importa:** sin esto, cualquier archivo con un formato ligeramente distinto (y varios
lo tenían) habría producido una tabla con los datos en el lugar equivocado, sin que fuera obvio
a simple vista — el tipo de error más peligroso, porque el programa no se cae, simplemente da
resultados incorrectos en silencio.

**Bug real encontrado y corregido con esta técnica:** al construir el consolidado de la carpeta
RBL, usar la palabra "ASE" como pista para encontrar el encabezado parecía razonable — pero
resultó que la palabra "ASE" también aparece **dentro de los datos** (ej. "ASE 1 Promoambiental"
es un valor de una fila, no un encabezado). Esto hacía que el programa, en algunos archivos,
detectara por error la primera fila de DATOS como si fuera el encabezado, y todo el año 2021 se
perdía de la serie. Se corrigió cambiando la palabra clave a "CONCESIONARIO"/"OPERADOR", que sí
aparecen solo en encabezados reales.

### 3.2 "Quedarte solo con las filas que sí son datos" (`recortar_filas_validas`)

**El problema:** después del encabezado, muchos archivos tienen filas finales de "Fuente:
Secretaría de..." o notas al pie, que no son datos reales pero podrían confundirse con una fila
más de la tabla.

**Qué se hizo:** se conserva solo las filas donde una columna clave (ej. el código de UPZ) es
realmente un número — cualquier fila de texto libre al final se descarta automáticamente.

### 3.3 "Convertir texto a números, sin adivinar mal" (`convertir_numericas` y el parseo del RBL)

**El problema más sutil de todo el proyecto:** los números en español a veces se escriben con
punto para los miles y coma para los decimales (ej. "22.132,99" significa veintidós mil ciento
treinta y dos con noventa y nueve), pero en inglés/en las hojas de cálculo más modernas es al
revés (punto = decimal). Un archivo de 2020 tenía el número "34.659" que **debía** leerse como
"34 mil 659" (formato en español, sin parte decimal), pero el programa lo leyó primero como "34
punto 659" (formato en inglés) — un error de **casi 1000 veces** en la magnitud del dato, que
pasó sin que nadie lo notara hasta que se comparó contra el orden de magnitud esperado (miles de
toneladas al mes, no decenas).

**Qué se hizo:** se estableció una regla clara — todos los archivos CSV de 2017 a 2020 siempre
están en formato español (se les aplica la conversión española sin excepción), y los archivos
Excel de 2021 en adelante ya vienen con los números correctos desde la fuente (no necesitan
conversión). Antes, el programa intentaba adivinar el formato número por número, lo cual era la
causa del error.

**Por qué esto es un ejemplo perfecto de por qué hay que verificar, no solo confiar:** el
programa "corrió sin errores" con el bug adentro — no hubo ningún mensaje de alerta. Solo se
encontró al **mirar el gráfico resultante y notar que los números no tenían sentido** (una caída
de 30,000 toneladas a 30 toneladas de un mes a otro, algo físicamente imposible para una ciudad
del tamaño de Bogotá).

### 3.4 "Arreglar el error de la suma que no daba 100%" (composición de residuos)

**El problema:** al calcular qué porcentaje de la basura es orgánica, cuál es plástico, etc., el
cálculo original promediaba cada categoría por separado. El problema es que si en un mes falta el
dato de una categoría (ej. no se reportó "Cerámica" ese mes), rellenarlo con cero y promediar así
nomás hace que la suma total de todas las categorías, para ese año, no dé exactamente 100% — se
"pierde" el peso de la categoría faltante.

**Qué se hizo:** en vez de promediar las columnas crudas, primero se ajusta CADA registro
individual para que sus categorías sumen exactamente 100% (esto se llama "normalizar"), y solo
después se promedia. Es la diferencia entre promediar "cómo se ve cada mes tal cual llegó" versus
"ajustar cada mes primero para que las proporciones tengan sentido, y luego promediar esos meses
ya ajustados".

### 3.5 Encodings — por qué algunos archivos mostraban símbolos raros (Ã±, ó, etc.)

**El problema:** los computadores guardan el texto como números binarios, y existen varias
"tablas de traducción" (encodings) distintas para convertir esos números en letras. Si un
archivo se guardó con una tabla y se lee con otra, las tildes y eñes se convierten en símbolos
sin sentido.

**Qué se hizo:** se identificó, archivo por archivo, cuál tabla de codificación usa cada fuente
(la mayoría de archivos gubernamentales colombianos usan "latin-1"; el archivo de recicladores
RURO usa una tabla más antigua llamada "cp850", típica de sistemas MS-DOS heredados) y se
especificó explícitamente al leer cada uno.

**Verificación importante hecha en esta auditoría:** se revisó, byte por byte, si los símbolos
raros que se veían en algunos análisis eran datos realmente dañados o solo un problema de cómo
la pantalla los mostraba — **se confirmó que era solo la pantalla** (la terminal de Windows no
sabe mostrar ciertos caracteres, pero el archivo en sí tiene la letra correcta guardada). No se
tuvo que corregir ningún archivo por esto, solo se documentó la causa para no alarmarse la
próxima vez que aparezca.

### 3.6 Traducir códigos numéricos a su significado real (diccionarios de encuestas)

**El problema:** en las encuestas (ECA 2021, EM2021), las respuestas no se guardan como texto
("Sí", "No") sino como números (1, 2, 99...) — el mismo número significa algo distinto en cada
pregunta (en una pregunta 1="Sí", en otra 1="Porque es bueno para el ambiente"). Sin la "llave"
que traduce cada código, cualquier gráfico mostraría números sin sentido en vez de respuestas
reales.

**Qué se hizo:** se construyó una función que lee el diccionario oficial de cada encuesta (un
archivo separado que sí trae la traducción de cada código) y arma automáticamente la tabla de
traducción por pregunta, para no tener que escribirla a mano (lo cual sería lento y propenso a
errores de tipeo).

### 3.7 Resumen de bugs reales encontrados y corregidos en esta fase

| Bug | Dónde | Cómo se detectó | Efecto si no se corrige |
|---|---|---|---|
| Encabezado detectado en la fila equivocada | Consolidado RBL, año 2021 | Al revisar la tabla resultante, faltaba un año completo | Se pierde toda la información de un año en la serie |
| Error de magnitud ~1000x en números | Consolidado RBL, archivos de 2020 | Al mirar el gráfico y ver una caída físicamente imposible | Cualquier conclusión sobre 2020 sería falsa |
| Archivos de PQRS mal interpretados como "un mes" cuando eran 59 meses acumulados | SIGAB, sección de gobernanza | Al ver que el número de PQRS era absurdamente alto (170,000+ en una localidad en un mes) | La comparación 2020 vs. 2022 habría mezclado años distintos de historia |
| Análisis estadístico sin el factor de expansión de la encuesta | Toda la Sección 1 y 8 del EDA | Pregunta directa y específica del usuario | Las conclusiones describirían solo a los encuestados, no a la población real de Bogotá |
| Variable de edad disponible pero nunca usada | ECA 2021 | Auditoría exhaustiva pedida por el usuario | Se perdía una variable real y significativa del análisis |

---

## 4. Auditoría del EDA — cada análisis, explicado: qué se hizo, qué dio, qué significa, cómo se usa

### 4.0 Antes de empezar: qué es el "factor de expansión" y por qué es tan importante

Imagina que quieres saber qué opina Bogotá sobre algo, pero no puedes preguntarle a los 8
millones de habitantes — encuestas a 2,282 personas (ECA) o a 234,043 hogares (EM2021), elegidas
con un método estadístico cuidadoso para que la muestra "se parezca" a la ciudad. El problema es
que, aunque el método es bueno, nunca es perfecto: es posible (y de hecho pasó en este proyecto)
que ciertos estratos, localidades o tipos de persona queden un poco sobre-representados o
sub-representados en la muestra final, por razones prácticas de cómo se hizo el trabajo de
campo.

El **factor de expansión** (`FEX_C` en EM2021; `PONDERADOR`, `FACTOR PERSONAS` y `FACTOR
HOGARES` en ECA2021) es un número que la misma entidad que hizo la encuesta calculó para cada
persona encuestada, diciendo: "esta persona, en las cuentas finales, debe contar como si
representara a X personas reales de Bogotá". Si no se usa este número al calcular porcentajes o
correlaciones, lo que se obtiene describe **la muestra que efectivamente se encuestó**, no la
ciudad real.

**Esto fue exactamente lo que pasó en la primera versión de este EDA** — el usuario preguntó
directamente si se había usado el factor de expansión, la respuesta honesta fue que no, y se
corrigió todo el análisis estadístico. Las diferencias encontradas fueron reales (se detallan
más abajo), aunque ninguna conclusión cambió de dirección.

### 4.1 Sección 1 del EDA — Separación en la fuente y calidad

#### Análisis 1: tendencia del % de aprovechamiento de la ciudad, 2018-2025

- **Qué se hizo:** un gráfico de línea simple, año por año, del porcentaje de residuos
  aprovechados en toda Bogotá.
- **Qué dio:** una tendencia relativamente estable entre 15% y 20% hasta 2023, y un salto grande
  a 43.88% en 2024.
- **Qué significa:** un cambio de esa magnitud en un solo año es inusual — lo más probable es que
  no sea un cambio real de comportamiento ciudadano de la noche a la mañana, sino un cambio en
  cómo se mide o reporta el aprovechamiento (ej. una nueva metodología del operador, o la entrada
  en operación de nueva infraestructura). Esto ya se había señalado en fases anteriores del
  proyecto y se sigue sosteniendo con los datos consolidados.
- **Cómo se usa:** como advertencia — cualquier modelo que use el año 2024 en adelante como
  "línea base" sin marcar ese quiebre estaría escondiendo una discontinuidad real de los datos.

#### Análisis 2: mapa de % de separación por UPZ

- **Qué se hizo:** un **mapa coroplético** (un mapa donde cada zona se pinta de un color según el
  valor de una variable — más oscuro = más alto) mostrando el % de separación en cada una de las
  112 UPZ.
- **Qué dio:** variación visible entre UPZ, sin un patrón perfectamente uniforme.
- **Qué significa:** confirma que el aprovechamiento **no es igual en toda la ciudad** — hay
  zonas que separan más que otras, lo cual es justo el tipo de desigualdad territorial que la
  pregunta de investigación del proyecto busca explicar.
- **Cómo se usa:** es la base visual para decidir si el modelo de agentes debe tener variación
  por UPZ (si) o si bastaría un solo número de ciudad (no, porque sí hay variación real).

#### Análisis 3: razones y dificultades reales para separar (microdato individual de la ECA 2021)

- **Qué se hizo:** en vez de solo ver el porcentaje que separa, se preguntó **por qué** — usando
  las respuestas individuales de la encuesta (no un promedio, sino cada persona real), traducidas
  de códigos a texto real, y comparadas ponderadas (representando a la ciudad) contra sin
  ponderar (solo la muestra).
- **Qué dio:** la razón principal para separar es, de lejos, "porque es bueno para el ambiente" —
  muy por encima de razones económicas ("para vender") o sociales ("para ayudar a los
  recicladores"). La dificultad principal es "que todas las personas del hogar separen" y "no hay
  suficiente espacio para varias canecas".
- **Qué significa:** la motivación de la gente que sí separa es mayormente ambiental/de
  conciencia, no económica — y el obstáculo principal no es "no querer", sino problemas prácticos
  de coordinación dentro del hogar y de espacio físico en la vivienda.
- **Cómo se usa:** esto es evidencia real a favor de que el modelo de agentes debe representar la
  separación como algo que depende de **coordinación social dentro del hogar y con los vecinos**
  (el "mecanismo de imitación social" de la hipótesis original), no solo de un cálculo económico
  individual.

#### Análisis 4: ¿el estrato influye en si se separa? (chi-cuadrado)

- **Qué se hizo:** una **prueba de chi-cuadrado** (una prueba estadística que responde: "¿la
  relación entre estas dos variables categóricas que veo en los datos es lo bastante fuerte como
  para no ser solo casualidad?"), comparando estrato contra si la persona separa o no, con la
  encuesta ponderada y sin ponderar.
- **Qué dio:** sin ponderar, chi²=18.3 con p=0.0026; ponderado (el número correcto a citar),
  chi²=14.0 con p=0.0156.
- **Qué significa el "p-valor":** es la probabilidad de ver una relación tan fuerte como la
  observada, **si en realidad no hubiera ninguna relación real** entre estrato y separación. Un
  p-valor de 0.0156 significa que, si no hubiera relación real, veríamos un resultado así de
  fuerte por puro azar menos del 2% de las veces — lo suficientemente raro como para concluir que
  sí hay una relación real (el punto de corte convencional en estadística es 5%, o 0.05).
- **Cómo se usa:** confirma, con evidencia estadística formal (no solo "se ve en el mapa"), que el
  estrato debe ser una variable del modelo de agentes.

#### Análisis 5: ¿la edad influye? (agregado en esta auditoría)

- **Qué se hizo:** se encontró que la ECA 2021 sí tiene una variable de edad individual (que no se
  había usado) y se probó, ponderada, junto con el estrato.
- **Qué dio:** odds ratio de 1.04 para edad, con p<0.0001 (muy significativo).
- **Qué significa un "odds ratio" de 1.04:** por cada año adicional de edad, las probabilidades
  (no el porcentaje directo, sino la "razón de momios" — ver glosario) de separar residuos suben
  un 4%. Puede sonar poco, pero se acumula: la diferencia entre alguien de 20 años y alguien de
  60 años sería, aproximadamente, (1.04 elevado a 40) ≈ 4.8 veces más probable de separar, si todo
  lo demás fuera igual.
- **Cómo se usa:** es evidencia de que la edad sí debería considerarse al construir los perfiles
  de los "agentes hogar" del modelo — las personas mayores parecen tener más disposición a
  separar.

### 4.2 Sección 2 del EDA — Recolección y logística

#### Análisis 6: toneladas recolectadas por operador (ASE), 2018-2026

- **Qué se hizo:** un gráfico de líneas, una por cada uno de los 5 operadores de aseo (ASE),
  mostrando el promedio mensual de toneladas domiciliarias recolectadas cada año (se usa
  **promedio**, no suma total, porque algunos años no tienen los 12 meses de datos disponibles, y
  sumar un año incompleto se vería como una caída falsa).
- **Qué dio:** cada operador mantiene un volumen relativamente estable (entre ~15,000 y ~50,000
  toneladas/mes según el operador) a lo largo de los 8 años, sin caídas ni saturación visible.
- **Qué significa:** el sistema formal de recolección parece tener capacidad sobrante o al menos
  suficiente — nunca se ve un operador "topando" con un límite de capacidad de forma evidente en
  los datos históricos.
- **Cómo se usa:** da evidencia real (no solo un supuesto) para el diseño del ABM de que la
  recolección formal casi nunca es el cuello de botella del sistema — el problema está en otro
  lado (probablemente separación en la fuente, no en la capacidad de recoger).

#### Análisis 7: mapa de macrorutas reales, coloreado por frecuencia

- **Qué se hizo:** un mapa donde cada zona de recolección real de Bogotá se pinta según con qué
  frecuencia semanal pasa el camión (ej. todos los días vs. 3 veces por semana).
- **Qué dio:** la frecuencia varía geográficamente, no es uniforme en toda la ciudad.
- **Qué significa:** confirma con datos reales (por primera vez en el proyecto) que existe una
  estructura operativa real distinta por zona, más allá de solo saber cuántas toneladas se
  recogen en total.
- **Cómo se usa:** puede alimentar un nuevo atributo del modelo de agentes (frecuencia de
  recolección por UPZ), en vez de asumir que la recolección siempre pasa igual en todas partes.

#### Análisis 8: puntos críticos de acumulación por UPZ, en 4 momentos del tiempo (2020, 2022, 2024, 2026)

- **Qué se hizo:** cuatro mapas lado a lado (llamados **pequeños múltiplos**), todos con la misma
  escala de color, mostrando cuántos puntos críticos de acumulación de basura hay en cada UPZ, en
  4 momentos distintos.
- **Qué dio:** el mismo grupo de UPZ (una zona del centro-norte de la ciudad) aparece
  consistentemente como el de más puntos críticos en los 4 cortes.
- **Qué significa:** el problema de puntos críticos **no es aleatorio ni cambia mes a mes** — es
  un patrón territorial persistente en el tiempo, lo que sugiere una causa estructural (no un
  evento pasajero).
- **Cómo se usa:** este hallazgo (medido con un número llamado "coeficiente de variación" = 1.19,
  que indica alta variación entre zonas) es la evidencia que sostiene la recomendación de tratar
  la infraestructura/puntos limpios como su propio "mecanismo" en el modelo de agentes, en vez de
  asumir que la infraestructura es más o menos igual en toda la ciudad.

#### Análisis 9: mapa bivariado — estrato y puntos críticos combinados

- **Qué se hizo:** un **mapa bivariado** (una técnica avanzada que combina 2 variables en un solo
  mapa, usando una cuadrícula de 9 colores en vez de una sola escala) mostrando, a la vez, el
  estrato promedio y el número de puntos críticos de cada UPZ.
- **Qué dio:** hay zonas de estrato alto que también tienen puntos críticos altos — la relación no
  es tan simple como "estrato bajo = más problemas de basura".
- **Qué significa:** el supuesto original del modelo (una fórmula que asumía que solo estrato
  bajo y densidad explican la falta de infraestructura) **no se sostiene completamente** con el
  dato real — hay más factores en juego que los dos que se habían asumido.
- **Cómo se usa:** justifica reemplazar la fórmula sintética/inventada del modelo por el conteo
  real de puntos críticos, en vez de seguir asumiendo la fórmula original.

### 4.3 Sección 3 del EDA — Recicladores y formalización

#### Análisis 10: recicladores registrados por año, y estado Activo vs. Retirado

- **Qué se hizo:** un gráfico de barras del número de recicladores registrados cada año
  (2012-2021), y otro comparando cuántos siguen "Activos" en el registro vs. "Retirados".
- **Qué dio:** 89.9% siguen activos, 10.1% se retiraron (por razones documentadas: cédula no
  encontrada, fallecimiento, etc.).
- **Qué significa:** el registro oficial (RURO) parece razonablemente actualizado — la mayoría de
  quienes se registraron siguen vigentes en el sistema.
- **Cómo se usa:** da el tamaño de la "población base" de recicladores que el modelo puede asumir
  como realmente activa.

#### Análisis 11: tipo de afiliación a salud y tipo de vivienda

- **Qué se hizo:** dos gráficos de barras horizontales mostrando cuántos recicladores tienen cada
  tipo de afiliación a salud (Subsidiado, Contributivo, etc.) y cada tipo de vivienda (Arrendada,
  Propia, Calle, etc.).
- **Qué dio:** ~20,401 recicladores están en régimen Subsidiado (el que reciben las personas sin
  capacidad de pago) contra solo ~1,412 en Contributivo (el régimen de un empleo formal). En
  vivienda, "Arrendada" domina claramente, con categorías de alta precariedad (Calle, Cambuche,
  Invasión) también presentes.
- **Qué significa:** confirma, con datos reales, que la población recicladora es
  **mayoritariamente informal y con condiciones de vida precarias** — no es una suposición, es lo
  que muestran los datos oficiales.
- **Cómo se usa:** sostiene la decisión de modelar a los recicladores como una población que opera
  fuera de esquemas laborales formales.

#### Análisis 12: % de afiliación a ARL (riesgos laborales) por localidad — el hallazgo más importante de esta sección

- **Qué se hizo:** un gráfico de barras horizontal, ordenado de menor a mayor, del porcentaje de
  recicladores con afiliación a ARL (el seguro de accidentes/riesgos laborales — el indicador más
  directo de si alguien tiene un trabajo formal) en cada una de las 18 localidades con datos.
- **Qué dio:** **14 de 18 localidades tienen 0% de afiliación a ARL**, y el máximo observado es
  14.3% (en una localidad con muestra muy pequeña, solo 7 recicladores).
- **Qué significa:** aunque el 89.9% de recicladores están "Activos" en el registro oficial (RURO),
  eso **no significa que tengan protección laboral real** — son dos cosas completamente distintas
  que antes se estaban tratando, implícitamente, como si fueran una sola. "Estar registrado" ≠
  "estar formalizado laboralmente".
- **Cómo se usa:** este matiz cambia cómo se debe modelar a los recicladores en el ABM —en vez de
  un solo número de "formalización", se deben representar dos cosas distintas: si están
  registrados oficialmente (~90%, alto) y si tienen protección laboral real (~0-14%, casi nulo).

### 4.4 Sección 4 y 5 del EDA — Gobernanza e incentivos económicos

#### Análisis 13: quejas (PQRS) de aseo por localidad, comparando 2020 y diciembre 2022

- **Qué se hizo:** un **gráfico de pendiente** (dos columnas de tiempo conectadas por una línea
  por cada localidad — se sigue la línea con la vista para ver si sube o baja), después de
  corregir un error de interpretación de los datos (cada archivo traía **59 meses acumulados**,
  no un solo mes — se corrigió tomando solo el mes más reciente de cada archivo).
- **Qué dio:** todas las localidades muestran una caída en el número de PQRS de 2020 a diciembre
  de 2022.
- **Qué significa:** hay que ser cauteloso al interpretar esto — 2020-2021 fue el período de
  aislamiento por la pandemia de COVID-19, que pudo afectar tanto la generación de residuos como
  la forma de reportar quejas, así que esta caída podría reflejar un efecto pandémico temporal,
  no necesariamente una mejora real y sostenida del servicio.
- **Cómo se usa:** como el único proxy cuantitativo disponible de gobernanza institucional, con la
  advertencia explícita de esta limitación de interpretación.

#### Análisis 14: mapa del factor de incentivo económico por UPZ

- **Qué se hizo:** se combinó la tabla real de tarifas (con el porcentaje de subsidio o
  contribución de cada estrato) con la composición real de estratos de cada UPZ, para calcular un
  "factor de incentivo ponderado" por zona, y se pintó en un mapa con colores divergentes (azul =
  subsidiado, rojo = paga de más).
- **Qué dio:** las zonas del norte y noreste de la ciudad (estratos altos) aparecen en rojo
  (contribuyen más de lo que reciben); las del sur (estratos bajos) en azul (reciben más subsidio
  del que pagan) — un patrón que coincide con la geografía socioeconómica real conocida de
  Bogotá.
- **Qué significa:** confirma que el sistema de tarifas sí redistribuye recursos de forma
  significativa entre zonas de la ciudad, y que ese patrón es geográficamente coherente con lo
  que ya se sabe de Bogotá — una señal de que el cálculo tiene sentido.
- **Cómo se usa:** es un mecanismo económico completamente nuevo que se puede incorporar al
  modelo de agentes — antes el ABM no tenía ningún dato económico real.

### 4.5 Sección 6 del EDA — Interacciones entre actores

#### Análisis 15: recicladores vs. % de separación, por localidad

- **Qué se hizo:** un gráfico de dispersión (cada punto es una localidad, su posición horizontal
  es el número de recicladores y la vertical el % de separación, y el tamaño del punto representa
  cuántos grandes generadores de basura hay).
- **Qué dio:** una correlación de Spearman muy débil y **no significativa** (r=-0.14, p=0.548).
- **Qué significa:** contrario a lo que se podría suponer intuitivamente, **no hay evidencia de
  que más recicladores en una localidad se relacione con mayor separación de residuos** — son
  fenómenos que, a nivel de localidad, parecen ser prácticamente independientes entre sí en los
  datos disponibles.
- **Cómo se usa:** es un hallazgo honesto y valioso — evita que el modelo asuma una relación
  causal entre recicladores y separación que los datos no respaldan.

#### Análisis 16: correlación entre variables de distintas categorías

- **Qué se hizo:** un **mapa de calor de correlación** (una tabla donde cada celda se pinta según
  qué tan relacionadas están dos variables entre sí, azul o rojo según si suben juntas o al
  revés) entre estrato, densidad poblacional, separación, calidad de separación, número de
  recicladores, y fragmentación social.
- **Qué dio:** estrato y separación están relacionadas positivamente (r≈0.28 a nivel UPZ); estrato
  y número de recicladores están relacionadas negativamente (r≈-0.23 — las UPZ de estrato más
  alto tienden a tener menos recicladores).
- **Qué significa:** confirma que los recicladores se concentran más en zonas de estrato más
  bajo — coherente con el conocimiento general del oficio de reciclaje en Colombia.
- **Cómo se usa:** ayuda a decidir qué variables de control incluir juntas en el modelo, sabiendo
  cuáles ya están relacionadas entre sí (para no "contar dos veces" el mismo efecto).

### 4.6 Sección 8 del EDA — El análisis multivariado con la Encuesta Multipropósito

Esta es la sección más importante de todo el EDA para decidir qué variables debe tener el modelo
de agentes — se explica en detalle aparte porque usa una técnica más avanzada.

#### ¿Qué es una "regresión logística" y por qué es mejor que mirar variable por variable?

Imagina que quieres saber si el estrato influye en la separación. Si solo miras estrato y
separación juntos, puede que el "efecto" del estrato en realidad esté siendo causado, en parte,
por otra cosa que va junto con el estrato — por ejemplo, la educación también sube con el
estrato, así que un efecto que parece ser "del estrato" podría en realidad ser "de la educación"
que casualmente viaja junto con el estrato.

Una **regresión logística** es una técnica estadística que estima el efecto de **cada variable
al mismo tiempo que las demás**, aislando el efecto propio de cada una. El resultado para cada
variable es un **odds ratio** (razón de momios — ver glosario), que dice cuánto cambian las
probabilidades del resultado (separar o no) por cada unidad que sube esa variable, **mientras
todas las demás se mantienen fijas**.

#### Qué se hizo, exactamente

Se usaron 234,043 hogares de la Encuesta Multipropósito 2021 (mucho más grande que la ECA), con
8 variables al mismo tiempo: estrato, educación, ingreso, informalidad laboral, personas por
hogar, tipo de vivienda (como indicador de tenencia), y participación en 2 tipos de
organizaciones (ambiental y Junta de Acción Comunal). Se ajustó **con y sin** el factor de
expansión `FEX_C`, para comparar.

#### Qué dio (resultado final, ponderado, el correcto para citar)

| Variable | Odds ratio | ¿Qué significa este número? |
|---|---|---|
| Participación en Junta de Acción Comunal | **2.63** | Participar en la JAC más que duplica las probabilidades de separar, controlando por todo lo demás |
| Participación en organización ambiental | **2.33** | Participar en una organización ambiental más que duplica las probabilidades también |
| Vivienda propia | 1.40 | Ser dueño de la vivienda (vs. arrendarla) aumenta 40% las probabilidades |
| Estrato | 1.37 | Cada estrato adicional aumenta 37% las probabilidades |
| Personas por hogar | 1.13 | Cada persona adicional en el hogar aumenta 13% las probabilidades |
| Educación | 1.13 | Cada nivel educativo adicional aumenta 13% las probabilidades |
| Informalidad laboral | 0.85 | Tener un empleo informal REDUCE 15% las probabilidades |
| Ingreso (ajustado) | 1.00 | **Sin efecto real** una vez controlado por lo demás (no significativo, p=0.33) |

#### Qué significa todo esto, en conjunto

El hallazgo más importante: **la participación comunitaria pesa más que el estrato o la
educación**. Esto sugiere que estar conectado con la comunidad (a través de organizaciones
vecinales o ambientales) es, según estos datos, un factor tan o más fuerte que la condición
socioeconómica para explicar quién separa residuos. Y el ingreso, por sí solo, **no aporta nada
extra** una vez ya se sabe el estrato, la educación y si el trabajo es formal — es decir, no es
"tener más plata" lo que hace la diferencia, sino la combinación de condición estructural más
integración social.

#### Cómo se usa esto en el modelo de agentes

Es la justificación más sólida de todo el EDA para agregar `participacion_comunitaria` como un
atributo real del `HogarAgente` del modelo — con más respaldo estadístico que varios de los
parámetros que el modelo ya tenía desde antes.

---

## 5. Síntesis final: qué sabemos con certeza vs. qué sigue siendo un supuesto

> **Actualización (ronda de ajustes tras esta auditoría):** se corrigió una categoría de RURO
> duplicada por espacios/mayúsculas (ver §3.3 y la nota técnica más abajo), se reejecutó TODA la
> Fase 1 con ese fix, y se amplió la regresión de EM2021 de 8 a 13 variables — agregando las que
> quedaban "extraídas pero sin analizar". Los hallazgos nuevos están incorporados en esta lista.

### Lo que ahora se sabe con evidencia real y sólida:

- El estrato influye en la separación (dos pruebas distintas lo confirman: chi² en ECA, y
  regresión en EM2021).
- La participación comunitaria es el factor más fuerte de todos los medidos.
- La informalidad laboral reduce la separación.
- El ingreso, por sí solo, no tiene efecto adicional una vez se controla por lo demás — se
  confirmó de nuevo en el modelo ampliado (odds ratio prácticamente 1.00): es un hallazgo estable,
  no un accidente del primer modelo.
- La edad tiene un efecto positivo pequeño pero real (encontrado en esta ronda, ECA 2021).
- Vivir en conjunto residencial aumenta la probabilidad de separar (posible efecto de reglas u
  organización comunitaria propias de los conjuntos).
- Vivir cerca de un basurero/botadero **reduce** la probabilidad de separar — es la primera
  evidencia real a favor del mecanismo de "entorno degradado desmotiva" de la hipótesis original.
- Sentirse pobre (más allá del estrato objetivo) también reduce, un poco, la probabilidad de
  separar — la percepción subjetiva aporta información propia.
- **Hallazgo con matiz, no confirmación limpia:** vivir en un entorno con "disposición
  inadecuada de basuras" en general (una pregunta distinta a "cerca de un basurero") se asoció
  con MÁS separación, no menos — contrario a lo esperado. No se fuerza una sola narrativa cuando
  dos variables del mismo mecanismo apuntan en direcciones distintas.
- Solo 1.41% de los hogares de Bogotá no usa el servicio formal de recolección — de ese grupo
  pequeño, enterrar la basura es la forma más común, seguida de quemarla.
- La infraestructura (puntos críticos) varía fuerte entre zonas y de forma persistente en el
  tiempo — no es uniforme.
- Los recicladores están registrados oficialmente en su mayoría (90%), pero casi ninguno tiene
  protección laboral real (0-14%).
- La recolección formal tiene capacidad estable, sin señales de saturación en 8 años de datos.

### Corrección de limpieza aplicada en esta ronda:

- **RURO — categorías de "Nivel Educativo" y "Medio de Recolección" duplicadas por
  espacios/mayúsculas** (ej. "PRIMARIA" se contaba 3 veces por separado) — corregido con
  normalización de texto (`strip()` + mayúsculas), verificado que colapsa las categorías sin
  perder ninguna real. Se reejecutó toda la Fase 1 con este fix — `data/processed/` quedó
  regenerado. Efecto encontrado: la moda de "medio de recolección" por localidad sigue siendo
  mayoritariamente "SIN INFORMACIÓN" (19 de 20 localidades) — un hallazgo honesto de que esta
  variable derivada, tal como está construida hoy, aporta poca información útil (la categoría
  "sin dato" domina), no un error de cálculo.

### Lo que sigue siendo un supuesto o un hueco real (documentado, no escondido):

- Los parámetros de qué tan rápido cambia la actitud de un hogar hacia la separación (no hay
  ningún dato que siga a las mismas personas en el tiempo para medir esto).
- La capacidad de recolección individual de un reciclador (nadie mide esto en ninguna fuente
  disponible).
- El efecto real del incentivo económico sobre el comportamiento (existe el dato de la tarifa,
  pero no hay evidencia todavía de que cambie el comportamiento — es una hipótesis a probar con
  el modelo, no un hecho confirmado).
- La relación entre recicladores y separación resultó, sorprendentemente, sin evidencia
  significativa — no se debe asumir un vínculo directo entre ambos.
- Todo lo relacionado con camiones individuales, rutas óptimas, y capacidad remanente del
  Relleno Doña Juana — sin ninguna fuente de datos disponible.

---

## 6. Glosario de términos técnicos (en orden de aparición en este documento)

- **UPZ (Unidad de Planeamiento Zonal):** división geográfica oficial de Bogotá, más chica que
  una localidad. Bogotá tiene 112.
- **Localidad:** la división administrativa más grande de Bogotá (como un "distrito"). Bogotá
  tiene 20 (ej. Chapinero, Kennedy, Suba).
- **Manzana (catastral):** la unidad geográfica más pequeña usada en este proyecto — básicamente
  una cuadra de la ciudad.
- **Estrato:** clasificación oficial colombiana de 0 a 6 del nivel socioeconómico de una
  vivienda, usada para subsidios de servicios públicos.
- **Factor de expansión / ponderador:** número que indica a cuántas personas/hogares reales
  representa una sola respuesta de encuesta, para que las estadísticas describan a la población
  real y no solo a la muestra encuestada.
- **Mapa coroplético:** un mapa donde cada zona se pinta de un color según el valor de una sola
  variable (más oscuro = valor más alto).
- **Mapa bivariado:** un mapa que combina 2 variables a la vez en una sola cuadrícula de colores
  (9 combinaciones posibles: alto-alto, alto-bajo, etc.).
- **Pequeños múltiplos:** varios mapas o gráficos pequeños, del mismo tipo, puestos uno al lado
  del otro (por ejemplo, uno por año) para comparar cómo cambia algo en el tiempo, todos con la
  misma escala de color para que la comparación sea justa.
- **Chi-cuadrado:** una prueba estadística que evalúa si la relación observada entre dos
  variables categóricas (ej. estrato y "separa sí/no") es lo bastante fuerte como para no ser
  solo casualidad de la muestra.
- **p-valor:** la probabilidad de observar un resultado tan fuerte como el que se vio, si en
  realidad no hubiera ninguna relación real entre las variables. Un p-valor bajo (convencionalmente
  menor a 0.05, o 5%) se interpreta como evidencia de que la relación sí es real.
- **Regresión logística:** técnica estadística que estima el efecto de varias variables al mismo
  tiempo sobre un resultado de sí/no, aislando el efecto propio de cada variable de los efectos
  de las demás.
- **Odds ratio (razón de momios):** el número que resulta de una regresión logística para cada
  variable — dice cuánto se multiplican las probabilidades del resultado por cada unidad que sube
  esa variable. Un odds ratio de 2 significa que las probabilidades se duplican; de 0.5, que se
  reducen a la mitad; de 1, que no hay ningún efecto.
- **Correlación (r de Spearman/Pearson):** un número entre -1 y 1 que mide qué tan relacionadas
  están dos variables numéricas — cercano a 1: suben juntas; cercano a -1: una sube cuando la otra
  baja; cercano a 0: no hay relación clara.
- **Coeficiente de variación:** una medida de qué tan dispersos están los valores de una variable
  entre distintas zonas — un número alto (mayor a 1) indica que hay mucha diferencia entre zonas;
  un número bajo indica que todas las zonas se parecen entre sí.
- **Listwise deletion (eliminación por lista):** cuando se hace un análisis con varias variables
  a la vez y a una persona le falta el dato de aunque sea una sola de ellas, esa persona se excluye
  por completo del análisis (para no inventar datos que no existen).
- **Encoding:** la "tabla de traducción" que usa un computador para convertir números binarios en
  letras — si se usa la tabla equivocada al leer un archivo, las tildes y eñes se convierten en
  símbolos sin sentido.

---

*Fin de la auditoría. Cualquier número o gráfico de este proyecto que no esté citado aquí debe
tratarse con la misma cautela que los "huecos" documentados en la sección 5 — no se debe asumir
que está validado si no aparece explícitamente en este documento.*
