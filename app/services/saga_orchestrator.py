from typing import List, Callable, Optional, Dict, Any
from dataclasses import dataclass, field
import logging
from domain.saga_models import EstadoSaga, SagaStep

logger = logging.getLogger(__name__)


@dataclass
class SagaOrchestrator:
    """
    Orquestador de Saga - Patrón Saga Orquestado
    
    Gestiona la ejecución de pasos transaccionales y sus compensaciones
    en caso de fallo, garantizando consistencia eventual.
    """
    nombre: str
    steps: List[SagaStep] = field(default_factory=list)
    estado: EstadoSaga = EstadoSaga.INICIADA
    contexto: Dict[str, Any] = field(default_factory=dict)
    
    def agregar_step(
        self,
        nombre: str,
        accion: Callable,
        compensacion: Callable
    ) -> 'SagaOrchestrator':
        """Agrega un paso a la saga con su acción y compensación"""
        step = SagaStep(nombre=nombre)
        self.steps.append(step)
        
        # Guardamos las funciones en el contexto
        if 'acciones' not in self.contexto:
            self.contexto['acciones'] = {}
        if 'compensaciones' not in self.contexto:
            self.contexto['compensaciones'] = {}
            
        self.contexto['acciones'][nombre] = accion
        self.contexto['compensaciones'][nombre] = compensacion
        
        return self
    
    async def ejecutar(self) -> bool:
        """
        Ejecuta todos los pasos de la saga.
        Si alguno falla, ejecuta las compensaciones en orden inverso.
        """
        logger.info(f"🚀 Iniciando Saga: {self.nombre}")
        self.estado = EstadoSaga.EN_PROGRESO
        
        try:
            # Ejecutar cada paso
            for step in self.steps:
                logger.info(f"▶️  Ejecutando step: {step.nombre}")
                accion = self.contexto['acciones'][step.nombre]
                
                try:
                    resultado = await accion(self.contexto)
                    step.ejecutado = True
                    step.datos_compensacion = resultado
                    logger.info(f"✅ Step completado: {step.nombre}")
                    
                except Exception as e:
                    logger.error(f"❌ Error en step {step.nombre}: {str(e)}")
                    # Si falla, compensar
                    await self._compensar()
                    self.estado = EstadoSaga.FALLIDA
                    return False
            
            # Todos los steps ejecutados exitosamente
            self.estado = EstadoSaga.COMPLETADA
            logger.info(f"🎉 Saga completada: {self.nombre}")
            return True
            
        except Exception as e:
            logger.error(f"💥 Error crítico en saga {self.nombre}: {str(e)}")
            await self._compensar()
            self.estado = EstadoSaga.FALLIDA
            return False
    
    async def _compensar(self):
        """Ejecuta las compensaciones en orden inverso"""
        logger.warning(f"🔄 Iniciando compensación de saga: {self.nombre}")
        self.estado = EstadoSaga.COMPENSANDO
        
        # Compensar en orden inverso
        for step in reversed(self.steps):
            if step.ejecutado and not step.compensado:
                logger.info(f"↩️  Compensando step: {step.nombre}")
                compensacion = self.contexto['compensaciones'][step.nombre]
                
                try:
                    await compensacion(self.contexto, step.datos_compensacion)
                    step.compensado = True
                    logger.info(f"✅ Compensación exitosa: {step.nombre}")
                except Exception as e:
                    logger.error(f"⚠️  Error en compensación de {step.nombre}: {str(e)}")
        
        self.estado = EstadoSaga.COMPENSADA
        logger.info(f"✅ Compensación completada: {self.nombre}")
    
    def obtener_estado(self) -> Dict[str, Any]:
        """Retorna el estado actual de la saga"""
        return {
            "nombre": self.nombre,
            "estado": self.estado.value,
            "steps": [
                {
                    "nombre": step.nombre,
                    "ejecutado": step.ejecutado,
                    "compensado": step.compensado
                }
                for step in self.steps
            ]
        }
