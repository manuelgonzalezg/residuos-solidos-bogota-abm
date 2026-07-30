# Sistema de Gestión de Residuos Sólidos de Bogotá — EDA + Modelo Basado en Agentes (ABM)

Análisis de datos y **simulación basada en agentes (Agent-Based Model)** del sistema de generación y recolección de residuos sólidos de Bogotá, usando datos abiertos oficiales (SIGAB / observatorio ambiental). Combina un análisis exploratorio de la generación de residuos por localidad con un modelo de agentes implementado tanto en **Python** como en **NetLogo**.

> **Por qué me importa este proyecto:** los sistemas de residuos urbanos son un ejemplo clásico de **sistema complejo** — muchos actores (hogares, recicladores, operadores de aseo, localidades) cuyas interacciones producen un comportamiento global que no se explica mirando las partes por separado. Modelarlo con agentes es la metodología central de las ciencias de la complejidad, y es la dirección en la que quiero seguir creciendo.

## Componentes

1. **Análisis exploratorio (EDA)** — Generación de residuos por localidad, cruces con variables culturales y de comportamiento, e identificación de patrones y grandes generadores a partir de los datos del SIGAB.
2. **Modelo Basado en Agentes en Python** — Agentes de hogar, reciclador e infraestructura (operadores de aseo) que interactúan en un entorno; incluye calibración y visualización en mapa.
3. **Modelo en NetLogo** — Reimplementación del modelo en NetLogo con su interfaz, para simulación visual e interactiva sobre las UPZ de Bogotá.

## Estructura del repositorio

```
residuos-solidos-bogota-abm/
├── abm/                       # Modelo basado en agentes (Python)
│   ├── agentes_hogar.py
│   ├── agentes_reciclador.py
│   ├── agentes_infraestructura.py
│   ├── entorno.py
│   ├── modelo.py
│   ├── config_abm.py
│   ├── calibracion.py
│   ├── datos_reales.py
│   ├── visualizacion_mapa.py
│   └── netlogo/               # Modelo equivalente en NetLogo
│       ├── residuos_bogota.nlogox
│       ├── codigo_modelo.nls
│       ├── GUIA_INTERFAZ.md
│       └── datos/             # Insumos del modelo (UPZ, ASE, adyacencia)
├── src/                       # Pipeline de datos: carga, limpieza, features, EDA
├── notebooks/                 # EDA dirigido y simulación del ABM
│   ├── EDA_Dirigido_Fase3.ipynb
│   └── ABM_Simulacion_Residuos_Bogota.ipynb
├── requirements.txt
└── README.md
```

## Tecnologías

`Python` · `Mesa` (agentes) · `pandas` · `NetLogo` · `GeoPandas` · `matplotlib` / `seaborn` · `Jupyter`

## Datos

Fuente: datos abiertos del **Sistema de Información para la Gestión de Residuos (SIGAB)** y del observatorio ambiental de Bogotá. Son datos **públicos**, sin información personal. Los datasets más pesados no se incluyen en el repositorio; el código documenta cómo obtenerlos.

## Cómo explorar

- El modelo en **NetLogo** se abre con el archivo `abm/netlogo/residuos_bogota.nlogox` (ver `GUIA_INTERFAZ.md`).
- El modelo en **Python** vive en `abm/`; los notebooks en `notebooks/` muestran el EDA y la simulación.

---
*Autor: Manuel Alejandro González Gallego — Especialización en Analítica de Datos (CUN), 2026.*
