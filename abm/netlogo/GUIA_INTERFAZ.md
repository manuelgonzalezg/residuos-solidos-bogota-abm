# Guía para armar la pestaña Interface en NetLogo

> **ACTUALIZACIÓN 2026-07-23 — esta guía ya no es necesaria para el uso normal.**
> `residuos_bogota.nlogox` ahora incluye la interfaz completa lista para abrir: mapa con la
> silueta urbana real de Bogotá (umbral de 14 unidades a los centroides UPZ), actores visibles
> (hogares como personas con actitud verde/amarillo/rojo semitransparente, recicladores de
> oficio naranjas por UPZ, 5 camiones ASE patrullando con descarga en el relleno, montículo del
> Relleno Doña Juana con contador de rechazo), panel de indicadores agrupado (ciudad / actores y
> flujos), 5 switches de capas visuales, selector de vista del mapa (4 vistas) y 3 gráficas.
> Nada de la capa visual altera la lógica calibrada (RMSE ≈ 1.196 pp) — los movimientos de
> camiones y recicladores son ilustrativos; las cantidades las gobiernan las reglas replicadas
> del modelo Python. `codigo_modelo.nls` sigue siendo el espejo exacto del código del `.nlogox`.
> Esta guía se conserva como referencia histórica de cómo armar la interfaz a mano.

Por qué esta guía y no un `.nlogo` de un solo clic: la pestaña Interface de NetLogo se guarda en
un formato binario-posicional (coordenadas de píxeles por widget) que no puedo verificar sin
tener NetLogo real abierto en este entorno. Prefiero darte algo garantizado de armar en 10-15
minutos con la interfaz gráfica (cero riesgo) a un archivo que podría no abrir. El código
(`codigo_modelo.nls`) sí es texto plano NetLogo puro — ese no tiene ese riesgo.

## Paso 0 — Antes de pegar el código

El código referencia 8 variables como **sliders** (NetLogo las declara automáticamente al crear
el slider — si las declararas también con `globals`, NetLogo da error de "ya definida"). El
modelo no compila hasta que existan el código Y los 8 sliders. Puedes crear los sliders antes o
después de pegar el código, pero no lo des por compilado hasta tener ambas cosas.

## Paso 1 — Copiar los datos

Copia la carpeta `abm/netlogo/datos/` (los 3 `.csv`) a la MISMA carpeta donde guardes tu archivo
`.nlogo` — el código los lee con ruta relativa (`"datos/netlogo_zonas.csv"`).

## Paso 2 — Los 8 sliders (pestaña Interface → botón "Slider")

| Variable global (nombre exacto) | Mínimo | Máximo | Incremento | Valor por defecto |
|---|---|---|---|---|
| `anio-simulado` | 2018 | 2024 | 1 | 2024 |
| `multiplicador-infraestructura` | 0.5 | 2.0 | 0.1 | 1.0 |
| `multiplicador-capacidad-formal` | 0.5 | 2.0 | 0.1 | 1.0 |
| `capacidad-recoleccion-individual` | 5.0 | 30.0 | 1.0 | 15.0 |
| `beta-decaimiento` | 0.0 | 0.10 | 0.01 | 0.02 |
| `beta-recuperacion` | 0.0 | 0.10 | 0.01 | 0.02 |
| `umbral-percepcion-impacto` | 0.0 | 0.10 | 0.005 | 0.07 |
| `factor-brecha-intencion-accion` | 0.20 | 1.00 | 0.05 | 0.63 |

Las dos primeras (`multiplicador-infraestructura`, `multiplicador-capacidad-formal`) son las
**únicas dos palancas causales de escenario** verificadas en el modelo original — las demás son
de calibración/comportamiento. Con todas en su valor por defecto, la corrida reproduce el dato
real de hoy sin ninguna intervención.

## Paso 3 — Pegar el código

Abre la pestaña **Code**, borra el contenido de ejemplo, y pega **todo** el archivo
`codigo_modelo.nls`. Guarda (Ctrl+S) — debería compilar sin errores si ya creaste los 8 sliders.

## Paso 4 — Botones (pestaña Interface → botón "Button")

| Etiqueta sugerida | Comando | Tipo |
|---|---|---|
| ▶ Preparar (setup) | `setup` | una vez |
| ▶▶ Correr (día a día) | `go` | **Forever** (marca el checkbox "Forever") |
| ⏩ Correr año completo (365 días) | `correr-anio-completo` | una vez (puede tardar, corre 365 días de golpe) |

## Paso 5 — Monitors (pestaña Interface → botón "Monitor")

| Etiqueta | Reporter |
|---|---|
| Día | `ticks` |
| Hogares reales (ciudad) | `hogares-reales-totales` |
| Hogares simulados | `hogares-simulados` |
| % aprovechamiento acumulado | `pct-aprovechamiento-acumulado-ciudad` |
| % aprovechamiento hoy | `pct-aprovechamiento-dia` |
| Generado hoy (ton) | `generado-hoy-ton` |
| Aprovechado hoy (ton) | `aprovechado-hoy-ton` |
| Rechazo hoy (ton) | `rechazo-hoy-ton` |
| Capacidad formal usada (%) | `capacidad-formal-usada-pct` |
| Costo fiscal VIAT acumulado (COP) | `costo-fiscal-viat-cop` |

## Paso 6 — Plots (pestaña Interface → botón "Plot")

**Plot 1 — "% Aprovechamiento acumulado"**
- Pen única: `plot pct-aprovechamiento-acumulado-ciudad`

**Plot 2 — "Balance diario (ton)"**
- Pen "generado": `plot generado-hoy-ton`
- Pen "aprovechado": `plot aprovechado-hoy-ton`
- Pen "rechazo": `plot rechazo-hoy-ton`

**Plot 3 — "Estado de actitud de los hogares"**
- Pen "bueno" (verde): `plot n-estado-bueno`
- Pen "advertencia" (amarillo): `plot n-estado-advertencia`
- Pen "crítico" (rojo): `plot n-estado-critico`

Cada pen se configura en el editor del plot (clic derecho → Edit → pestaña de cada pen), con el
comando `plot <reporter>` en su campo "Pen update commands", y `plot-pen-reset` / nada especial
en "Setup commands" (los plots ya se limpian solos con `clear-all` en `setup`).

## Paso 7 — El "universo" (View / mundo)

**No configures manualmente el tamaño del mundo** — `setup` lo hace automáticamente
(`resize-world`) según los centroides reales de las 112 UPZ leídos del CSV, cada vez que cambias
el año. Solo asegúrate, en Settings del modelo (icono de engranaje sobre el View), de dejar:
- **Wrapping**: NO marcado en X ni en Y (el mapa no debe "envolver" en los bordes).
- Patch size: el que quieras visualmente (ej. 2-3 px) — es solo cosmético, `setup` ya ajusta
  min/max-pxcor/pycor reales.

## Qué vas a ver al correr

- El mapa se colorea como un mosaico real de las 112 UPZ de Bogotá (verde más intenso = más %
  aprovechado acumulado en esa zona).
- Los hogares (miles de puntos) se ven dispersos dentro de su zona, coloreados verde/amarillo/rojo
  según su estado de separación (en su base / decayendo / en el piso) — se actualiza cada 7 días
  simulados, igual que en el modelo Python original.
- Los recicladores de oficio y los 5 operadores de aseo existen como agentes reales (mueven los
  números) pero están ocultos por defecto (`hidden? true`) — puedes quitarles el `hidden?` en el
  código si quieres verlos como marcadores en el mapa.

## Verificación (sin exigir números idénticos a Python)

NetLogo y Python usan generadores de números aleatorios distintos — no busques una réplica
numérica exacta, sino:
1. **112 zonas creadas**, hogares simulados del mismo orden de magnitud que Python (~75,000 para
   2024) — puede variar un poco por redondeo, no por error.
2. **% de capacidad formal usada** debe quedarse muy por debajo de 100% todo el año (hallazgo real
   del proyecto: la capacidad formal casi nunca se satura).
3. Subir `multiplicador-infraestructura` a 2.0 debe subir el % de aprovechamiento acumulado final;
   igual dirección que en el dashboard Python.
4. La curva de "% aprovechamiento acumulado" debe verse mayormente plana con pequeños escalones
   cada 7 ticks (cuando se actualiza la actitud), no una curva suave.
