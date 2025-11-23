# Patrón Saga Orquestado - Cafetería API

## 📖 ¿Qué es el Patrón Saga?

El **Patrón Saga** es un patrón de diseño para gestionar transacciones distribuidas y mantener la consistencia de datos en sistemas donde no se pueden usar transacciones ACID tradicionales.

### Tipos de Saga

1. **Saga Coreografiada**: Cada servicio publica eventos y reacciona a eventos de otros servicios
2. **Saga Orquestada**: Un orquestador centralizado coordina todos los pasos ✅ **(Implementado aquí)**

## 🎯 Implementación

### Componentes

#### 1. **SagaOrchestrator** (`services/saga_orchestrator.py`)
Orquestador centralizado que:
- Ejecuta pasos secuencialmente
- Gestiona el contexto compartido
- Ejecuta compensaciones en orden inverso si algo falla
- Mantiene el estado de la saga

#### 2. **PedidoSagaService** (`services/pedido_saga_service.py`)
Servicio de negocio que implementa la saga de creación de pedidos con 4 pasos:

**Pasos de la Saga:**
1. ✅ **Validar Productos** - Verifica existencia y disponibilidad
2. ✅ **Reservar Inventario** - Bloquea stock temporalmente
3. ✅ **Crear Pedido** - Genera el pedido con cálculo de total
4. ✅ **Confirmar Pedido** - Confirma la transacción

**Compensaciones (Rollback):**
1. ↩️ Compensar Validación (sin cambios)
2. ↩️ **Liberar Reservas** - Devuelve el inventario reservado
3. ↩️ **Eliminar Pedido** - Borra el pedido creado
4. ↩️ **Cancelar Confirmación** - Marca pedido como cancelado

#### 3. **Modelos** (`domain/saga_models.py`)
- `Pedido`: Entidad de negocio del pedido
- `ItemPedido`: Items del pedido con cálculo de subtotal
- `SagaStep`: Representa un paso de la saga
- `EstadoSaga`: Estados posibles (INICIADA, EN_PROGRESO, COMPLETADA, COMPENSANDO, etc.)

#### 4. **API Router** (`api/v1/routers/pedidos.py`)
Endpoints REST para gestionar pedidos:
- `POST /api/v1/pedidos/` - Crear pedido con saga
- `GET /api/v1/pedidos/` - Listar pedidos
- `GET /api/v1/pedidos/{id}` - Obtener pedido
- `GET /api/v1/pedidos/inventario/reservas` - Ver reservas actuales

## 🚀 Uso

### Crear un Pedido

```bash
POST /api/v1/pedidos/
Content-Type: application/json

{
  "cliente": "Juan Pérez",
  "items": [
    {
      "producto_id": 1,
      "cantidad": 2
    },
    {
      "producto_id": 3,
      "cantidad": 1
    }
  ]
}
```

### Respuesta Exitosa

```json
{
  "mensaje": "Pedido creado exitosamente",
  "pedido": {
    "id": 1,
    "cliente": "Juan Pérez",
    "items": [
      {
        "producto_id": 1,
        "nombre": "Café Americano",
        "cantidad": 2,
        "precio_unitario": 2.50,
        "subtotal": 5.00
      },
      {
        "producto_id": 3,
        "nombre": "Latte",
        "cantidad": 1,
        "precio_unitario": 4.00,
        "subtotal": 4.00
      }
    ],
    "total": 9.00,
    "estado": "confirmado"
  },
  "saga": {
    "nombre": "CrearPedido-1",
    "estado": "completada",
    "steps": [
      {"nombre": "ValidarProductos", "ejecutado": true, "compensado": false},
      {"nombre": "ReservarInventario", "ejecutado": true, "compensado": false},
      {"nombre": "CrearPedido", "ejecutado": true, "compensado": false},
      {"nombre": "ConfirmarPedido", "ejecutado": true, "compensado": false}
    ]
  }
}
```

### Respuesta con Error (Con Compensación)

Si un producto no existe o no está disponible:

```json
{
  "detail": {
    "mensaje": "Error al crear pedido. Se han revertido todos los cambios.",
    "saga": {
      "nombre": "CrearPedido-1",
      "estado": "compensada",
      "steps": [
        {"nombre": "ValidarProductos", "ejecutado": true, "compensado": true},
        {"nombre": "ReservarInventario", "ejecutado": false, "compensado": false},
        {"nombre": "CrearPedido", "ejecutado": false, "compensado": false},
        {"nombre": "ConfirmarPedido", "ejecutado": false, "compensado": false}
      ]
    }
  }
}
```

## 📊 Diagrama de Flujo

```
┌─────────────────────────────────────────────────────────┐
│                   SAGA ORQUESTADOR                      │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
            ┌───────────────────────────┐
            │  1. Validar Productos     │ ✅
            └───────────────────────────┘
                            │
                     ┌──────┴──────┐
                     │   ¿Éxito?   │
                     └──────┬──────┘
                   Sí │     │ No
                      │     └─────► COMPENSAR (fin)
                      ▼
            ┌───────────────────────────┐
            │  2. Reservar Inventario   │ ✅
            └───────────────────────────┘
                            │
                     ┌──────┴──────┐
                     │   ¿Éxito?   │
                     └──────┬──────┘
                   Sí │     │ No
                      │     └─────► COMPENSAR Steps 1-2
                      ▼
            ┌───────────────────────────┐
            │  3. Crear Pedido          │ ✅
            └───────────────────────────┘
                            │
                     ┌──────┴──────┐
                     │   ¿Éxito?   │
                     └──────┬──────┘
                   Sí │     │ No
                      │     └─────► COMPENSAR Steps 1-3
                      ▼
            ┌───────────────────────────┐
            │  4. Confirmar Pedido      │ ✅
            └───────────────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │   COMPLETADA  │ 🎉
                    └───────────────┘
```

## 🔍 Ventajas del Patrón Saga

1. **Consistencia Eventual**: Garantiza que el sistema llegue a un estado consistente
2. **Sin Bloqueos**: No requiere locks distribuidos
3. **Resiliente**: Maneja fallos automáticamente
4. **Auditable**: Cada paso queda registrado
5. **Compensaciones Automáticas**: Rollback sin intervención manual

## 🎓 Conceptos Clave

### Estados de la Saga
- `INICIADA`: Saga creada pero no ejecutada
- `EN_PROGRESO`: Ejecutando pasos
- `COMPLETADA`: Todos los pasos exitosos
- `COMPENSANDO`: Ejecutando rollback
- `COMPENSADA`: Rollback completado
- `FALLIDA`: Error irrecuperable

### Idempotencia
Cada compensación debe ser **idempotente**, es decir, ejecutarla múltiples veces produce el mismo resultado.

### Contexto Compartido
El orquestador mantiene un contexto que se comparte entre todos los pasos, permitiendo pasar datos de un paso a otro.

## 🧪 Testing

Para probar la saga, puedes:

1. **Caso exitoso**: Crear pedido con productos válidos
2. **Caso de fallo**: Intentar con producto inexistente
3. **Ver reservas**: Consultar `GET /api/v1/pedidos/inventario/reservas`

## 📝 Logs

El orquestador genera logs detallados:

```
INFO: 🚀 Iniciando Saga: CrearPedido-1
INFO: ▶️  Ejecutando step: ValidarProductos
INFO: 🔍 Validando productos...
INFO: ✅ 2 productos validados
INFO: ✅ Step completado: ValidarProductos
INFO: ▶️  Ejecutando step: ReservarInventario
INFO: 🔒 Reservando inventario...
INFO:   📦 Reservados 2 de producto 1
INFO:   📦 Reservados 1 de producto 3
INFO: ✅ 2 reservas realizadas
INFO: ✅ Step completado: ReservarInventario
INFO: ▶️  Ejecutando step: CrearPedido
INFO: 📝 Creando pedido...
INFO: ✅ Pedido #1 creado - Total: $9.00
INFO: ✅ Step completado: CrearPedido
INFO: ▶️  Ejecutando step: ConfirmarPedido
INFO: ✅ Confirmando pedido...
INFO: 🎉 Pedido #1 confirmado exitosamente
INFO: ✅ Step completado: ConfirmarPedido
INFO: 🎉 Saga completada: CrearPedido-1
```

## 🔮 Extensiones Futuras

- Agregar timeouts para cada step
- Persistir estado de sagas en base de datos
- Reintentos automáticos con backoff exponencial
- Eventos asíncronos para notificaciones
- Dashboard de monitoreo de sagas
