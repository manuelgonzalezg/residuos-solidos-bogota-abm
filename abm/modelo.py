"""Modelo principal del ABM (MVP): une entorno, hogares y recicladores, y corre un año completo.

Ver Diseno_ABM.md para el diseño completo. Este es el alcance del MVP (§7): sin calibración
formal, sin escenarios, sin validaciones automatizadas todavía — solo el modelo corriendo y
devolviendo un % de aprovechamiento agregado, para confirmar que la mecánica tiene sentido de
orden de magnitud antes de invertir en calibración.
"""
import sys
from collections import defaultdict
from pathlib import Path

import mesa
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src import config as config_datos  # noqa: E402

from . import agentes_infraestructura, agentes_hogar, agentes_reciclador, config_abm, datos_reales, entorno


ESTRATOS_CATEGORIA_COLUMNA = {
    "Baja": "pct_estrato_bajo",
    "Media": "pct_estrato_medio",
    "Alta": "pct_estrato_alto",
}


class ModeloResiduosBogota(mesa.Model):
    def __init__(self, anio: int = 2024, rng: int | None = None,
                 capacidad_recoleccion_individual: float | None = None,
                 beta_decaimiento: float | None = None,
                 beta_recuperacion: float | None = None,
                 umbral_percepcion_impacto: float | None = None,
                 factor_brecha_intencion_accion: float | None = None,
                 estado_previo_cohortes: dict | None = None,
                 multiplicador_infraestructura: float = 1.0,
                 multiplicador_capacidad_formal: float = 1.0):
        """Los 4 parámetros libres (ver Diseno_ABM.md §6) se pueden fijar por corrida —usados
        por los Sliders de `abm/dashboard.py`— en vez de tomarse siempre de `config_abm.py`.
        `None` (default) usa el valor de `config_abm.py` sin cambios.

        `estado_previo_cohortes`: dict {(codigo_upz, estrato_categoria): prob_separa_actual
        promedio} con el que terminó el año anterior de una simulación ENCADENADA multi-año
        (ver `abm/calibracion.py::correr_serie_anios`). Cuando se pasa, sustituye el
        `prob_separa` estático de la encuesta como base de los agentes de ese año — es lo que le
        da a la simulación multi-año una MEMORIA real de un año a otro, en vez de reiniciar cada
        año desde la misma foto fija de la encuesta (ver nota en `agentes_hogar.py` sobre por qué
        el mecanismo de imitación por sí solo, sin esta memoria, no puede producir una tendencia).

        `multiplicador_infraestructura`/`multiplicador_capacidad_formal`: controles de ESCENARIO
        (2026-07-13, panel "Escenarios y política" del dashboard) — escalan el índice de
        infraestructura real (SIGAB) y la capacidad formal real (RBL) respectivamente. Default
        1.0 = exactamente el dato real de hoy, sin intervención (idéntico a no pasar el
        parámetro). A diferencia de los parámetros de comportamiento de arriba, estos DOS ya
        modifican mecanismos causales verificados (`prob_efectiva` en `agentes_hogar.py` y el
        techo de `_recoleccion_formal()`), así que sí sirven para explorar "¿y si invertimos más
        en infraestructura/capacidad?" — no son un supuesto de comportamiento sin validar.
        """
        super().__init__(rng=rng if rng is not None else config_abm.SEMILLA_ALEATORIA)
        self.anio = anio
        self.dia_actual = 0
        self.capacidad_recoleccion_individual = capacidad_recoleccion_individual
        self.beta_decaimiento = beta_decaimiento
        self.beta_recuperacion = beta_recuperacion
        self.umbral_percepcion_impacto = umbral_percepcion_impacto
        self.factor_brecha_intencion_accion = factor_brecha_intencion_accion
        self.estado_previo_cohortes = estado_previo_cohortes or {}
        self.multiplicador_infraestructura = multiplicador_infraestructura
        self.multiplicador_capacidad_formal = multiplicador_capacidad_formal

        df_modelo = pd.read_csv(config_datos.DATA_PROCESSED / "df_modelo.csv")
        df_anio = df_modelo[df_modelo["AÑO"] == anio].reset_index(drop=True)
        if df_anio.empty:
            raise ValueError(f"No hay datos en df_modelo.csv para el año {anio}")

        codigos_upz = df_anio["UPZ"].astype(int).tolist()

        df_adyacencia = entorno.construir_o_cargar_adyacencia_upz()
        grafo = entorno.construir_grafo_upz(df_adyacencia, codigos_upz)
        self.grid = mesa.space.NetworkGrid(grafo)

        # --- Datos reales de Fase 2/3 (ver abm/datos_reales.py) — reemplazan supuestos del MVP v1 ---
        df_infraestructura_real = datos_reales.construir_o_cargar_infraestructura_real().set_index("UPZ")
        df_participacion = datos_reales.construir_o_cargar_participacion_comunitaria().set_index("codigo_localidad")
        df_formalizacion = datos_reales.construir_o_cargar_formalizacion_recicladores().set_index("codigo_localidad")
        df_capacidad_ase = datos_reales.construir_o_cargar_capacidad_ase()
        # Heterogeneidad real de hogar (ronda 4, 2026-07-14) — ver Justificacion_Metodologica_Comite.md
        df_perfil_hogar = datos_reales.construir_o_cargar_perfil_hogar_localidad().set_index("codigo_localidad")
        # Separación en la fuente REAL a nivel UPZ (ronda 5, 2026-07-14, EM2021 — reemplaza el
        # `prob_separa`/`pct_calidad_separacion` de `df_modelo.csv`, que era ECA2021 heredado de
        # localidad, con localidades sostenidas por 1-3 encuestas). Ver
        # Justificacion_Metodologica_Comite.md.
        df_separacion_upz = datos_reales.construir_o_cargar_separacion_upz_em2021()
        df_separacion_upz["UPZ"] = df_separacion_upz["UPZ"].astype(int)
        df_separacion_upz = df_separacion_upz.set_index("UPZ")

        # --- Variación REAL en el tiempo (2026-07-11): infraestructura y capacidad formal ya no
        # se blindan en un solo promedio 2018-2024 — cada año simulado toma su snapshot/cifra
        # real más cercana, para que la trayectoria multi-año tenga un motor de cambio real
        # respaldado en dato, no solo en parámetros de comportamiento libres. Ver
        # `Investigacion_Salto_Aprovechamiento.md` (decomposición shift-share) y
        # `abm/datos_reales.py` para el detalle de cobertura de cada fuente.
        df_infra_por_anio = datos_reales.construir_o_cargar_infraestructura_real_por_anio()
        anios_snapshot_disponibles = sorted(df_infra_por_anio["anio_snapshot"].unique())
        anio_snapshot_usado = datos_reales.snapshot_infraestructura_mas_cercano(anio, anios_snapshot_disponibles)
        df_infraestructura_anio = df_infra_por_anio[
            df_infra_por_anio["anio_snapshot"] == anio_snapshot_usado
        ].set_index("UPZ")

        df_capacidad_por_anio = datos_reales.construir_o_cargar_capacidad_ase_por_anio()
        fila_anio_capacidad = df_capacidad_por_anio[
            (df_capacidad_por_anio["anio"] == anio) & (df_capacidad_por_anio["confiable"])
        ]
        df_capacidad_ase_usada = fila_anio_capacidad if not fila_anio_capacidad.empty else df_capacidad_ase

        self.entornos: dict[int, entorno.EntornoUPZ] = {}

        # Asignar recicladores por localidad -> UPZ, proporcional a población (evita el doble
        # conteo de usar el total de la localidad tal cual en cada UPZ, ver Diseno_ABM.md §3).
        poblacion_por_localidad = df_anio.groupby("codigo_localidad")["Total"].transform("sum")
        participacion_poblacional = df_anio["Total"] / poblacion_por_localidad.replace(0, np.nan)

        for i, fila in df_anio.iterrows():
            codigo_upz = int(fila["UPZ"])
            codigo_localidad = fila.get("codigo_localidad")
            ent = entorno.EntornoUPZ(codigo_upz, fila)

            # Infraestructura REAL: snapshot SIGAB más cercano a `anio` (ya no el promedio de los
            # 4 cortes) — con fallback al promedio blended si esta UPZ faltara en ese snapshot.
            if codigo_upz in df_infraestructura_anio.index:
                ent.infraestructura_index = df_infraestructura_anio.loc[codigo_upz, "infraestructura_index_real"]
            elif codigo_upz in df_infraestructura_real.index:
                ent.infraestructura_index = df_infraestructura_real.loc[codigo_upz, "infraestructura_index_real"]
            else:
                ent.infraestructura_index = 0.7
            # Control de escenario (default 1.0 = dato real sin cambios, ver __init__): el índice
            # normalizado nunca puede superar 1.0 aunque el multiplicador sea > 1.
            ent.infraestructura_index = min(ent.infraestructura_index * self.multiplicador_infraestructura, 1.0)
            # Separación en la fuente REAL a nivel UPZ (ronda 5, EM2021, ver arriba) — reemplaza
            # `fila["prob_separa"]`/`fila["pct_calidad_separacion"]` de `df_modelo.csv` (ECA2021,
            # heredado de localidad). Fallback al valor legado de df_modelo.csv solo si la UPZ no
            # apareciera en la fuente nueva (no ocurre hoy: cobertura 112/112, se deja por
            # robustez, mismo patrón que el fallback de infraestructura arriba).
            if codigo_upz in df_separacion_upz.index:
                pct_separa_upz_real = df_separacion_upz.loc[codigo_upz, "pct_separa_upz"]
                pct_calidad_separacion_upz_real = df_separacion_upz.loc[codigo_upz, "pct_calidad_separacion_upz"]
            else:
                pct_separa_upz_real = (fila.get("prob_separa", 0.0) or 0.0) * 100.0
                pct_calidad_separacion_upz_real = fila.get("pct_calidad_separacion", 0.0) or 0.0
            # Incentivo económico REAL (VIAT + factor de subsidio CRA por composición de estrato).
            ent.factor_incentivo = datos_reales.factor_incentivo_upz(
                fila.get("pct_e1", 0.0), fila.get("pct_e2", 0.0), fila.get("pct_e3", 0.0),
                fila.get("pct_e4", 0.0), fila.get("pct_e5", 0.0), fila.get("pct_e6", 0.0),
            )
            # Participación comunitaria y formalización de recicladores, REALES, a nivel
            # localidad (Sumapaz, localidad 20, excluida — sin UPZ urbanas, ver src/config.py).
            if codigo_localidad in df_participacion.index and codigo_localidad != config_datos.LOCALIDAD_SUMAPAZ:
                ent.pct_participacion_comunitaria = df_participacion.loc[codigo_localidad, "pct_participacion_comunitaria"]
            if codigo_localidad in df_perfil_hogar.index and codigo_localidad != config_datos.LOCALIDAD_SUMAPAZ:
                ent.pct_vivienda_propia_localidad = df_perfil_hogar.loc[codigo_localidad, "pct_vivienda_propia"]
                ent.pct_informal_localidad = df_perfil_hogar.loc[codigo_localidad, "pct_informal"]
            if codigo_localidad in df_formalizacion.index:
                ent.pct_registro_activo_reciclador = df_formalizacion.loc[codigo_localidad, "pct_registro_activo"]
                ent.pct_formalizacion_laboral_reciclador = df_formalizacion.loc[codigo_localidad, "pct_formalizacion_laboral"]

            participacion = participacion_poblacional.iloc[i]
            participacion = 0.0 if pd.isna(participacion) else participacion
            ent.num_recicladores_asignados = fila.get("num_recicladores_ruro", 0.0) * participacion

            self.entornos[codigo_upz] = ent

            poblacion_reciclador = agentes_reciclador.PoblacionRecicladoresUPZ(
                self, codigo_upz, ent.num_recicladores_asignados,
                edad_promedio_reciclador=None,
                capacidad_recoleccion_individual=self.capacidad_recoleccion_individual,
                pct_registro_activo=ent.pct_registro_activo_reciclador,
                pct_formalizacion_laboral=ent.pct_formalizacion_laboral_reciclador,
            )
            self.grid.place_agent(poblacion_reciclador, codigo_upz)

            for estrato_categoria, columna_pct in ESTRATOS_CATEGORIA_COLUMNA.items():
                pct = fila.get(columna_pct, 0.0) or 0.0
                hogares_categoria = fila.get("HOGARES", 0.0) * (pct / 100.0)
                poblacion_categoria = fila.get("Total", 0.0) * (pct / 100.0)
                if hogares_categoria <= 0:
                    continue

                n_agentes = max(
                    config_abm.MIN_AGENTES_HOGAR_POR_CELDA,
                    round(hogares_categoria * config_abm.FRACCION_MUESTREO_HOGARES),
                )
                poblacion_por_agente = poblacion_categoria / n_agentes

                clave_cohorte = (codigo_upz, estrato_categoria)
                if clave_cohorte in self.estado_previo_cohortes:
                    # Estado encadenado de un año anterior: ya refleja comportamiento simulado,
                    # NO se le vuelve a aplicar la brecha intención-acción (eso la compondría
                    # cada año — ver nota en agentes_hogar.py).
                    prob_separa_base_cohorte = self.estado_previo_cohortes[clave_cohorte]
                else:
                    factor_brecha = (
                        self.factor_brecha_intencion_accion if self.factor_brecha_intencion_accion is not None
                        else config_abm.FACTOR_BRECHA_INTENCION_ACCION
                    )
                    prob_separa_base_cohorte = (pct_separa_upz_real / 100.0) * factor_brecha

                agentes_cohorte = []
                for _ in range(n_agentes):
                    hogar = agentes_hogar.HogarAgente(
                        self,
                        codigo_upz=codigo_upz,
                        estrato_categoria=estrato_categoria,
                        poblacion_representada=poblacion_por_agente,
                        prob_separa_base=prob_separa_base_cohorte,
                        pct_calidad_separacion=pct_calidad_separacion_upz_real,
                        pct_participacion_comunitaria_localidad=ent.pct_participacion_comunitaria,
                        pct_vivienda_propia_localidad=ent.pct_vivienda_propia_localidad,
                        pct_informal_localidad=ent.pct_informal_localidad,
                        beta_decaimiento=self.beta_decaimiento,
                        beta_recuperacion=self.beta_recuperacion,
                        umbral_percepcion_impacto=self.umbral_percepcion_impacto,
                        factor_brecha_intencion_accion=self.factor_brecha_intencion_accion,
                    )
                    self.grid.place_agent(hogar, codigo_upz)
                    agentes_cohorte.append(hogar)

                # Añade heterogeneidad real (vivienda/informalidad) en la salida diaria sin mover
                # el promedio agregado de la cohorte — ver docstring de la función y la nota en
                # HogarAgente.__init__ sobre por qué NO se aplica a prob_separa_base.
                agentes_hogar.normalizar_factor_heterogeneidad(agentes_cohorte)

        # --- Operadores de aseo (ASE) — 5 agentes con capacidad diaria REAL (RBL consolidado) ---
        # Ver agentes_infraestructura.OperadorUAESP: no hay dato real de qué UPZ atiende cada
        # ASE, así que se usa la capacidad SUMADA como techo agregado de ciudad (§4quater).
        self.operadores_ase = []
        for _, fila_ase in df_capacidad_ase_usada.iterrows():
            if fila_ase["capacidad_dia_ton"] <= 0:
                continue  # excluye RPC Aguas de Bogotá (~0 ton/día domiciliario en el RBL)
            # Control de escenario (default 1.0 = dato real sin cambios, ver __init__).
            capacidad_escenario = fila_ase["capacidad_dia_ton"] * self.multiplicador_capacidad_formal
            operador = agentes_infraestructura.OperadorUAESP(self, fila_ase["ase"], capacidad_escenario)
            self.operadores_ase.append(operador)
        self.capacidad_formal_total_dia_ton = sum(op.capacidad_dia_ton for op in self.operadores_ase)
        self._ultimo_recolectado_formal_dia = 0.0

        # Agrupación estática (los hogares no se mueven) para que la actualización de actitudes
        # sea O(n) por ciclo en vez de O(n²) — cada agente NO recorre la red por su cuenta.
        self.hogares_por_upz_estrato: dict[tuple[int, str], list] = defaultdict(list)
        for hogar in self.agents_by_type[agentes_hogar.HogarAgente]:
            self.hogares_por_upz_estrato[(hogar.codigo_upz, hogar.estrato_categoria)].append(hogar)

        self.datacollector = mesa.DataCollector(
            model_reporters={
                "generado_dia_ton": lambda m: sum(e.material_generado_dia for e in m.entornos.values()),
                "aprovechado_dia_ton": lambda m: sum(e.material_aprovechado_dia for e in m.entornos.values()),
                "rechazo_dia_ton": lambda m: sum(e.material_rechazo_dia for e in m.entornos.values()),
                "pct_aprovechamiento_dia": lambda m: m._pct_aprovechamiento_dia(),
                "pct_aprovechamiento_acumulado_ciudad": lambda m: m._pct_aprovechamiento_acumulado_ciudad(),
                "capacidad_formal_usada_pct": lambda m: m._pct_capacidad_formal_usada(),
                "material_recolectado_recicladores_dia_ton": lambda m: sum(
                    a.capacidad_total_dia_ton for a in m.agents_by_type[agentes_reciclador.PoblacionRecicladoresUPZ]
                ),
            }
        )

    def _pct_aprovechamiento_dia(self) -> float:
        """Ratio de SOLO el día actual (generado hoy / aprovechado hoy) — NO es acumulado, se
        recalcula desde cero cada día. Útil para ver el flujo del día, no la tendencia del año."""
        generado = sum(e.material_generado_dia for e in self.entornos.values())
        aprovechado = sum(e.material_aprovechado_dia for e in self.entornos.values())
        return (aprovechado / generado * 100.0) if generado > 0 else 0.0

    def _pct_aprovechamiento_acumulado_ciudad(self) -> float:
        """% de aprovechamiento ACUMULADO de ciudad completa desde el día 0 hasta hoy — el
        número que responde "¿cómo va el año?", distinto de `_pct_aprovechamiento_dia` (que solo
        mide el día actual). Mismo cálculo que cada fila de `resumen_por_upz()`, pero agregado."""
        generado = sum(e.acumulado_generado for e in self.entornos.values())
        aprovechado = sum(e.acumulado_aprovechado for e in self.entornos.values())
        return (aprovechado / generado * 100.0) if generado > 0 else 0.0

    def _pct_capacidad_formal_usada(self) -> float:
        if self.capacidad_formal_total_dia_ton <= 0:
            return 0.0
        return min(self._ultimo_recolectado_formal_dia / self.capacidad_formal_total_dia_ton * 100.0, 100.0)

    def _recoleccion_formal(self):
        """El sistema formal de recolección (5 agentes `OperadorUAESP`, capacidad diaria REAL
        del RBL consolidado — ver `agentes_infraestructura.py`) recoge lo que quede en el pool
        de material separado que los recicladores de oficio no alcanzaron a recolectar, hasta su
        capacidad conjunta real (`capacidad_formal_total_dia_ton`) — ya NO "sin restricción" como
        en el MVP v1. En la práctica esta capacidad rara vez se satura (evidencia real del EDA:
        el RBL nunca muestra señales de saturación en 8 años), así que el comportamiento
        agregado cambia poco frente a v1, pero ahora es una restricción verificable, no un
        supuesto. La competencia sin coordinación del mecanismo #2 se refleja en CÓMO se reparte
        el material recuperado entre recicladores informales y sistema formal, no en si se
        recupera o no.
        """
        pool_total_restante = sum(ent.material_pool_disponible for ent in self.entornos.values())
        recolectado_formal = min(pool_total_restante, self.capacidad_formal_total_dia_ton)
        self._ultimo_recolectado_formal_dia = recolectado_formal

        # Reparto proporcional del techo agregado entre UPZ, según cuánto material le quedó a
        # cada una en su propio pool (ninguna UPZ se queda sin atender por el orden de recorrido).
        for ent in self.entornos.values():
            if pool_total_restante <= 0:
                continue
            proporcion = ent.material_pool_disponible / pool_total_restante
            recolectado_upz = recolectado_formal * proporcion
            ent.material_aprovechado_dia += recolectado_upz
            ent.material_pool_disponible -= recolectado_upz

        for operador in self.operadores_ase:
            operador.material_recolectado_acumulado += (
                recolectado_formal * (operador.capacidad_dia_ton / self.capacidad_formal_total_dia_ton)
                if self.capacidad_formal_total_dia_ton > 0 else 0.0
            )

    def _actualizar_actitudes_hogares(self):
        """Efecto de imitación/free-riding (mecanismo #1), calculado en dos pasadas O(n) en
        vez de que cada agente recorra la red por su cuenta (con miles de agentes, hacerlo por
        agente es demasiado lento — ver Diseno_ABM.md §3 y el comentario en `agentes_hogar.py`).
        """
        promedio_local: dict[tuple[int, str], float] = {}
        for clave, agentes in self.hogares_por_upz_estrato.items():
            promedio_local[clave] = sum(a.prob_separa_actual for a in agentes) / len(agentes)

        for (codigo_upz, estrato), agentes in self.hogares_por_upz_estrato.items():
            vecinos_upz = [codigo_upz] + list(self.grid.G.neighbors(codigo_upz))
            valores_vecinos = [
                promedio_local[(v, estrato)] for v in vecinos_upz if (v, estrato) in promedio_local
            ]
            if not valores_vecinos:
                continue
            promedio_vecinos = sum(valores_vecinos) / len(valores_vecinos)
            for agente in agentes:
                agente.actualizar_actitud_separacion(promedio_vecinos)

    def step(self):
        for ent in self.entornos.values():
            ent.reiniciar_paso_diario()

        self.agents_by_type[agentes_hogar.HogarAgente].shuffle_do("step")
        self.agents_by_type[agentes_reciclador.PoblacionRecicladoresUPZ].shuffle_do("step")

        self._recoleccion_formal()

        for ent in self.entornos.values():
            material_no_separado = ent.material_generado_dia - ent.material_aprovechado_dia
            ent.material_rechazo_dia = max(material_no_separado, 0.0)
            ent.cerrar_paso_diario()

        self.datacollector.collect(self)
        self.dia_actual += 1
        # Tope real de un año simulado: `df_modelo` da insumos fijos por año (sin rollover
        # automático a 2025+), así que seguir corriendo Play más allá del día 365 solo repetiría
        # el mismo año — `self.running` es el mecanismo NATIVO de Mesa que `ModelController` ya
        # respeta (deshabilita Play/Step solo) — ver `abm/dashboard.py`.
        self.running = self.dia_actual < config_abm.DIAS_POR_ANIO

        if self.dia_actual % config_abm.CADA_CUANTOS_DIAS_ACTUALIZA_ACTITUD == 0:
            self._actualizar_actitudes_hogares()

    def correr_anio(self, dias: int | None = None) -> pd.DataFrame:
        dias = dias or config_abm.DIAS_POR_ANIO
        for _ in range(dias):
            self.step()
        return self.datacollector.get_model_vars_dataframe()

    def estado_final_por_cohorte(self) -> dict:
        """Promedio de `prob_separa_actual` por (UPZ, categoría de estrato) al cierre de la
        corrida — la "memoria" que se pasa como `estado_previo_cohortes` al modelo del año
        siguiente en una simulación encadenada (ver `abm/calibracion.py::correr_serie_anios`).

        Ponderado por `poblacion_representada` (corregido 2026-07-14, mismo criterio que
        `agentes_hogar.normalizar_factor_heterogeneidad`) — antes de la heterogeneidad real de la
        ronda 4, todos los agentes de una cohorte pesaban casi lo mismo y el promedio simple era
        una aproximación razonable; con heterogeneidad real entre agentes, promediar sin ponderar
        sesgaría el estado encadenado hacia cohortes con más agentes muestreados, no hacia la
        población real que representan.
        """
        resultado = {}
        for clave, agentes in self.hogares_por_upz_estrato.items():
            if not agentes:
                continue
            peso_total = sum(a.poblacion_representada for a in agentes)
            if peso_total <= 0:
                resultado[clave] = sum(a.prob_separa_actual for a in agentes) / len(agentes)
            else:
                resultado[clave] = sum(
                    a.prob_separa_actual * a.poblacion_representada for a in agentes
                ) / peso_total
        return resultado

    def pct_aprovechamiento_anual(self) -> float:
        """% de aprovechamiento acumulado de TODO lo corrido hasta ahora (no solo el día actual)
        — el KPI de reconciliación anual, Σaprovechado/Σgenerado (ver Diseno_ABM.md §5)."""
        generado = sum(e.acumulado_generado for e in self.entornos.values())
        aprovechado = sum(e.acumulado_aprovechado for e in self.entornos.values())
        return (aprovechado / generado * 100.0) if generado > 0 else 0.0

    def resumen_por_upz(self) -> pd.DataFrame:
        filas = []
        for codigo_upz, ent in self.entornos.items():
            pct = (
                ent.acumulado_aprovechado / ent.acumulado_generado * 100.0
                if ent.acumulado_generado > 0 else 0.0
            )
            filas.append({
                "UPZ": codigo_upz,
                "codigo_localidad": ent.codigo_localidad,
                "nombre_localidad": ent.nombre_localidad,
                "clasificacion_social": ent.clasificacion_social,
                "infraestructura_index": ent.infraestructura_index,
                "factor_incentivo": ent.factor_incentivo,
                "pct_participacion_comunitaria": ent.pct_participacion_comunitaria,
                "pct_registro_activo_reciclador": ent.pct_registro_activo_reciclador,
                "pct_formalizacion_laboral_reciclador": ent.pct_formalizacion_laboral_reciclador,
                "pct_estrato_bajo": ent.pct_estrato_bajo,
                "pct_estrato_medio": ent.pct_estrato_medio,
                "pct_estrato_alto": ent.pct_estrato_alto,
                "hogares_reales": ent.hogares_reales,
                "generado_acumulado_ton": ent.acumulado_generado,
                "aprovechado_acumulado_ton": ent.acumulado_aprovechado,
                "rechazo_acumulado_ton": ent.acumulado_rechazo,
                "pct_aprovechamiento": pct,
            })
        return pd.DataFrame(filas)
