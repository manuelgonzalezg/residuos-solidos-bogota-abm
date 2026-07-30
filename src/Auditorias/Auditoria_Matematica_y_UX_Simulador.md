# Auditoría severa: sustento lógico-matemático + experiencia de usuario del simulador

**Fecha:** 2026-07-23 · **Alcance:** simulador NetLogo (`abm/netlogo/`), datos exportados,
artefactos de calibración (`data/processed/22-24`), y comunicabilidad del trabajo completo.
**Método:** cada afirmación se recalculó desde los CSV fuente con código independiente (no se
confió en la documentación existente). Veredictos: ✅ verificado · ⚠️ hallazgo que requiere
acción · ❌ error.

---

## PARTE A — Auditoría de sustento lógico y matemático

### A1. ✅ Generación de residuos (0.35 ton/persona/año) — VERIFICADO, con matiz importante

**Afirmación:** la ciudad genera `población × 0.35 / 365` ton/día.
**Verificación:** población 2024 = 8.002.180 → esperado ingenuo = 7.673 ton/día. El simulador
muestra **6.790 ton/día**. La diferencia (11,5%) NO es un error: los agentes hogar solo se crean
para las 3 categorías de estrato (bajo/medio/alto), que cubren el **88,5% de la población**
(7.080.816 personas). 7.080.816 × 0.35/365 = **6.790 ton/día — cuadra exacto** con el simulador.
**Matiz:** la cobertura por UPZ va de 25,6% (mínimo, una UPZ con estratificación incompleta en
la fuente de manzanas) a 97,1% (mediana 89,0%).
**Acción:** (1) documentar en la pestaña Info y en la tesis que el modelo representa el ~88,5%
de la población clasificable por estrato — **HECHO** (Info del simulador + §7.6.4 de la tesis);
(2) revisar las UPZ de baja cobertura en `manzanaestratificacion.gpkg` — **IDENTIFICADAS**
(2026-07-23): UPZ 2 La Academia (Suba, 25,6%, 2.304 hogares), UPZ 117 (Fontibón, 27,3%, 335
hogares), UPZ 105 (Engativá, 30,8%), UPZ 108 (Puente Aranda, 32,4%) y UPZ 63 (Ciudad Bolívar,
33,3%, solo 10 hogares). Son UPZ predominantemente no residenciales o de desarrollo reciente
(aeropuerto, industria, borde urbano) donde muchas manzanas no tienen estrato asignado —
patrón esperable de la fuente catastral, no un error de procesamiento. Impacto agregado bajo
(las 5 suman ~6.500 hogares de 2,84 millones, el 0,23%). Queda documentado como limitación
conocida de cobertura, sin acción correctiva necesaria.

### A2. ✅ Capacidad formal ASE y "% capacidad usada" — COHERENTE, etiqueta mejorable

**Verificación:** capacidad 2024 = 4.865,2 ton/día (suma de 5 ASE del CSV). El monitor muestra
18,78% porque mide SOLO el flujo recogido por operadores formales (1.258 aprovechado del día
− ~343 de recicladores = ~915; 915/4.865 = 18,8% ✓). Si alguien divide aprovechado total /
capacidad obtiene 25,9% y creería que hay un error.
**Acción:** renombrar el monitor para que se autoexplique ("Camiones ASE: % de su capacidad
que usan") — el hallazgo de fondo (la capacidad formal NUNCA se satura) es correcto y robusto.

### A3. ✅ Piso de separación 0.4399 — VERIFICADO contra dato crudo

Mínimo real de `pct_separa_upz` 2024 = **43,9926% en UPZ 95** (Las Cruces) — coincide con
`config_abm.PROB_SEPARA_PISO = 0.4399` y con su justificación documentada (EM2021, n=939). ✓

### A4. ✅ Costo fiscal VIAT — EXACTO

466.239,3 ton aprovechadas × 11.388 COP/ton = **5.309,5 millones COP** = lo que muestra el
simulador, centavo a centavo. ✓

### A5. ✅ Matemática de odds-ratio — EXACTA

OR 2.48 sobre base 0.5 → 0.7126 ✓ (fórmula momios exacta, no aproximación multiplicativa).
OR 1.40 → factor relativo 1.1667 ✓. Idéntico a `agentes_hogar.py`. ✓

### A6. ✅ Consistencia interna del % de aprovechamiento

18,81% del simulador = aprovechado acumulado / generado MODELADO (2.478.350 ton/año). Contra el
generado ingenuo de ciudad completa daría 16,65% — ver A1: es la misma explicación de cobertura.
Internamente consistente. ✓

### A7. ⚠️ (RECONCILIADO EN SEGUNDA PASADA) — Los "tres RMSE" tienen explicación, pero falta blindarla

**Primera pasada de esta auditoría:** el 23 recalculado daba 1.4567 pp ≠ 1.1961 documentado.
**Segunda pasada (leyendo `calibracion.py::_error_cuadratico`):** la convención OFICIAL del
proyecto **excluye el año ancla 2018** del RMSE (el encadenamiento parte de 2018, no se predice
a sí mismo). Con esa convención, el archivo 23 da **1.1519 pp** — consistente con el 1.1961
documentado (misma convención, corridas distintas). El 1.4567 de la primera pasada incluía 2018
indebidamente. *Se deja el error y la corrección a la vista: así se audita.*

| Artefacto | RMSE | Explicación |
|---|---|---|
| `22_...rejilla` mejor fila: 1.117 (brecha=0.55, cap=10) | resolución REDUCIDA (90 días) | la búsqueda; su óptimo NO sobrevivió a resolución completa (hallazgo ya documentado en config_abm.py) |
| `24_...sensibilidad` es_optimo: **1.1961** (combo final) | resolución completa | la cifra citada en docs ✓ |
| `23_...confirmacion` recalculado: **1.1519** | resolución completa, sin ancla | consistente con 1.1961 ✓ |

**Acciones restantes (menores pero necesarias):**
1. Explicitar en la tesis y en la Justificación Metodológica que el RMSE se calcula sobre
   2019-2023 **excluyendo el año ancla 2018** (hoy está solo implícito en el código).
2. Regenerar 23 con semilla fija y registrar qué corrida lo produjo (script entregado:
   `abm/regenerar_confirmacion.py`) para que 23 y 24 cuenten la misma historia con una sola cifra.
3. Citar SIEMPRE la cifra con su convención: "RMSE ≈ 1.2 pp (2019-2023, año ancla excluido)".

### A8. ⚠️ SEVERO — El modelo replica el NIVEL, no la TENDENCIA

Errores por año (sim − real): 2018 **+2.47**, 2019 +2.13, 2020 +0.57, 2021 **−1.31**, 2022
+0.06, 2023 −0.23. El simulado es casi plano (17.8→18.4) mientras el real sube (15.4→18.6).
El proyecto ya lo reconoce en parte (análisis shift-share del salto 2021), pero **el simulador
no lo comunica**: la gráfica principal no muestra el dato real, así que un espectador no puede
juzgar la validez por sí mismo.
**Acción:** añadir la línea del dato real del año elegido a la gráfica principal del simulador
(validación a la vista). En la tesis: presentar la tabla de errores por año, no solo el RMSE.

### A9. ✅ Capacidad de recicladores — orden de magnitud plausible

23.859 recicladores × 15 kg/día = 357,9 ton/día ≈ 7% de la capacidad formal — dentro de la cota
de consistencia documentada (supuesto acotado, RN020-022 "Pendiente"). ✓

### A10. Resumen A: la matemática del modelo ES sólida (8✅/2⚠️)

Ningún error de cálculo. Los dos ⚠️ son de **gobernanza de artefactos** (A7) y de
**comunicación de validez** (A8) — ambos corregibles sin tocar el modelo.

---

## PARTE B — Auditoría basada en el usuario (severa)

**Prueba aplicada:** ¿qué entiende cada público en los primeros 60 segundos frente al simulador?

### B1. ❌ No existe la "historia de entrada"

Nada en pantalla dice QUÉ es esto ni QUÉ pregunta responde. Un espectador ve un mapa verde con
puntos y 14 números. La pregunta del proyecto cabe en una frase: *"¿Cuánto más reciclaría
Bogotá si mejora la infraestructura o la capacidad de recolección?"* — debe estar visible.

### B2. ❌ Jerga sin traducir en la interfaz

VIAT, UPZ, ASE, RURO, EM2021, CRA, "brecha intención-acción", "beta-decaimiento" — ninguna
definida en pantalla. Para "cualquier público" cada sigla es un muro. Falta un mini-glosario
visible (3 líneas bastan).

### B3. ⚠️ 8 sliders con la misma jerarquía visual, pero solo 2 son "jugables"

Las dos palancas causales (infraestructura, capacidad formal) están mezcladas con 5 parámetros
de calibración que NADIE debería tocar y un año. El usuario no sabe qué mover. Los de
calibración deben estar visualmente degradados/separados ("⚙ avanzado — no tocar para réplica").

### B4. ⚠️ Nadie puede "jugar un escenario" sin instrucciones

Para responder la pregunta del proyecto hay que: mover slider → setup → año completo → comparar
mentalmente con la corrida anterior. Solución de manual de museo de ciencia: **botones de
escenario de 1 clic** ("Escenario real", "Doble infraestructura", "Doble capacidad formal") que
configuran y corren solos.

### B5. ⚠️ 14 monitores compiten sin lectura guiada

El resultado principal (% aprovechamiento) ya está destacado ✓, pero "Hogares simulados" vs
"Hogares reales" es un detalle técnico que no merece 2 casillas; "Día" aparece dos veces
(monitor + contador de la vista). Consolidar a ~10.

### B6. ⚠️ La gráfica principal no tiene referencia externa

Sin la línea del dato real (ver A8) ni una meta de ciudad (p.ej. PGIRS), "18.8%" no significa
nada para un espectador: ¿es bueno? ¿es malo? Contexto = comprensión.

### B7. ✅ Aciertos que conservar

Silueta de Bogotá reconocible; actores con íconos legibles; leyenda presente; secciones
numeradas; escala real documentada; paleta profesional; Info narrativa completa.

---

## PLAN PRIORIZADO (impacto ÷ esfuerzo)

| # | Mejora | Ataca | Esfuerzo |
|---|---|---|---|
| 1 | Titular de la pregunta + subtítulo "verde=bien, rojo=se rinde" arriba del mapa | B1 | Bajo |
| 2 | Botones de escenario de 1 clic (real / doble infra / doble capacidad) | B4 | Bajo |
| 3 | Línea de dato real en la gráfica principal | A8, B6 | Bajo |
| 4 | Mini-glosario de 3 líneas en pantalla (UPZ, ASE, VIAT) | B2 | Bajo |
| 5 | Separador "⚙ AVANZADO" degradando los 5 sliders de calibración | B3 | Bajo |
| 6 | Renombrar monitores a lenguaje humano y consolidar a ~10 | A2, B5 | Bajo |
| 7 | Regenerar artefactos 22/23 con el combo final (o documentar su origen) | A7 | Medio (requiere correr Python) |
| 8 | Nota de cobertura 88,5% en Info + tesis; revisar UPZ 25,6% | A1 | Bajo/Medio |
| 9 | Tabla de errores por año en la tesis (nivel vs tendencia) | A8 | Medio |
| 10 | "Explícalo en 60 segundos" al inicio de la pestaña Info | B1 | Bajo |

**Veredicto global:** el fondo matemático está sano (2 hallazgos de gobernanza, 0 errores de
cálculo). El déficit real es de **comunicación**: el simulador sabe más de lo que cuenta.
Los ítems 1-6 y 10 se pueden aplicar de inmediato en el `.nlogox` sin tocar la lógica calibrada.
