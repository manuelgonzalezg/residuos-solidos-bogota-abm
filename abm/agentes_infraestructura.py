"""Infraestructura real de puntos críticos (SIGAB) y agentes Operador de aseo (ASE, con RBL).

Historial: en el MVP original (v1) el índice de infraestructura era una fórmula sintética
inventada, y `OperadorUAESP` un stub sin instanciar (ver `Diseno_ABM.md` §4). Desde la Fase 2/3
ambos tienen datos reales — ver `abm/datos_reales.py` y
`Reglas_Negocio_v2_y_Modelado_Agentes.md` §3.1 y §4quater. Esta versión reemplaza ambos supuestos.
"""
import mesa


class OperadorUAESP(mesa.Agent):
    """Un agente por ASE (5 en total — Promoambiental, LIME, Ciudad Limpia, Bogotá Limpia, Área
    Limpia; RPC Aguas de Bogotá se excluye por tener capacidad domiciliaria ~0 en el RBL), con
    capacidad diaria REAL (promedio histórico de toneladas/mes del RBL consolidado, ver
    `datos_reales.construir_o_cargar_capacidad_ase`).

    Simplificación deliberada (no se inventa lo que no se sabe): no existe ningún dato real que
    diga qué UPZ atiende cada ASE específicamente, así que estos 5 agentes NO reclaman material
    por UPZ individual — el modelo suma su capacidad total real y la aplica como un único techo
    agregado de ciudad al recolectar lo que los recicladores de oficio no alcanzaron (ver
    `ModeloResiduosBogota._recoleccion_formal`). Es una mejora real frente a "sin restricción"
    (v1), sin fingir una precisión geográfica que ningún dato sostiene.
    """

    def __init__(self, model, ase_nombre: str, capacidad_dia_ton: float):
        super().__init__(model)
        self.ase_nombre = ase_nombre
        self.capacidad_dia_ton = capacidad_dia_ton
        self.material_recolectado_acumulado = 0.0
