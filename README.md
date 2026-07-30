# Sistema de Gestión de Residuos Sólidos de Bogotá — EDA + Modelo Basado en Agentes (ABM)

> 🚧 **En construcción:** el código y los materiales de este proyecto se están publicando desde la carpeta de trabajo original. La estructura descrita abajo es la del proyecto completo.


Análisis de datos y **simulación basada en agentes** del sistema de generación y recolección de residuos sólidos de Bogotá, usando datos abiertos oficiales (SIGAB / observatorio ambiental). El proyecto combina un análisis exploratorio de la generación de residuos por localidad con un **modelo basado en agentes (Agent-Based Model)** que simula el comportamiento del sistema.

> **Por qué me importa este proyecto:** los sistemas de residuos urbanos son un ejemplo clásico de **sistema complejo** — muchos actores (generadores, recolectores, localidades) cuyas interacciones producen un comportamiento global que no se explica mirando las partes por separado. Modelarlo con agentes es la metodología central de las ciencias de la complejidad, y es la dirección en la que quiero seguir creciendo.

## Componentes

1. **Análisis exploratorio (EDA)** — Generación de residuos por localidad, cruces con variables culturales y de comportamiento, e identificación de patrones y grandes generadores a partir de los datos del SIGAB.
2. **Modelo Basado en Agentes (ABM)** — Simulación de agentes (generadores/localidades) y su interacción con el sistema de recolección, para explorar escenarios y comportamiento emergente.
3. **Dashboard** — Visualización interactiva de resultados (ejecutable vía `ejecutar_dashboard`).

## Estructura del repositorio

```
residuos-solidos-bogota-abm/
├── notebooks/        # Análisis exploratorio y preparación de datos
├── src/              # Código fuente del análisis y utilidades
├── abm/              # Modelo basado en agentes
├── data/             # Datos abiertos (muestras pequeñas; los grandes se excluyen)
├── requirements.txt
└── README.md
```

## Datos

Fuente: datos abiertos del **Sistema de Información para la Gestión de Residuos (SIGAB)** y del observatorio ambiental de Bogotá. Son datos **públicos**, sin información personal. Los archivos más pesados se excluyen del repositorio (ver `.gitignore`) y se documenta cómo descargarlos.

## Tecnologías

`Python` · `pandas` · `Mesa` (modelado basado en agentes) · `Streamlit` (dashboard) · `matplotlib` / `seaborn` · `GeoPandas`

## Estado

Proyecto académico desarrollado en la Especialización en Analítica de Datos (CUN), 2026. Incluye un MVP funcional con dashboard.

---
*Autor: Manuel Alejandro González Gallego.*

<!-- COMO_COMPLETAR: copia aquí las carpetas src/, abm/, notebooks/ y data/ (muestras pequeñas) desde tu carpeta de Drive "EDA + ABM Residuos Bogota". NO subas el archivo .env de esa carpeta: contiene claves. Ya está excluido en .gitignore por si acaso. -->
