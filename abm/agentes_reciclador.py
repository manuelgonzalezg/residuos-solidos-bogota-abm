"""Agente Población de Recicladores de Oficio (uno por UPZ).

Opera mecanismo #2 de la hipótesis: compite sin coordinación por el material ya separado por
los hogares, junto con el sistema formal de recolección (ahora `OperadorUAESP`, con capacidad
real por ASE — ver `agentes_infraestructura.py` y `modelo.py`). Dato real disponible: conteo de
recicladores por localidad (RURO) — sin rutas ni ingresos, pero SÍ con dos indicadores reales de
formalización desde la Fase 2/3 (RURO 2022): `pct_registro_activo` (~90%, estar vigente en el
RURO) y `pct_formalizacion_laboral` (~0-14%, afiliación ARL) — son cosas DISTINTAS, no una sola
"formalización" (ver Reglas_Negocio_v2_y_Modelado_Agentes.md §3.6). De ahí que este agente siga
siendo una población agregada por UPZ, no individuos con movimiento — el dato sigue sin ser
individual, solo más rico que antes.
"""
import mesa

from . import config_abm


class PoblacionRecicladoresUPZ(mesa.Agent):
    def __init__(self, model, codigo_upz: int, n_recicladores_asignados: float,
                 edad_promedio_reciclador: float | None = None,
                 capacidad_recoleccion_individual: float | None = None,
                 pct_registro_activo: float = 90.0,
                 pct_formalizacion_laboral: float = 0.0):
        super().__init__(model)
        self.codigo_upz = codigo_upz
        self.n_recicladores_asignados = n_recicladores_asignados
        self.edad_promedio_reciclador = edad_promedio_reciclador

        # Dos indicadores de formalización REALES y DISTINTOS (RURO 2022, Fase 2/3) — no se
        # usan todavía para modular el comportamiento (ningún mecanismo del EDA lo sostiene con
        # evidencia causal clara), se exponen como atributos informativos/de reporte, listos
        # para una futura iteración de calibración que sí los use.
        self.pct_registro_activo = pct_registro_activo
        self.pct_formalizacion_laboral = pct_formalizacion_laboral

        # Parámetro libre (ver Diseno_ABM.md §6): configurable por corrida —p.ej. desde los
        # Sliders del dashboard— en vez de leerse siempre del módulo config_abm.
        self.capacidad_recoleccion_individual = (
            capacidad_recoleccion_individual
            if capacidad_recoleccion_individual is not None
            else config_abm.CAPACIDAD_RECOLECCION_KG_DIA_POR_RECICLADOR
        )

        # Modificador menor de eficiencia por edad promedio (supuesto simple: recicladores más
        # jóvenes ligeramente más productivos; único diferenciador real disponible en RURO).
        self.modificador_edad = 1.0
        if edad_promedio_reciclador is not None and edad_promedio_reciclador > 0:
            self.modificador_edad = max(0.7, min(1.1, 60.0 / edad_promedio_reciclador))

        self.material_recolectado_acumulado = 0.0

    @property
    def capacidad_total_dia_ton(self) -> float:
        """Capacidad diaria total en toneladas (parámetro libre por reciclador, sin valor real
        en `03_reglas_negocio.csv` — RN020-022 están "Pendiente")."""
        kg_dia = (
            self.n_recicladores_asignados
            * self.capacidad_recoleccion_individual
            * self.modificador_edad
        )
        return kg_dia / 1000.0

    def step(self):
        """Reclama del pool de material ya separado en su UPZ, hasta su capacidad."""
        entorno = self.model.entornos[self.codigo_upz]

        reclamado = min(self.capacidad_total_dia_ton, entorno.material_pool_disponible)
        entorno.material_pool_disponible -= reclamado
        entorno.material_aprovechado_dia += reclamado
        self.material_recolectado_acumulado += reclamado
