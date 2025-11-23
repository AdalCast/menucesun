from pydantic import BaseModel, Field
from typing import List
from decimal import Decimal


class ItemPedidoIn(BaseModel):
    producto_id: int = Field(..., gt=0, description="ID del producto")
    cantidad: int = Field(..., gt=0, description="Cantidad a pedir")


class CrearPedidoIn(BaseModel):
    cliente: str = Field(..., min_length=1, description="Nombre del cliente")
    items: List[ItemPedidoIn] = Field(..., min_items=1, description="Items del pedido")


class ItemPedidoOut(BaseModel):
    producto_id: int
    nombre: str
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal


class PedidoOut(BaseModel):
    id: int
    cliente: str
    items: List[ItemPedidoOut]
    total: Decimal
    estado: str
