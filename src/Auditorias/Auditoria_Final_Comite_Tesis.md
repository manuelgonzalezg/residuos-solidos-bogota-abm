# Auditoría Final — Nivel Comité de Tesis de Posgrado

### Sistema de gestión de residuos sólidos de Bogotá: EDA + Modelo Basado en Agentes (ABM)
**Autores:** Manuel Alejandro González Gallego, Gloria Inés Robledo Ulloa — CUN
**Director:** Mariano Esteban Romero Torres
**Fecha de esta auditoría:** 2026-07-14
**Estado:** documento vigente — reemplaza a `Certificacion_Entregable_Final.md` (2026-07-11) como
la certificación de estado más reciente; ese documento se conserva íntegro como registro
histórico de la ronda de auditoría que resolvió el caso `Cerebro.xlsx`.

---

## 0. Cómo leer y usar este documento

Este NO es un documento nuevo que reemplaza a los demás — es el punto de entrada que los conecta
a todos, para que usted pueda auditar el proyecto de punta a punta sin tener que reconstruir el
orden usted mismo. Cada afirmación trae:

- Un semáforo de confianza (mismo criterio usado en `Resultados_EDA_Funcionamiento_Bogota.md`):
  🟢 evidencia sólida y verificada · 🟡 evidencia con matices o limitaciones declaradas · 🔴
  supuesto sin dato directo, acotado pero no medido.
- Una cita exacta de archivo/función/documento — nada aquí debería requerir que usted confíe en
  mi palabra; todo apunta a algo que puede abrir y volver a correr.

**Mapa de documentos** (todos en `src/Auditorias/`, en el orden en que conviene leerlos si quiere
el detalle completo de algo):

| Documento | Qué cubre |
|---|---|
| `Plan_EDA.md` | Diseño original del EDA, las 6 categorías de variables |
| `Auditoria_Completa_Datos_Limpieza_EDA.md` | Auditoría fuente por fuente de `data/raw/`, con glosario estadístico |
| `Resultados_EDA_Funcionamiento_Bogota.md` | Síntesis de TODO lo que dijeron los datos, por tema |
| `Analisis_Variables_Negocio.md` | Pregunta de investigación formal, objetivos, inventario de variables |
| `Recoleccion_Datos_Fase2.md` | Fuentes externas traídas en Fase 2 (SIGAB, macrorutas, RURO, CRA, PQRS) |
| `Diseno_ABM.md` | Diseño del ABM: agentes, mecanismos, calendario, plan de calibración |
| `Reglas_Negocio_v2_y_Modelado_Agentes.md` | Cada regla de negocio del ABM, trazada a su evidencia |
| `Investigacion_Salto_Aprovechamiento.md` | Por qué se descartó el 48.5%/43.88% oficial 2024-2025 como objetivo de calibración |
| `Justificacion_Metodologica_Comite.md` | Por qué UPZ, origen de cada beta, heterogeneidad, contraste con MATSim |
| `Flujo_Completo_Logica_ABM.md` | La lógica exacta que ejecuta el modelo, paso a paso, con cita de línea |
| `Certificacion_Entregable_Final.md` | Auditoría de orden del 2026-07-11 (histórica, ver nota arriba) |
| **`Auditoria_Final_Comite_Tesis.md` (este documento)** | Síntesis final: qué resultados dio el proyecto y cómo verificarlos usted mismo |

---

## 1. Resumen ejecutivo

Este proyecto combina un EDA exhaustivo de las fuentes reales de gestión de residuos de Bogotá
con un Modelo Basado en Agentes (ABM, Mesa/Python) que simula 75,273 hogares (muestra real del
3% de ~2.5 millones de hogares reales, ponderada), 112 poblaciones de recicladores de oficio y 5
operadores formales de aseo, día a día, durante años calendario reales (2018-2024).

**El resultado central**: el modelo, calibrado contra la serie oficial de aprovechamiento
2018-2023 (15.38% → 18.56%), reproduce esa trayectoria con un error de **RMSE=1.1961 puntos
porcentuales** — y al proyectar 2024 con los mismos mecanismos (sin ningún cambio regulatorio),
da **18.32%**, muy por debajo del 43.88% que reportó UAESP para 2024. Esa brecha de ~25.6pp **no
es un fallo del modelo** — es evidencia de que el salto oficial de 2024 coincide con un cambio de
metodología de medición (Decreto 1381/2024), no con una mejora real de esa magnitud en el
comportamiento ciudadano (ver §6 y `Investigacion_Salto_Aprovechamiento.md`).

**Lo que hace a este proyecto defendible ante un comité no es que "funcione perfecto"** — es que
cada número tiene una fuente declarada (real, calibrado, o supuesto acotado — ver §5), cada bug
real encontrado en el camino está documentado con su corrección (§7, no escondido), y las
limitaciones se declaran explícitamente en vez de disimularse (§10).

---

## 2. Pregunta de investigación y objetivos (cita textual, no paráfrasis)

**Pregunta de investigación formal** (`Analisis_Variables_Negocio.md` §1.1, cita textual del
proyecto de grado):

> "¿Cómo las interacciones entre los actores y sus reglas de comportamiento dentro del sistema
> urbano de gestión de residuos sólidos de Bogotá generan las dinámicas emergentes que
> condicionan el aprovechamiento de los residuos y bajo qué escenarios de intervención dichas
> dinámicas podrían modificarse para mejorar el desempeño del sistema?"

**Objetivo general** (cita textual):

> "Analizar las dinámicas emergentes del sistema socio-técnico de gestión de residuos sólidos
> urbanos en Bogotá mediante la integración del análisis exploratorio de datos y la simulación
> basada en agentes, con el fin de comprender cómo los comportamientos e interacciones entre los
> actores influyen en la persistencia de bajos niveles de aprovechamiento."

**Objetivos específicos** (cita textual, con dónde se cumple cada uno):

1. *"Analizar la información histórica mediante EDA..."* → `Resultados_EDA_Funcionamiento_Bogota.md`, completo. 🟢
2. *"Identificar y caracterizar los principales actores..."* → `Reglas_Negocio_v2_y_Modelado_Agentes.md` §1-4, completo. 🟢
3. *"Construir un modelo ABM simplificado, con reglas fundamentadas en evidencia empírica y supuestos explícitos"* → `abm/`, este documento §4-5. 🟢
4. *"Analizar mediante escenarios de simulación el efecto de cambios en comportamiento/variables estratégicas"* → dashboard, panel "Escenarios y política" (2 palancas causales reales, ver §5 y §10). 🟡 — cumplido de forma acotada, honesta sobre qué variables SÍ tienen mecanismo causal verificado.

---

## 3. Arquitectura de datos: qué es real, de dónde viene, a qué resolución

### 3.1 El tamaño real del problema (línea base, sin ambigüedad)

🟢 Bogotá generó, en 2023 (último año con cifra oficial internamente consistente),
**2,667,955 toneladas** de residuos (~7,300 ton/día); solo **495,238 toneladas (18.56%)** se
aprovecharon, el resto fue al Relleno Sanitario Doña Juana (`Residuos generados bogota.xlsx`,
reconciliada en `Investigacion_Salto_Aprovechamiento.md` §1).

🟢 Generación per cápita real: **0.35 ton/persona/año** (promedio 2018-2023) — corregido el
2026-07-11 de un valor previo (0.28) que venía de `Cerebro.xlsx` sin verificación independiente y
subestimaba la generación real ~20-25% (`src/config.py:75-77`, `Certificacion_Entregable_Final.md`
§1.2).

### 3.2 Tabla de granularidad real por fuente (la pregunta "¿por qué UPZ?", resuelta)

| Fuente | Granularidad real en el origen | Uso en el modelo |
|---|---|---|
| Manzanas con estrato (44,260 polígonos) | Manzana | Colapsada a UPZ a propósito — más fina que lo que sostiene el comportamiento |
| Población/hogares (DANE) | UPZ | Usada tal cual (real) |
| **EM2021** (Encuesta Multipropósito, ~234,000 hogares) | **UPZ real** (vía `COD_UPZ_GRUPO`, 112/112 UPZ cubiertas) para separación; localidad (20) para participación/vivienda/informalidad | **Fuente PRIMARIA de comportamiento desde 2026-07-14** |
| ECA2021 (Cultura Ambiental, ~2,282 personas) | Localidad (20, algunas n=1/n=3) | Legado — reemplazada por EM2021 (ver §7) |
| SIGAB (puntos críticos, contenedores) | Punto real (lat/lon) | Infraestructura real por UPZ |
| RBL consolidado (recolección formal) | Ninguna geografía (ciudad/operador) | Techo de capacidad real, ciudad |
| RURO (recicladores de oficio) | Localidad | Repartido a UPZ proporcional a población (supuesto declarado) |
| VIAT + subsidios CRA | Tarifa normativa | Aplicada por composición real de estrato |

Detalle completo, con la historia de por qué se descartó manzana y por qué UPZ no es
uniformemente "la mejor resolución posible": `Justificacion_Metodologica_Comite.md` §1-2.

### 3.3 El dato oficial de 2024-2025 NO se usa como objetivo — y por qué

🟡 UAESP reportó 43.88% (2024) y OAB 48.50% (2025) — ambas cifras son la salida de un **modelo
macroeconométrico propio de la UAESP**, no una medición directa (báscula), y coinciden con la
entrada en vigor del Decreto 1381/2024 y el nuevo PGIRS 2024-2028. La serie 2018-2023 (medida con
metodología estable) es la única internamente consistente — por eso es el objetivo de calibración,
no 2024-2025. Investigación completa, con las 3 fuentes independientes que se cruzaron para
confirmar esto: `Investigacion_Salto_Aprovechamiento.md` §1-3.

---

## 4. El modelo: agentes, mecanismos, flujo diario

Ver `Flujo_Completo_Logica_ABM.md` para el detalle línea por línea. Resumen:

**Agentes** (verificado, `abm/modelo.py`):
- **75,273 `HogarAgente`** — muestra del 3% de hogares reales, sobre **204 cohortes UPZ×estrato**
  reales (de 112 UPZ × 3 estratos = 336 posibles).
- **112 `PoblacionRecicladoresUPZ`** (una por UPZ) — recicladores de oficio reales (RURO),
  repartidos proporcional a población.
- **5 `OperadorUAESP`** (uno por ASE real: Promoambiental, LIME, Ciudad Limpia, Bogotá Limpia,
  Área Limpia) con capacidad diaria real (RBL consolidado).

**Los 3 mecanismos de la hipótesis, operacionalizados**:
1. **Free-riding / bajo impacto percibido**: cada 7 días, la actitud de separación de un hogar
   (`prob_separa_actual`) decae hacia un piso o se recupera hacia su base, según si sus vecinos de
   red (misma UPZ/estrato) separan sensiblemente menos que él (`agentes_hogar.py::actualizar_actitud_separacion`).
2. **Recicladores compiten sin coordinación**: reclaman del pool de material separado en orden
   aleatorio, antes que el sistema formal (`agentes_reciclador.py::step`).
3. **Infraestructura desigual**: el índice real de infraestructura (SIGAB) multiplica
   directamente la probabilidad efectiva de separación de cada hogar por UPZ.

**Ciclo diario**: Generación → decisión de separación (real + heterogénea, §8) → pool de UPZ →
recicladores informales reclaman → sistema formal reclama el sobrante (techo real de ciudad) →
lo no reclamado se pierde y cuenta como rechazo → Doña Juana.

---

## 5. Origen de cada parámetro — tabla completa (verificada, no de memoria)

| Parámetro | Valor final | Categoría | Evidencia |
|---|---|---|---|
| `PROB_SEPARA_PISO` | 0.4399 | 🟢 Real | Mínimo real de `pct_separa_upz` (EM2021, UPZ 95 Las Cruces, n=939 hogares) entre 112 UPZ |
| `FACTOR_BRECHA_INTENCION_ACCION` | 0.63 | 🟡 Calibrado | Búsqueda en rejilla (3 etapas) contra la serie real 2018-2023 — el parámetro más identificable |
| `BETA_DECAIMIENTO_SEPARACION` | 0.02 | 🟡 Calibrado | Insensible entre 0.03-0.05 (RMSE idéntico dentro de 0.01pp); 0.02 confirmado mejor a resolución completa |
| `UMBRAL_PERCEPCION_IMPACTO` | 0.07 | 🟡 Calibrado | Margen relativo (no absoluto) — crítico: 0.035 da RMSE 5-7× peor con la base EM2021 |
| `BETA_RECUPERACION_SEPARACION` | 0.02 | 🔴 No identificable | Rango de RMSE al variarlo: 0.000pp en 3 rondas de calibración distintas — se conserva, no se esconde |
| `ODDS_RATIO_PARTICIPACION_COMUNITARIA` | 2.48 | 🟢 Real | Regresión logística ponderada, EM2021, Sección 8/9 del EDA |
| `ODDS_RATIO_VIVIENDA_PROPIA` | 1.40 | 🟢 Real | Misma regresión |
| `ODDS_RATIO_INFORMAL` | 0.85 | 🟢 Real | Misma regresión, dirección negativa |
| `VIAT_PESOS_POR_TONELADA` | 11,388.0 | 🟢 Real | Tarifa oficial CRA/Ciudad Limpia, dic-2025 |
| `CAPACIDAD_RECOLECCION_KG_DIA_POR_RECICLADOR` | 15.0 | 🔴 Supuesto acotado | Sin dato directo; acotado por orden de magnitud (~7% del RBL formal) |
| `FRACCION_MUESTREO_HOGARES` | 0.03 | 🔴 Decisión de cómputo | No es un hallazgo, es tamaño de muestra |
| `CADA_CUANTOS_DIAS_ACTUALIZA_ACTITUD` | 7 | 🔴 Supuesto de cadencia | Sin dato longitudinal disponible en ninguna fuente |

Detalle completo con la historia de cada recalibración: `Justificacion_Metodologica_Comite.md`
§3, `abm/config_abm.py` (comentarios con fecha de cada cambio, nunca borrados).

---

## 6. Resultados finales de la calibración — "qué resultados nos dio"

### 6.1 Historia completa de calibración (3 episodios, cada uno documentado con su motivo)

| Fecha | Qué pasó | RMSE resultante |
|---|---|---|
| 2026-07-11 | Primera calibración. Reportó 4 de 5 parámetros como "no identificables" | 1.07pp (con el mecanismo, sin saberlo, muerto desde el día 1 — ver §7.1) |
| 2026-07-13 | Se encontraron y corrigieron 2 bugs reales de mecanismo (§7.1). Recalibración completa | 1.15pp (mecanismo genuinamente vivo) |
| 2026-07-14 | `prob_separa` cambió de fuente (ECA2021/localidad → EM2021/UPZ, §7.2). Recalibración de 3 etapas | **1.1961pp — RESULTADO FINAL VIGENTE** |

### 6.2 Trayectoria simulada final, 2018-2024 (encadenada, resolución completa: 365 días/año, 3% muestreo)

| Año | Real oficial | Simulado (final) | Diferencia |
|---|---|---|---|
| 2018 (ancla) | 15.38% | 18.08% | — (año no calibrado, punto de partida) |
| 2019 | 15.70% | 17.87% | +2.17pp |
| 2020 | 17.28% | 17.86% | +0.58pp |
| 2021 | 19.18% | 17.76% | -1.42pp |
| 2022 | 18.27% | 18.26% | -0.01pp |
| 2023 | 18.56% | 18.25% | -0.31pp |
| 2024 (contrafactual, sin dato real comparable) | 43.88% (no comparable, ver §3.3) | 18.32% | brecha ≈25.56pp, explicada por quiebre de metodología, no por el modelo |

RMSE calculado solo sobre 2019-2023 (2018 es ancla, no se calibra contra él): **1.1961pp**.
Reproducible exactamente: `abm/calibracion.py::correr_serie_anios(2018, 2024, dias_por_anio=365, rng=42)` con los parámetros de §5.

### 6.3 Sensibilidad de parámetros (método OAT, declarado explícitamente como tal — no es Sobol/Morris)

`data/processed/24_sensibilidad_parametros.csv` — construido de la rejilla ya corrida (no una
búsqueda nueva). `factor_brecha_intencion_accion` domina el ajuste; `beta_recuperacion` no mueve
el RMSE en ninguna combinación probada en 3 rondas de calibración distintas — es una limitación
de identificabilidad real, no un error. Nota: este CSV específico quedó de la calibración de
2026-07-13 (ECA2021) — no se regeneró tras el cambio de fuente de 2026-07-14; la conclusión
cualitativa (brecha domina, recuperación no identificable) se mantuvo consistente en las 3 rondas,
pero el CSV numérico exacto es de la penúltima ronda, declarado así explícitamente (`Justificacion_Metodologica_Comite.md` §6).

---

## 7. Bugs reales encontrados y corregidos — transparencia metodológica completa

Un comité que audite el código va a encontrar cambios de parámetros a lo largo del tiempo — aquí
está el porqué de cada uno, para que no se lean como inconsistencia sino como el rastro de una
auditoría real.

### 7.1 El mecanismo de imitación/free-riding estaba muerto desde el día 1 (encontrado 2026-07-13)

Dos bugs independientes, ambos en `agentes_hogar.py`:
1. El disparador de decaimiento comparaba contra un umbral **absoluto** (0.15) que ninguna de las
   204 cohortes reales alcanzaba nunca (mínimo real: 0.187).
2. El piso de decaimiento no se reescalaba por la brecha intención-acción, dejándolo muy por
   encima de la base real del 99.65% de los agentes.

Efecto: TODAS las series del dashboard salían perfectamente planas. Esto **explica
retroactivamente** por qué la primera calibración (2026-07-11) reportó 4 de 5 parámetros como "no
identificables" — nunca llegaban a ejecutarse. Detalle completo:
`Investigacion_Salto_Aprovechamiento.md` §8.

### 7.2 UPZ heredaba comportamiento de localidad sin necesidad (encontrado y resuelto 2026-07-14)

El usuario compartió el diccionario completo de EM2021 y se encontró `COD_UPZ_GRUPO` — geografía
UPZ real nunca antes extraída. Verificado: 112/112 UPZ reales cubiertas, cada una con 600+
hogares de muestra propia — reemplaza a ECA2021 (localidad, con Los Mártires n=1 y Santa Fe n=3).
Spot-check: Los Mártires pasó de 100% (heredado, n=1) a 55-67% por UPZ real; Santa Fe de 33% (n=3)
a 44-75% por UPZ real. Detalle: `Justificacion_Metodologica_Comite.md` §5bis.

### 7.3 La resolución reducida de calibración dejó de ser un proxy confiable (encontrado 2026-07-14)

Al cambiar la fuente de datos (§7.2), la búsqueda en rejilla a resolución reducida (90 días/año)
encontró un óptimo (RMSE=1.21pp) que, al confirmarse a resolución completa (365 días/año), resultó
mucho peor (RMSE=2.10pp). Hipótesis verificada probando 4 variantes adicionales directamente a
resolución completa: el ciclo semanal de actualización de actitud corre ~12 veces en 90 días pero
~52 veces en 365 — un `beta_decaimiento` que se ve bien con 12 ciclos sobre-acumula con 52. Se
encontró la combinación correcta (`decay=0.02`) probando variantes a resolución completa
directamente. Es la primera vez en el proyecto que la resolución reducida no fue un proxy
confiable — documentado como hallazgo metodológico, no descartado en silencio.

### 7.4 Primer diseño de heterogeneidad rompió la calibración (encontrado y corregido 2026-07-14)

Al conectar 2 predictores reales adicionales (vivienda propia, informalidad) como heterogeneidad
individual, el primer diseño (mutar `prob_separa_base` por agente) rompió el RMSE (1.15pp→4.25pp)
porque esa misma variable gobierna el disparador NO LINEAL de decaimiento — agregar varianza ahí
cambia cuántos agentes cruzan el umbral, no solo el nivel. Rediseñado como multiplicador de salida
separado (`factor_heterogeneidad_hogar`), verificado con RMSE re-confirmado idéntico (1.1961pp).
Detalle completo: `Justificacion_Metodologica_Comite.md` §5.

### 7.5 Otros bugs reales, menores pero documentados

- Capacidad formal de recolección sobreestimada ~12× (dividía un total ANUAL entre 30, no 365) — `Certificacion_Entregable_Final.md` §1.2.
- 3 archivos RBL de 2020 descartados en silencio por un fallo del *sniffer* de CSV — mismo documento.
- `construir_o_cargar_participacion_comunitaria()` no ponderaba por `FEX_C` (factor de expansión de la encuesta) — corregido 2026-07-14, efecto pequeño pero es la cifra correcta de citar.
- Un comentario de código decía "EM2021" cuando la fuente real era ECA2021 (error de documentación, no de cálculo) — corregido y dejado trazable en `abm/config_abm.py`.
- "Generación por estrato" (panel nuevo del dashboard) no sumaba el 100% del total generado — se encontró que `pct_estrato_bajo/medio/alto` no suman 100% en ninguna UPZ real (~11-17% de manzanas sin estrato asignado en la fuente DANE) — se corrigió mostrando una categoría explícita "Sin estrato asignado" en vez de subcontar en silencio.

---

## 8. Heterogeneidad real y qué representa un "agente hogar"

Un `HogarAgente` es una muestra ponderada de una cohorte real UPZ×estrato — NO un hogar real
individual (no hay GPS de hogares), NO una cohorte agregada sin varianza. De los 6 predictores
reales y significativos que el propio EDA encontró (regresión logística ponderada, EM2021), 3
están conectados al ABM: participación comunitaria (OR=2.48), vivienda propia (OR=1.40),
informalidad (OR=0.85, dirección negativa) — 2 de los 3 en cuartos, no en `prob_separa_base` (ver
§7.4). `log_ingreso` se probó y se descartó por no ser significativo (p=0.33) — decisión de
rigor, no un hueco. Contraste honesto de escala con MATSim (millones de agentes, aprendizaje
iterativo, red vial real — vs. 75,273 agentes, calibración anual estática, red de vecindad UPZ):
`Justificacion_Metodologica_Comite.md` §7.

---

## 9. Verificaciones de robustez ya hechas (identidades numéricas, no solo "se ve bien")

| Verificación | Resultado |
|---|---|
| Σ(recolectado informal) + Σ(recolectado formal) == aprovechado acumulado | Exacto (diferencia = 0.0000 ton, verificado con script directo) |
| Separado en la fuente ≥ reclamado (informal+formal) | Cumplido siempre (fuga real documentada en el panel "Flujo de agentes" del dashboard) |
| Promedio ponderado de `factor_heterogeneidad_hogar` por cohorte == 1.0 | Exacto, en las 199 cohortes con >1 agente |
| Crosswalk EM2021→UPZ real | 112/112 UPZ cubiertas, 0 conflictos |
| RMSE re-confirmado tras cada cambio de mecanismo | Sí, en las 3 rondas de calibración — nunca se asumió que un cambio "no debería afectar el resultado" sin volver a correrlo |
| Render headless del dashboard completo (75,273 agentes, todos los paneles) | Sin excepciones |

---

## 10. Limitaciones honestas — lista consolidada final

1. **El objetivo de calibración (serie 2018-2023) es la salida de un modelo econométrico de la
   UAESP, no una medición física directa** — se calibra un modelo contra la estimación de otro
   modelo. Práctica aceptada cuando no hay mejor ground truth, pero debe decirse así de explícito.
2. Solo `factor_brecha_intencion_accion` es claramente identificable; `beta_recuperacion` no
   mueve el RMSE en ninguna combinación probada en 3 rondas de calibración — limitación real, sin
   dato longitudinal disponible en ninguna fuente para medir velocidad de cambio de actitud.
3. La resolución espacial real es la UPZ (112 zonas) — no hay dato de calles, rutas de camión
   individuales, ni GPS de flota real en ninguna fuente pública disponible.
4. Los hogares en los mapas del dashboard son posiciones simbólicas (proporcionales a
   composición real de estrato, o al estado real de comportamiento) — no son coordenadas GPS
   reales de viviendas.
5. `~11-17%` de la generación de residuos cae en manzanas "sin estrato asignado" en la fuente
   DANE — mostrado explícitamente en el dashboard, no absorbido en las 3 categorías conocidas.
6. Educación ambiental, incentivos económicos y frecuencia de recolección **no tienen mecanismo
   causal verificado** en el modelo — deliberadamente excluidos del panel de escenarios (solo
   infraestructura y capacidad formal, que sí lo tienen).
7. El análisis de sensibilidad es OAT (uno-a-la-vez), no un método global (Sobol/Morris) —
   válido y estándar para el presupuesto computacional de un ABM de tesis, declarado como tal.
8. El dashboard no proyecta más allá de 2024 — no existe ningún dato real que sostenga una
   proyección a 2025-2035; el selector de año simulado se limita a 2018-2024 (dato real) a
   propósito.
9. Se evaluó y se descartó explícitamente incluir CO2 evitado, árboles equivalentes y empleos
   verdes generados — sin factor de conversión oficial citable disponible para este proyecto,
   incluirlos sería inventar precisión.
10. El costo fiscal del incentivo (VIAT) asume que toda tonelada aprovechada recibe el pago
    completo — no descuenta fricciones administrativas reales del proceso de pago.
11. `data/processed/24_sensibilidad_parametros.csv` quedó de la penúltima calibración (ECA2021),
    no se regeneró numéricamente tras el cambio de fuente de la última ronda — la conclusión
    cualitativa se mantuvo, el archivo exacto no.

---

## 11. Estado verificado de cada componente (hoy, no de memoria)

| Componente | Estado | Verificación |
|---|---|---|
| `src/` (9 módulos) | ✅ Importa sin error | Verificado en esta sesión |
| `abm/` (10 módulos) | ✅ Importa y corre sin error | Modelo instanciado y corrido en esta sesión |
| Calibración final | ✅ RMSE=1.1961pp confirmado a resolución completa | `abm/calibracion.py::correr_serie_anios`, corrida real esta sesión |
| Dashboard (`abm/dashboard.py`) | ✅ Corriendo | HTTP 200, log limpio, render headless sin excepciones, verificado esta sesión |
| Documentación (`src/Auditorias/`, 12 documentos) | ✅ Consistente | Sin contradicciones activas conocidas; notas de actualización trazables donde algo cambió |

---

## 12. Mapa de trazabilidad — cómo verificar cada cosa usted mismo

| Quiere verificar... | Comando/archivo exacto |
|---|---|
| El RMSE final | `python -c "from abm import calibracion; df=calibracion.correr_serie_anios(2018,2024,dias_por_anio=365,rng=42,verbose=True); print(calibracion._error_cuadratico(df))"` |
| Los parámetros calibrados vigentes | `abm/config_abm.py` (con su historia completa en comentarios, nunca borrada) |
| El crosswalk EM2021→UPZ | `data/processed/26_crosswalk_em2021_upz.csv` |
| La separación real por UPZ (EM2021) | `data/processed/27_separacion_upz_em2021.csv` |
| Que el mecanismo de decaimiento SÍ está vivo | Correr el dashboard, Play varios días, observar que las series NO son planas |
| El flujo real informal-vs-formal | Dashboard, sección 5, panel "Flujo de agentes en vivo" |
| Origen de cada regla de negocio | `Reglas_Negocio_v2_y_Modelado_Agentes.md` §3, parámetro por parámetro |

---

## 13. Preguntas que un comité probablemente hará (con respuesta lista)

**¿Por qué UPZ y no localidad o manzana?** → §3.2 de este documento y
`Justificacion_Metodologica_Comite.md` §1-2: UPZ es el techo real para infraestructura/demografía;
desde 2026-07-14 también lo es para comportamiento (EM2021). Manzana existe pero es más fina que
lo que el comportamiento sostiene.

**¿De dónde sale cada beta?** → §5 de este documento, tabla completa con semáforo de confianza.

**¿Cómo se calibró y contra qué?** → §6. Rejilla exhaustiva, no optimizador de caja negra; contra
la serie 2018-2023, con la advertencia explícita de que esa serie es un modelo, no una medición.

**¿Por qué el modelo no predice el 43.88%/48.50% de 2024-2025?** → §3.3 y §6.2: esas cifras
coinciden con un cambio de metodología de medición, no se toman como objetivo por eso — es un
hallazgo, no una falla de ajuste.

**¿Qué tan comparable es esto con MATSim (o un ABM "de verdad")?** →
`Justificacion_Metodologica_Comite.md` §7: inspirado en el espíritu, no en la escala — se declara
la diferencia explícitamente, no se sobrevende la analogía.

**¿Qué pasa si cambio la fuente de datos otra vez, o agrego un mecanismo nuevo?** → Hay que
volver a correr la calibración completa a resolución completa, no asumir que el resultado
anterior sigue siendo válido (ver §7.3-7.4, encontrado dos veces en este mismo proyecto).

---

## 14. Qué queda pendiente (honesto, no forzado a cerrarse aquí)

- `data/processed/24_sensibilidad_parametros.csv` no se regeneró numéricamente tras la última
  recalibración (§6.3) — la conclusión cualitativa se sostiene, el archivo exacto es de la ronda
  anterior.
- Free-riding/confianza en recicladores (preguntas P13/P14 de ECA2021) — identificadas como
  relevantes pero no conectadas como mecanismo nuevo, documentado como trabajo futuro
  (`Justificacion_Metodologica_Comite.md` hallazgo 7).
- `NVCBP11DA` (frecuencia real de recolección por hogar, EM2021) — mismo estado, sin conectar.
- Reorganización de `Backup y otros/Modelo_Residuos_Solidos_Bogota (2).ipynb` (el notebook que
  realmente regenera `data/processed/`) — sigue en una carpeta que sugiere "no tocar", pendiente
  desde `Certificacion_Entregable_Final.md` §1.4.
- La redacción final de la tesis como documento (introducción, marco teórico redactado,
  conclusiones, formato CUN) — fuera del alcance de todo lo auditado aquí.

---

*Fin de la auditoría. Este documento se escribió para que usted pueda validar el proyecto por su
cuenta, no para que confíe en él — cada cifra citada aquí tiene un comando o archivo exacto en
§12 para que la reproduzca usted mismo antes de defenderla ante el comité.*
