from dataclasses import dataclass
from typing import List, Optional
from decimal import Decimal
from enum import Enum


class EstadoPedido(str, Enum):
    PENDIENTE = "pendiente"
    CONFIRMADO = "confirmado"
    CANCELADO = "cancelado"
    FALLIDO = "fallido"


class EstadoSaga(str, Enum):
    INICIADA = "iniciada"
    EN_PROGRESO = "en_progreso"
    COMPLETADA = "completada"
    COMPENSANDO = "compensando"
    COMPENSADA = "compensada"
    FALLIDA = "fallida"


@dataclass
class ItemPedido:
    producto_id: int
    cantidad: int
    precio_unitario: Decimal
    nombre: str
    
    @property
    def subtotal(self) -> Decimal:
        return self.precio_unitario * self.cantidad


@dataclass
class Pedido:
    id: int
    items: List[ItemPedido]
    total: Decimal
    estado: EstadoPedido
    cliente: str
    
    def __init__(self, id: int, items: List[ItemPedido], cliente: str):
        self.id = id
        self.items = items
        self.cliente = cliente
        self.total = sum(item.subtotal for item in items)
        self.estado = EstadoPedido.PENDIENTE


@dataclass
class SagaStep:
    nombre: str
    ejecutado: bool = False
    compensado: bool = False
    datos_compensacion: Optional[dict] = None
