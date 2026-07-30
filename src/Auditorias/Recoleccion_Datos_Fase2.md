# Fase 2 — Recolección de Datos Externos y Activación de Recursos Locales
### Cierre de fase: qué se trajo, qué se activó, qué sigue sin existir
**Autores:** Manuel Alejandro González Gallego, Gloria Inés Robledo Ulloa — CUN
**Fecha de ejecución:** 2026-07-09/10
**Documento base:** `Analisis_Variables_Negocio.md` (inventario de variables previo a esta fase)
**Estado: cerrada.** Verificación end-to-end de todo el código nuevo/modificado corrida sin
errores el 2026-07-10 (loaders activados, RBL consolidado, `em2021` ampliado, rutas de Fase 2,
exportación a `data/processed/`).

> Esta fase tenía dos objetivos explícitos del usuario: (1) auditar a fondo toda la data cruda ya
> recolectada, y (2) investigar y traer las fuentes externas que hagan falta para responder la
> pregunta de investigación y cumplir los 4 objetivos del proyecto de grado. Por instrucción
> explícita, la categoría de "incentivos económicos" **excluye deliberadamente** las condiciones
> de mercado de materiales reciclables — ese tema queda reservado para un análisis propio,
> posterior, sobre la dinámica entre actores.

---

## 1. Las 6 categorías vigentes en esta fase

1. Nivel de separación en la fuente y calidad de la separación
2. Estructura y eficiencia de la recolección y la logística
3. Capacidad y formalización de los recicladores de oficio
4. Gobernanza institucional y coordinación intersectorial
5. **Incentivos económicos** (sin condiciones de mercado de reciclables — excluido a propósito)
6. Factores socio-demográficos y territoriales (estrato, densidad, hábitos)

---

## 2. Auditoría de `data/raw/`: lo que ya teníamos y nunca se usó

Antes de salir a buscar nada externo, se auditó exhaustivamente cada archivo ya presente en
`data/raw/` (2 agentes de exploración de solo lectura, cruzados contra `src/carga_datos.py` y
`src/config.py`). Hallazgos que cambian el diagnóstico de "no tenemos el dato" a "lo tenemos,
nadie lo conecta":

| Recurso | Categoría | Estado encontrado |
|---|---|---|
| Carpeta RBL (`Residuos/datos-residuos-recogidos-rbl-2017-2025 (1)/`, 97 archivos, 2017-2026) | 2 | Nunca consolidada — sin ningún loader |
| `cargar_recoleccion_concesionario()` | 2 | Función escrita, **cero invocaciones** en ningún notebook |
| `cargar_puntos_limpios()` | 2 | Función escrita, **cero invocaciones** |
| `cargar_cantidad_entregada_ases()` | 2 | Función escrita, **cero invocaciones** |
| Microdatos crudos ECA 2021 (`2021-04-22-base-datos-abiertos_eca-2021_scrd-1.xlsx`, hoja `NUM`, ~2,282 encuestas individuales) | 1 | Solo se usa el agregado de 20 filas por localidad; el crudo individual (razones de no separar, qué materiales separa cada quién) nunca se lee |
| Columnas de `em2021.csv` no incluidas en `COLUMNAS_MULTIPROPOSITO` | 1, 6 | `NVCBP11D`, `NVCBP14B`, `NVCBP14I`, `NVCBP15F`, `NVCBP15K`, `NHCCP37` — confirmadas en el diccionario oficial, nunca extraídas |
| `Grandes_Generadores__de_Residuos_-_UAESP...csv` (7,456 puntos geolocalizados) | 2 | Cargado pero nunca usado como proxy de infraestructura |
| `Superservicios_Residuos_Generados...csv` | 2 | Dataset **nacional** (192 municipios); solo 42/2,760 filas son de Bogotá — usarlo sin filtrar mezclaría otras ciudades |

---

## 3. Fuentes externas: qué se buscó, qué se encontró, qué se descartó

Todas las fuentes se verificaron primero por `WebFetch` directo a la página del dataset antes de
descargar — son portales oficiales (`datosabiertos.bogota.gov.co`, `cra.gov.co`, `uaesp.gov.co`),
licencia CC BY-SA 4.0 o equivalente de dominio público.

### 3.1 SIGAB (UAESP) — Sistema de Información para la Gestión de Aseo de Bogotá

**Categoría 2 y 4.** `datosabiertos.bogota.gov.co/dataset/sigab-uaesp`. Se descargó el ZIP
consolidado `sigab-2020-2025.zip` (128.6 MB, 629 entradas) más el snapshot independiente
`sigab-junio-2026.zip` (2.3 MB). De ahí se extrajeron **4 snapshots representativos** repartidos
en el tiempo (decisión ya validada con el usuario: varios cortes, no uno solo ni la serie
mensual completa): **2020, diciembre-2022, diciembre-2024, junio-2026**. Cada snapshot trae:
`cestas.csv`, `contenedores.csv`, `grandes-generadores.csv`, `objetos-lavados.csv`,
`pqrsxlocalidad.csv`, `pqrsxestrato.csv`, `pqrsxconcesionario.csv`, `pqrsxasextiposdqs.csv`,
`ptoscriticos.csv` (puntos críticos, pipe-delimitado, con coordenadas).

**Hallazgo de calidad (nuevo, verificado archivo por archivo):** los 5 archivos de PQRS del
snapshot **diciembre-2024 están vacíos** (1 byte cada uno — un `\x00` sin contenido real),
mientras que `puntoscriticos.csv` sí trae datos completos ese mismo mes. De forma simétrica,
`SIGAB_CONTENEDORES.csv` del snapshot **junio-2026 también está vacío** (1 byte) mientras el
resto de archivos de ese mes sí tienen datos. Esto es un problema de la fuente oficial (UAESP),
no de la descarga — **los snapshots de 2020 y diciembre-2022 son los únicos de los 4 con PQRS
completo**; diciembre-2024 y junio-2026 solo aportan puntos críticos/contenedores/generadores.

### 3.2 Macrorutas de Recolección y de Barrido (UAESP)

**Categoría 2.** `datosabiertos.bogota.gov.co/dataset/macrorutas-de-recoleccion-bogota-d-c` y
`...macrorutas-de-barrido-bogota-d-c`. Se descargaron en GeoJSON (formato más simple que
Shapefile/GPKG para lectura directa con geopandas). **125 zonas de recolección** y **179 zonas de
barrido**, vigencia 2025, con horario de inicio/fin y frecuencia (ej. "Lunes a Sábado") por
localidad — la estructura operativa real de la recolección, algo que ni RBL ni ningún archivo
previo tenía (RBL solo da toneladas agregadas por operador, sin estructura espacial ni horaria).

### 3.3 RURO "Generalidades" — versión oficial del portal (distinta al CSV que ya teníamos)

**Categoría 3.** Se descargaron dos datasets adicionales a `informacion-ruro-.csv` (que ya
teníamos, 24,196 registros individuales con género/edad/localidad/medio de recolección):

- **`RURO_2012-2021.xlsx`** (`datosabiertos.bogota.gov.co/dataset/generalidades-del-registro-unico-recicladores-de-oficio-ruro-2012-2021`):
  no es un listado individual, es un resumen con series y tablas que **ninguna otra fuente ya
  tenía**: conteo de registros por año (2012-2021), **causas de retiro del registro** (fallecido,
  cédula no encontrada, duplicado, etc.), **discapacidad por tipo** (motriz, auditiva, visual,
  cognitiva...), y — el hallazgo más valioso — **Estado en el RURO: Activo (24,895) vs. Retirado
  (2,785)**, el primer indicador real de formalización/vigencia que existe en todo el proyecto.
- **RURO 2022 por localidad** (18 archivos, uno por localidad, 339 filas agrupadas en total,
  `datosabiertos.bogota.gov.co/dataset/generalidades-del-registro-unico-recicladores-de-oficio-ruro-ano-2022`):
  trae variables que **ninguna fuente anterior tenía para recicladores**: `Estado En Ruro`
  (Activo/Retirado), `Tipo de Vivienda` (arrendada/propia), `Salud` (tipo de afiliación:
  subsidiado/contributivo — proxy directo de informalidad), `#ARL` (afiliación a riesgos
  laborales — indicador directo de formalización), `#Cabeza_Hogar`, `#Analfabetas`, `#HabCalle`,
  `#Pensionados`, y el medio de transporte usado (propio/comunal/prestado). Esto convierte la
  categoría 3 de "delgada" (solo conteo y edad) a **con variables reales de formalización**, algo
  que `Diseno_ABM.md` señalaba explícitamente como no disponible.

### 3.4 Gobernanza institucional (categoría 4) — el hueco más difícil, con un hallazgo negativo importante

Se buscó específicamente un proxy cuantitativo de coordinación/respuesta institucional. El
dataset genérico **"Consolidado PQRS"** de Bogotá (`datosabiertos.bogota.gov.co/en/dataset/consolidado-pqrs`)
se descargó (`consolidado_pqrs_2018.csv`, 15,558 filas, 2013-2018) y **se verificó a fondo antes
de darlo por útil**: sus 21 categorías de "Criterio (Tipificación)" son **enteramente del IDU**
(Instituto de Desarrollo Urbano — obras viales, huecos, mantenimiento de malla vial), no de aseo
ni de UAESP. **Se descarta explícitamente como fuente de gobernanza de residuos** — queda el
archivo descargado por transparencia de lo que se revisó, pero no se usa.

El proxy real que sí sirve para esta categoría son los archivos **`pqrsxlocalidad.csv`,
`pqrsxestrato.csv`, `pqrsxconcesionario.csv`** dentro de los snapshots de SIGAB (sección 3.1) —
esos sí son PQRS específicas de aseo, por localidad/estrato/concesionario, que es exactamente lo
que se buscaba.

Adicionalmente se descargó el **PGIRS — Documento Técnico de Soporte** (UAESP,
`uaesp.gov.co/images/pgirs_mesas/DOCUMENTO TECNICO SOPORTE - DTS.pdf`, 8.3 MB): es el marco
normativo/institucional oficial de la gestión de residuos en Bogotá (enfoques de economía
circular, cultura ciudadana, ordenamiento territorial) — **contexto citable, no una variable
cuantitativa**. Sirve para fundamentar el marco de gobernanza en el texto de la tesis, no para
alimentar el ABM directamente.

### 3.5 Incentivos económicos (categoría 5 — sin condiciones de mercado de reciclables)

Se encontró y descargó un documento con **valores reales, vigentes y a nivel de estrato**, algo
que antes solo existía como un escalar agregado anual de ciudad (`03_reglas_negocio.csv`):

**`Tarifas_ASE3_202512.pdf`** (Ciudad Limpia Bogotá S.A. E.S.P., contrato UAESP No. 285 de 2018,
periodo diciembre 2025) trae:
- **VIAT (Valor del Incentivo al Aprovechamiento y Tratamiento de Residuos Sólidos) = $11,388.00/tonelada** — el número que `Diseno_ABM.md` no tenía.
- **Factor de subsidio/contribución por estrato**: Estrato 1 = -70%, Estrato 2 = -40%, Estrato 3 = -15%, Estrato 4 = 0% (no subsidia ni paga sobretasa), Estrato 5 = +50%, Estrato 6 = +60% — coincide con los topes normativos de la CRA (70%/40%/15% máximo para estratos 1/2/3) encontrados por separado en la investigación web (`cra.gov.co`).
- Costos de referencia completos (CBL, CLUS, CRT, CDF, CCS, CTL, VBA) y tarifa final por tipo de productor (residencial por estrato, pequeño/gran productor comercial/industrial/oficial).

Esto es **específico del ASE 3** (localidades 8 y 9); la estructura de factores por estrato es
normativa (CRA) y aplica a los 5 ASE por igual, pero los valores exactos de costos de referencia
sí varían por concesionario — se documenta esta limitación de alcance explícitamente.

### 3.6 Segundo corte temporal para cultura ambiental (categoría 6) — confirmado NO disponible como dataset abierto

Se buscó la Encuesta Bienal de Culturas (EBC) 2023/2025 como segundo punto en el tiempo para el
índice de "cultura ambiental" (hoy solo existe el corte único de ECA 2021). Los resultados
existen y se publican en prensa/informes (38.4% de hogares separa en 2025, índice de cultura
ambiental bajó de 0.40 a 0.38, con caídas marcadas en Tunjuelito, Bosa y Barrios Unidos), pero
tras una verificación exhaustiva en esta sesión de cierre:

- Se consultó directamente la **API de búsqueda de Datos Abiertos Bogotá**
  (`api/3/action/package_search`) con los términos "cultura ciudadana", "bienal", "culturas",
  "observatorio culturas" y "cultura ambiental" — **el único resultado relacionado en las cuatro
  búsquedas es `eca2021`**, el mismo dataset que ya se tenía desde la Fase 1. No existe ningún
  otro dataset de la EBC publicado en ese portal.
- Se revisó directamente el sitio de **Cultura Ciudadana** (`culturaciudadana.gov.co/sistema-de-informacion-de-cultura-ciudadana`)
  y el **Observatorio de Cultura** (`observatoriocultura.github.io`) — ninguno de los dos expone
  un enlace de descarga de microdatos/base de datos; solo visualizaciones interactivas de
  resultados agregados.

**Conclusión: la EBC 2023/2025 no está disponible como dataset abierto descargable** con los
medios de búsqueda usados en este proyecto — a diferencia de las demás fuentes de este
documento, no se pudo traer. La única vía para conseguirla sería una solicitud directa a la
Secretaría Distrital de Cultura, Recreación y Deporte (Dirección de Observatorio y Gestión del
Conocimiento), fuera del alcance de lo que se puede automatizar en esta fase.

### 3.7 Explícitamente fuera de esta búsqueda

Por instrucción directa del usuario: ninguna fuente de precios de materiales reciclables,
márgenes de bodegas/intermediarios, ni condiciones de mercado del reciclaje se buscó ni se trajo
en esta fase.

---

## 4. Activación de recursos locales (código nuevo en esta fase)

Además de traer datos nuevos, se conectó lo que ya existía pero nunca se ejecutaba:

- **`cargar_recoleccion_concesionario()`, `cargar_puntos_limpios()`, `cargar_cantidad_entregada_ases()`**:
  ahora se invocan desde el notebook de EDA (nueva Sección 17) y exportan a
  `data/processed/12_recoleccion_concesionario.csv`, `13_puntos_limpios.csv`,
  `14_cantidad_entregada_ases.csv`. No se modificó su lógica de lectura original.
- **`cargar_rbl_consolidado()`** (función nueva en `src/carga_datos.py`): consolida los 97
  archivos de la carpeta RBL (2017-2026) en una sola serie larga
  (`año, mes, esquema, operador, tipo_residuo, toneladas, archivo_origen`), exportada a
  `data/processed/15_rbl_consolidado.csv`. **Resultado probado: 2,240 filas, los 10 años
  completos (2017-2026), 7 tipos de residuo, 5 ASE + RPC Aguas de Bogotá (2018+) más 6 operadores
  del esquema de "zonas" de 2017** (sin duplicados por espacios/mayúsculas/tildes). Decisiones de
  limpieza documentadas en el propio código: exclusión de 5 archivos duplicados/parciales de
  2018, dos formatos numéricos (europeo 2017-2020 / nativo 2021+), y **no existe ningún archivo
  de equivalencia zona-2017→ASE-2018+ en la carpeta fuente** — se confirmó revisando el único
  candidato plausible (`data-set-rbl_nuevo_esquema_aseo.csv`, que resultó ser un corte parcial de
  12 días de febrero 2018, no una tabla de mapeo) — la serie comparable año a año empieza en
  2018, y 2017 queda marcado con `esquema="zonas_2017"` para quien quiera usarlo por separado.
- **`COLUMNAS_MULTIPROPOSITO`** se amplió de 16 a 40 columnas (probado contra `em2021.csv` real:
  234,043 filas de Bogotá tras el filtro, sin errores). Se agregaron las columnas que el
  `select()` original de PySpark ya nombraba (ingresos, educación, informalidad, participación
  comunitaria, percepción ambiental adicional, condiciones habitacionales) más las 6 confirmadas
  en esta fase (`NVCBP11D`, `NVCBP14B`, `NVCBP14I`, `NVCBP15F`, `NVCBP15K`, `NHCCP37`).
- **`src/config.py`**: se agregó el diccionario `ARCHIVOS_FASE2` con las rutas locales de todo lo
  descargado en la sección 3 — **son solo rutas, ningún loader las usa todavía**.

Todas las rutas de `data/raw/externo_fase2/` se verificaron existentes tras la descarga y cada
archivo se abrió y se inspeccionó su estructura real (no se dio nada por bueno solo por
descargarse) — ver el detalle de columnas, filas y hallazgos de calidad en las secciones 3.1-3.6.

---

## 4bis. Limpieza y verificación de cierre (sesión 2026-07-10)

### Documentación de tipo/naturaleza de las 24 columnas nuevas de `em2021.csv`

Se agregó `carga_datos.NATURALEZA_COLUMNAS_MULTIPROPOSITO_FASE2`, un diccionario que clasifica
cada una de las 24 columnas agregadas a `COLUMNAS_MULTIPROPOSITO` (numérica, categórica
binaria Sí/No, ordinal, o multi-opción), verificado contra el diccionario oficial DANE. Esto es
**documentación de tipo, no una decisión de qué variables usar en el modelo** — esa decisión
(cómo recodificar, cuáles fusionar a `df_modelo`) sigue siendo una decisión de modelado
pendiente, no algo que se pueda resolver "limpiando" sin definir primero el uso.

**Hallazgo de calidad puntual:** `NPCKP44A` está presente en `em2021.csv` y era nombrada en el
`select()` original de PySpark, pero **no aparece documentada en el diccionario oficial
`20230620_diccionario_variables_encuesta_em2021.xlsx`** — se conserva en la lista (por
continuidad con el alcance original) pero queda marcada explícitamente como de definición no
verificada.

### Verificación de encoding de los archivos de la Parte B (no había corrupción real)

Se investigó si los caracteres ilegibles vistos en las inspecciones anteriores (ej. "Recolecci�n"
en las macrorutas, "Ciudad L�mpia" en SIGAB) eran corrupción real de los archivos descargados.
**Verificado a nivel de bytes: no lo son.** Son dos encodings distintos y ambos correctos en su
propio archivo:
- `macrorutas_barrido.geojson`: UTF-8 real (`\xc3\xb3` = "ó" correctamente codificado).
- `sigab_puntoscriticos.csv`: latin-1 real (`\xed` = "í" correctamente codificado en un solo byte).

Los caracteres ilegibles eran únicamente un problema de **la consola de Windows al imprimir**
(cp1252), no de los archivos en disco. No hizo falta corregir ni re-guardar ningún archivo de la
Parte B — quedan tal como se descargaron, con la única precaución de que quien los lea debe usar
el encoding correcto según el archivo (documentado en cada sub-sección de la Parte 3).

### Verificación end-to-end final

Se corrió una verificación consolidada de todo el código nuevo/modificado en esta fase (los 4
loaders activados, `cargar_multiproposito()` ampliado, las 11 rutas de `ARCHIVOS_FASE2`, y la
exportación completa a `data/processed/`) — **sin errores**:

```
loaders activados OK: (6, 3) (8, 5) (6, 4)
RBL consolidado OK: (2240, 7) - años: [2017..2026] completos
em2021 ampliado OK: (234043, 40)
ARCHIVOS_FASE2 OK: las 11 rutas existen
Exportación OK: 12_recoleccion_concesionario.csv, 13_puntos_limpios.csv,
                14_cantidad_entregada_ases.csv, 15_rbl_consolidado.csv
```

---

## 5. Inventario de variables actualizado (6 categorías)

| Categoría | Antes de esta fase | Después de esta fase |
|---|---|---|
| 1. Separación en la fuente y calidad | Solo agregado por localidad | + microdatos crudos ECA2021 identificados (pendientes de cargar) y 6 columnas nuevas de `em2021.csv` ya extraídas |
| 2. Recolección y logística | Nada a nivel de agente, solo un escalar de infraestructura sintético | + RBL consolidado (2,240 filas, 10 años), + 4 snapshots SIGAB (puntos críticos, contenedores, generadores), + macrorutas reales (125 zonas de recolección, 179 de barrido, con horario/frecuencia) |
| 3. Recicladores | Solo conteo y edad promedio por localidad | + Estado Activo/Retirado (formalización), + afiliación ARL, + tipo de salud/vivienda, + causas de retiro, + discapacidad |
| 4. Gobernanza institucional | Inexistente | + PQRS de aseo por localidad/estrato/concesionario (SIGAB, 2020 y dic-2022 completos), + PGIRS como marco normativo citable. **Se descartó explícitamente** el "Consolidado PQRS" genérico (es de IDU, no de aseo) |
| 5. Incentivos económicos | Solo `RN001-RN009` agregados anuales de ciudad | + VIAT real ($11,388/ton), + factor de subsidio/contribución real por estrato, + costos de referencia completos (ASE 3, dic-2025) |
| 6. Socio-demográfico y territorial | Ya bien cubierto (DANE, manzanas, estratificación) | Sin cambios; se buscó un segundo corte temporal (EBC 2023/2025) pero no se logró descargar en esta fase |

---

## 6. Lo que sigue siendo un hueco real (honesto, no se resolvió)

- **Ingreso individual de recicladores de oficio**: ninguna fuente, ni interna ni externa, lo
  trae — ni siquiera el RURO oficial.
- **Capacidad real de camión / viajes por día**: ninguna fuente, interna ni externa, la tiene.
- **Coordinación intersectorial cuantificada** más allá del proxy de PQRS por concesionario: no
  existe una métrica directa de "qué tan bien coordinan las entidades entre sí".
- **Segundo corte temporal de cultura ambiental** (EBC 2023/2025): **confirmado que no está
  disponible como dataset abierto descargable** (ver §3.6) — existe como resultado publicado,
  no como microdato accesible; conseguirlo requeriría solicitud directa a la entidad.
- **Condiciones de mercado de materiales reciclables**: excluido a propósito, no buscado.
- **Naturaleza de las 24 columnas nuevas de `em2021.csv`**: documentada por tipo (numérica,
  binaria, ordinal), pero **no recodificada ni fusionada a `df_modelo`** — hacerlo sin definir
  primero qué variables entran al modelo sería inventar una decisión de modelado. Queda como
  trabajo explícito de la fase de selección/integración de variables, no de esta fase de
  recolección y limpieza técnica.

---

*Fin de la Fase 2 — recolección y limpieza técnica cerradas y verificadas end-to-end
(2026-07-10). No se modificó el paquete `abm/`, y no se decidió qué variables nuevas entran al
modelo — esas decisiones y el siguiente paso quedan para el usuario.*
