# Certificación del entregable: EDA → Reglas de negocio → ABM → Dashboard
### Auditoría final de orden y corrección, previa a presentación ante el comité de tesis
**Autores:** Manuel Alejandro González Gallego, Gloria Inés Robledo Ulloa — CUN
**Fecha:** 2026-07-11

> **⚠️ Documento histórico, superado en estado (no en validez de lo que ya corrigió):** desde
> 2026-07-14, la certificación vigente es `Auditoria_Final_Comite_Tesis.md` — cubre 3 rondas de
> recalibración adicionales (mecanismo de decaimiento reparado, fuente de comportamiento cambiada
> a EM2021/UPZ, heterogeneidad real conectada) que ocurrieron después de esta ronda. El RMSE
> citado aquí (1.07pp) y el estado del dashboard descrito aquí ya NO son los vigentes. Todo lo que
> esta ronda corrigió (purga de `Cerebro.xlsx`, fix de per-cápita 0.28→0.35, fix de capacidad
> formal 12×, fix de archivos RBL 2020) sigue vigente y no se repite en el documento nuevo.

---

## 0. Alcance de esta certificación

Esta revisión cubre **desde la limpieza de datos hasta la ejecución del dashboard** — no incluye
la redacción del documento de tesis en sí (introducción, marco teórico redactado, conclusiones,
formato CUN), que sigue siendo trabajo pendiente y está fuera de este alcance. Dentro de lo que
cubre, la pregunta que responde es: **¿está todo correcto, ordenado, y puede presentarse como
avance ante el comité, ahora mismo?**

**Veredicto: sí**, con las salvedades explícitas de la sección 6 (huecos de dato conocidos, ya
documentados en otras partes del proyecto, no ocultados).

---

## 1. Qué se hizo en esta ronda de auditoría final

### 1.1 `Cerebro.xlsx` — tratado como si nunca hubiera existido (instrucción explícita)

Se buscó y eliminó **toda** referencia a `Cerebro.xlsx` en el código activo y en los 6 documentos
`.md` activos del proyecto raíz:

- `src/config.py`: eliminada la ruta `CEREBRO_DIR` y la entrada `ARCHIVOS["cerebro"]`.
- `src/carga_datos.py`: eliminada la función `cargar_cerebro()` (no tenía invocaciones activas).
- `abm/config_abm.py`, `abm/datos_reales.py`: reescritos los comentarios que citaban el archivo.
- `Plan_EDA.md`, `Recoleccion_Datos_Fase2.md`, `Reglas_Negocio_v2_y_Modelado_Agentes.md`,
  `Auditoria_Completa_Datos_Limpieza_EDA.md`, `Resultados_EDA_Funcionamiento_Bogota.md`: reescritas
  las secciones/frases que lo mencionaban (incluida la sección completa "2.3 Reglas de negocio" de
  la auditoría, que describía el hallazgo de las 2 hojas contradictorias — se retiró, con
  renumeración de las secciones siguientes).
- `notebooks/EDA_Dirigido_Fase3.ipynb`: 3 celdas de markdown editadas para quitar la mención.

**Lo único que NO se tocó**: la carpeta `Backup y otros/` (dos notebooks originales y
`Revision_Comite_Tesis.md`) — es un archivo histórico explícitamente nombrado "Backup", y
reescribir su contenido original le quitaría el propósito de ser un respaldo fiel. El archivo de
datos en sí, `data/raw/Cerebro/Contexto del negocio - Cerebro.xlsx`, **tampoco se borró físicamente**
(es un archivo de dato, no generado por código, y borrarlo sería una acción difícil de revertir):
queda ahí, sin ningún código que lo lea o lo referencie — si quieres que se elimine físicamente,
dímelo y lo hago.

### 1.2 Tres errores reales corregidos (no solo "limpieza de referencias")

| Error encontrado | Dónde | Efecto si no se corregía |
|---|---|---|
| `RESIDUOS_PER_CAPITA_TON_ANIO = 0.28` — venía de `Cerebro.xlsx` (RN001), sin verificación independiente | `src/config.py` | Al recalcularlo desde dato real (`Residuos generados bogota.xlsx` ÷ población real por año, 2018-2023), el valor real consistente es **0.35** — el valor viejo subestimaba la generación ~20-25% |
| Capacidad formal de recolección sobreestimada **~12 veces** (dividía un total ANUAL entre 30, no entre 365) | `abm/datos_reales.py` (encontrado y corregido en la sesión anterior, verificado de nuevo aquí) | La capacidad agregada de los 5 ASE pasó de 38,913 a ~3,339-4,900 ton/día reales — con el valor viejo, la restricción de capacidad nunca podía ser vinculante |
| 3 archivos RBL de 2020 descartados en silencio por un fallo del *sniffer* de CSV (encontrado en la sesión anterior) | `src/carga_datos.py` | La cobertura real de 2020 pasó de 155,088 a 616,761 ton/año al corregirlo |

**Verificación de que el ajuste del per-cápita no rompió nada:** se volvió a correr la calibración
completa (2018-2024, resolución completa) con el valor corregido. El resultado es **idéntico** al
que ya estaba documentado (17.35% → 18.29% en la trayectoria 2018-2024, RMSE≈1.07pp) — el ajuste
cambia las toneladas absolutas simuladas (ahora más realistas, ~6,790 ton/día en 2024 vs. el rango
real de 7,300-10,900), pero no el % de aprovechamiento, porque afecta al numerador y denominador
del balance de masa por igual. **No hizo falta recalibrar `factor_brecha_intencion_accion`.**
Como beneficio adicional, la capacidad formal usada subió de ~13% a un **18%** más realista (sigue
sin saturarse, pero ahora con más margen real, no un artefacto de una capacidad 12x inflada).

Se corrigieron también, por consistencia, dos columnas derivadas que quedaron con el valor viejo
horneado adentro (`ton_recolectadas_estim_dia`, `ton_aprovechadas_estim_dia` en `df_modelo.csv`,
`df_modelo.pkl` y `06_parametros_abm.csv`) — no las usa ningún código del `abm/`, pero mostraban
un número incorrecto si alguien abriera el CSV directamente.

### 1.3 Código y notebooks obsoletos, marcados o corregidos (no eliminados a ciegas)

- **`abm/visualizacion_mapa.py`**: tenía una función `graficar_mapa_infraestructura` con la
  etiqueta *"índice SINTÉTICO... no es dato real"* — desactualizada desde que se reemplazó por el
  índice real de SIGAB. Corregida la etiqueta y el docstring.
- **`notebooks/ABM_Simulacion_Residuos_Bogota.ipynb`**: es el notebook del MVP v1 original —
  compara contra el 48.5% ya descartado, dice "sin calibrar" y "calibración.py no creado aún"
  (ambos ya no son ciertos). Se le agregó un aviso explícito **"⚠️ SUPERADO"** al inicio,
  explicando qué cambió y remitiendo al dashboard como la forma correcta de correr el modelo hoy
  — no se reescribió el resto del notebook, para conservarlo como registro histórico honesto del
  primer corte del proyecto.
- **`src/validaciones.py`**: verificado que SÍ está en uso activo (5 invocaciones reales en el
  notebook de la Fase 1) — no es código muerto, se conserva sin cambios.

### 1.4 Una confusión de organización que vale la pena que sepas (no se movió nada, por seguridad)

El notebook que **regenera activamente** `data/processed/` (Fase 1: limpieza, features,
exportación) vive en `Backup y otros/Modelo_Residuos_Solidos_Bogota (2).ipynb` — un nombre de
carpeta que sugiere "archivo viejo, no tocar", cuando en realidad es la pieza más activa de todo
el pipeline de datos. No lo moví a `notebooks/` (donde viven los otros dos notebooks activos)
porque su celda de configuración asume que se ejecuta con el directorio de trabajo en la raíz del
proyecto (`Path.cwd()`, no `Path.cwd().parent`) — moverlo sin verificar cómo lo ejecutas
normalmente podría romperlo. Si quieres, en la próxima sesión lo reorganizamos con cuidado.

---

## 2. Estado real de cada componente (verificado hoy, no de memoria)

| Componente | Estado | Verificación hecha hoy |
|---|---|---|
| Fase 1 — limpieza y `df_modelo` | ✅ Completo | Columnas derivadas re-parcheadas con constantes corregidas |
| Fase 2 — fuentes externas | ✅ Completo | Sin cambios necesarios en esta ronda |
| Fase 3 — EDA dirigido (`EDA_Dirigido_Fase3.ipynb`) | ✅ Completo | JSON validado tras editar 3 celdas (61 celdas intactas) |
| Auditoría de datos/limpieza/EDA | ✅ Completo, purgado de Cerebro | Renumeración de secciones verificada |
| Reglas de negocio v2 | ✅ Completo, purgado de Cerebro | — |
| `src/` (7 módulos) | ✅ Importan sin error | `python -c "import ..."` sobre los 7 módulos |
| `abm/` (9 módulos) | ✅ Importan y corren sin error | Igual, más una corrida completa de 365 días |
| Calibración (`abm/calibracion.py`) | ✅ Completo y verificado | Re-confirmado a resolución completa tras el fix de per-cápita: resultado idéntico |
| Dashboard (`abm/dashboard.py`) | ✅ Corriendo | Reiniciado desde cero (estaba caído al empezar esta sesión), HTTP 200, log sin errores |

---

## 3. Cómo correr el dashboard (para tu presentación)

Desde la carpeta del proyecto, en una terminal:

```
../.venv/Scripts/solara run abm/dashboard.py --port 8765
```

Se abre en `http://localhost:8765`. Verificado corriendo ahora mismo (HTTP 200). Los controles
Play/Step/Reset avanzan la simulación día a día; todos los paneles (mapa real de Bogotá, KPIs,
series de tiempo, contrafactual 2024) se redibujan solos.

---

## 4. Lo que sigue abierto (honesto, no es parte de "arreglar lo que está mal")

Estos NO son errores — son huecos de dato o decisiones de alcance ya documentadas en detalle en
`Resultados_EDA_Funcionamiento_Bogota.md` §10 y `Reglas_Negocio_v2_y_Modelado_Agentes.md`:

- 4 de los 5 parámetros de comportamiento del ABM no son identificables con datos anuales
  agregados (confirmado empíricamente en la calibración).
- Capacidad individual de reciclador, rutas/camiones, capacidad remanente de Doña Juana: sin
  fuente de dato disponible en ningún lado.
- `escenarios.py` y `validaciones_abm.py` (post-MVP) no se han escrito — no estaban en el alcance
  de "hasta el dashboard".
- La redacción final de la tesis como documento (fuera del alcance de esta certificación).

---

## 5. Checklist final

- [x] Ninguna referencia activa a `Cerebro.xlsx` en código ni en los 6 documentos de trabajo.
- [x] Todo el código (`src/`, `abm/`) importa sin error.
- [x] El ABM corre un año completo sin error (365 días, ~75,000 agentes).
- [x] La calibración multi-año (2018-2024) fue reconfirmada después de los fixes de esta ronda.
- [x] El dashboard está corriendo y responde HTTP 200, sin errores en el log.
- [x] Los documentos `.md` activos no se contradicen entre sí ni citan el 48.5% como vigente.
- [x] Se documentó, sin esconder nada, lo que sigue pendiente.

**Con esto, el proyecto está en condiciones de presentarse al comité como el avance hasta el ABM
simulado y el dashboard en vivo.**
