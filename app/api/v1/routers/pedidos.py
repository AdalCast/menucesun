from typing import List
from fastapi import APIRouter, Depends, HTTPException
from api.v1.schemas.pedido import CrearPedidoIn, PedidoOut
from services.pedido_saga_service import PedidoSagaService
from core.dependencies import get_pedido_saga_service

router = APIRouter(prefix="/pedidos", tags=["pedidos-saga"])


@router.post("/", status_code=201, summary="Crear pedido con patrón Saga")
async def crear_pedido(
    pedido_data: CrearPedidoIn,
    pedido_service: PedidoSagaService = Depends(get_pedido_saga_service)
):
    """
    Crea un pedido usando el **Patrón Saga Orquestado**.
    
    ## Proceso:
    1. **Validar productos** - Verifica existencia y disponibilidad
    2. **Reservar inventario** - Bloquea stock temporalmente
    3. **Crear pedido** - Genera el pedido con cálculo de total
    4. **Confirmar pedido** - Confirma la transacción
    
    ## Compensaciones:
    Si cualquier paso falla, se ejecutan las compensaciones en orden inverso:
    - Liberar inventario reservado
    - Eliminar pedido creado
    - Cancelar confirmación
    
    Esto garantiza **consistencia eventual** sin transacciones distribuidas.
    """
    items_data = [
        {"producto_id": item.producto_id, "cantidad": item.cantidad}
        for item in pedido_data.items
    ]
    
    resultado = await pedido_service.crear_pedido_saga(
        cliente=pedido_data.cliente,
        items_data=items_data
    )
    
    if not resultado['exito']:
        raise HTTPException(
            status_code=400,
            detail={
                "mensaje": resultado.get('mensaje', 'Error al crear pedido'),
                "saga": resultado['saga_estado']
            }
        )
    
    return {
        "mensaje": "Pedido creado exitosamente",
        "pedido": resultado['pedido'],
        "saga": resultado['saga_estado']
    }


@router.get("/", response_model=List[PedidoOut], summary="Listar pedidos")
async def listar_pedidos(
    pedido_service: PedidoSagaService = Depends(get_pedido_saga_service)
):
    """Lista todos los pedidos creados"""
    pedidos = pedido_service.obtener_pedidos()
    return pedidos


@router.get("/{pedido_id}", response_model=PedidoOut, summary="Obtener pedido")
async def obtener_pedido(
    pedido_id: int,
    pedido_service: PedidoSagaService = Depends(get_pedido_saga_service)
):
    """Obtiene un pedido específico por ID"""
    pedido = pedido_service.obtener_pedido_por_id(pedido_id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return pedido


@router.get("/inventario/reservas", summary="Ver reservas de inventario")
async def obtener_reservas(
    pedido_service: PedidoSagaService = Depends(get_pedido_saga_service)
):
    """
    Muestra el estado actual de las reservas de inventario.
    Útil para debugging del patrón Saga.
    """
    reservas = pedido_service.obtener_reservas()
    return {
        "reservas": [
            {"producto_id": pid, "cantidad_reservada": cant}
            for pid, cant in reservas.items()
        ]
    }
