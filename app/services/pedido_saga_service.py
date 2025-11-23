from typing import List, Dict, Any
from decimal import Decimal
import logging
from domain.saga_models import Pedido, ItemPedido, EstadoPedido
from domain.models import Producto
from repositories.interfaces import IProductoRepository
from services.saga_orchestrator import SagaOrchestrator

logger = logging.getLogger(__name__)


class PedidoSagaService:
    """
    Servicio de Pedidos usando Patrón Saga Orquestado
    
    Gestiona la creación de pedidos con validación de inventario,
    reserva de productos y confirmación, con rollback automático.
    """
    
    def __init__(self, producto_repo: IProductoRepository):
        self.producto_repo = producto_repo
        self._pedidos: List[Pedido] = []
        self._siguiente_id = 1
        # Simulación de inventario reservado
        self._reservas: Dict[int, int] = {}  # producto_id -> cantidad_reservada
    
    async def crear_pedido_saga(
        self,
        cliente: str,
        items_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Crea un pedido usando el patrón Saga.
        
        Pasos:
        1. Validar productos disponibles
        2. Reservar productos
        3. Calcular total
        4. Confirmar pedido
        
        Si cualquier paso falla, se ejecutan las compensaciones.
        """
        
        # Crear orquestador de saga
        saga = SagaOrchestrator(nombre=f"CrearPedido-{self._siguiente_id}")
        
        # Contexto compartido entre steps
        saga.contexto['cliente'] = cliente
        saga.contexto['items_data'] = items_data
        saga.contexto['pedido_service'] = self
        
        # Step 1: Validar productos
        saga.agregar_step(
            nombre="ValidarProductos",
            accion=self._validar_productos,
            compensacion=self._compensar_validacion
        )
        
        # Step 2: Reservar inventario
        saga.agregar_step(
            nombre="ReservarInventario",
            accion=self._reservar_inventario,
            compensacion=self._compensar_reserva
        )
        
        # Step 3: Calcular total y crear pedido
        saga.agregar_step(
            nombre="CrearPedido",
            accion=self._crear_pedido,
            compensacion=self._compensar_pedido
        )
        
        # Step 4: Confirmar pedido
        saga.agregar_step(
            nombre="ConfirmarPedido",
            accion=self._confirmar_pedido,
            compensacion=self._compensar_confirmacion
        )
        
        # Ejecutar saga
        exito = await saga.ejecutar()
        
        resultado = {
            "exito": exito,
            "saga_estado": saga.obtener_estado()
        }
        
        if exito:
            pedido = saga.contexto.get('pedido')
            resultado['pedido'] = {
                "id": pedido.id,
                "cliente": pedido.cliente,
                "items": [
                    {
                        "producto_id": item.producto_id,
                        "nombre": item.nombre,
                        "cantidad": item.cantidad,
                        "precio_unitario": float(item.precio_unitario),
                        "subtotal": float(item.subtotal)
                    }
                    for item in pedido.items
                ],
                "total": float(pedido.total),
                "estado": pedido.estado.value
            }
        else:
            resultado['mensaje'] = "El pedido no pudo ser creado. Se han revertido todos los cambios."
        
        return resultado
    
    # ========== ACCIONES DE LA SAGA ==========
    
    async def _validar_productos(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        """Step 1: Validar que los productos existan y estén disponibles"""
        logger.info("🔍 Validando productos...")
        
        items_data = contexto['items_data']
        productos_validados = []
        
        for item_data in items_data:
            producto_id = item_data['producto_id']
            cantidad = item_data['cantidad']
            
            producto = self.producto_repo.obtener_por_id(producto_id)
            
            if not producto:
                raise ValueError(f"Producto {producto_id} no encontrado")
            
            if not producto.disponible:
                raise ValueError(f"Producto {producto.nombre} no está disponible")
            
            if cantidad <= 0:
                raise ValueError(f"Cantidad inválida para {producto.nombre}")
            
            productos_validados.append({
                'producto': producto,
                'cantidad': cantidad
            })
        
        contexto['productos_validados'] = productos_validados
        logger.info(f"✅ {len(productos_validados)} productos validados")
        
        return {'productos_validados': len(productos_validados)}
    
    async def _reservar_inventario(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        """Step 2: Reservar inventario de productos"""
        logger.info("🔒 Reservando inventario...")
        
        productos_validados = contexto['productos_validados']
        reservas_realizadas = []
        
        for item in productos_validados:
            producto_id = item['producto'].id
            cantidad = item['cantidad']
            
            # Simular reserva de inventario
            if producto_id not in self._reservas:
                self._reservas[producto_id] = 0
            
            self._reservas[producto_id] += cantidad
            reservas_realizadas.append({
                'producto_id': producto_id,
                'cantidad': cantidad
            })
            
            logger.info(f"  📦 Reservados {cantidad} de producto {producto_id}")
        
        contexto['reservas'] = reservas_realizadas
        logger.info(f"✅ {len(reservas_realizadas)} reservas realizadas")
        
        return {'reservas': reservas_realizadas}
    
    async def _crear_pedido(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        """Step 3: Crear el pedido con los items"""
        logger.info("📝 Creando pedido...")
        
        productos_validados = contexto['productos_validados']
        cliente = contexto['cliente']
        
        items = [
            ItemPedido(
                producto_id=item['producto'].id,
                cantidad=item['cantidad'],
                precio_unitario=item['producto'].precio,
                nombre=item['producto'].nombre
            )
            for item in productos_validados
        ]
        
        pedido = Pedido(
            id=self._siguiente_id,
            items=items,
            cliente=cliente
        )
        
        self._pedidos.append(pedido)
        self._siguiente_id += 1
        
        contexto['pedido'] = pedido
        logger.info(f"✅ Pedido #{pedido.id} creado - Total: ${pedido.total}")
        
        return {'pedido_id': pedido.id}
    
    async def _confirmar_pedido(self, contexto: Dict[str, Any]) -> Dict[str, Any]:
        """Step 4: Confirmar el pedido"""
        logger.info("✅ Confirmando pedido...")
        
        pedido = contexto['pedido']
        pedido.estado = EstadoPedido.CONFIRMADO
        
        logger.info(f"🎉 Pedido #{pedido.id} confirmado exitosamente")
        
        return {'confirmado': True}
    
    # ========== COMPENSACIONES ==========
    
    async def _compensar_validacion(self, contexto: Dict[str, Any], datos: Dict[str, Any]):
        """Compensación: No hay nada que revertir en la validación"""
        logger.info("↩️  Compensando validación (sin cambios)")
    
    async def _compensar_reserva(self, contexto: Dict[str, Any], datos: Dict[str, Any]):
        """Compensación: Liberar inventario reservado"""
        logger.info("↩️  Liberando reservas de inventario...")
        
        reservas = datos.get('reservas', [])
        for reserva in reservas:
            producto_id = reserva['producto_id']
            cantidad = reserva['cantidad']
            
            if producto_id in self._reservas:
                self._reservas[producto_id] -= cantidad
                if self._reservas[producto_id] <= 0:
                    del self._reservas[producto_id]
                
                logger.info(f"  ✅ Liberados {cantidad} de producto {producto_id}")
    
    async def _compensar_pedido(self, contexto: Dict[str, Any], datos: Dict[str, Any]):
        """Compensación: Eliminar pedido creado"""
        logger.info("↩️  Eliminando pedido creado...")
        
        pedido_id = datos.get('pedido_id')
        self._pedidos = [p for p in self._pedidos if p.id != pedido_id]
        
        logger.info(f"  ✅ Pedido #{pedido_id} eliminado")
    
    async def _compensar_confirmacion(self, contexto: Dict[str, Any], datos: Dict[str, Any]):
        """Compensación: Marcar pedido como cancelado"""
        logger.info("↩️  Cancelando confirmación...")
        
        pedido = contexto.get('pedido')
        if pedido:
            pedido.estado = EstadoPedido.CANCELADO
            logger.info(f"  ✅ Pedido #{pedido.id} marcado como cancelado")
    
    # ========== CONSULTAS ==========
    
    def obtener_pedidos(self) -> List[Pedido]:
        """Obtiene todos los pedidos"""
        return self._pedidos.copy()
    
    def obtener_pedido_por_id(self, pedido_id: int) -> Pedido:
        """Obtiene un pedido por ID"""
        return next((p for p in self._pedidos if p.id == pedido_id), None)
    
    def obtener_reservas(self) -> Dict[int, int]:
        """Obtiene el estado de las reservas de inventario"""
        return self._reservas.copy()
