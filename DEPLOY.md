# 📦 Guía de Despliegue en EasyPanel

Esta guía te ayudará a desplegar la Cafetería API en EasyPanel paso a paso.

## 🎯 Configuración para EasyPanel

### 1. Configuración Básica

**Dockerfile Path:** `app/Dockerfile`  
**Port:** `8000`  
**Context Directory:** `app`

### 2. Variables de Entorno (Opcionales)

```env
REPO_BACKEND=memory
CIRCUIT_BREAKER_FAILURE_THRESHOLD=3
CIRCUIT_BREAKER_RECOVERY_TIMEOUT=30.0
```

### 3. Build Command (Automático)
EasyPanel detectará automáticamente el Dockerfile y lo construirá.

### 4. Start Command (Automático)
El comando está definido en el Dockerfile:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 🌐 Acceso después del Despliegue

- **Interfaz Principal:** `https://tu-dominio.easypanel.io/`
- **Panel Admin:** `https://tu-dominio.easypanel.io/ui/admin.html`
- **API Docs:** `https://tu-dominio.easypanel.io/docs`
- **API v1:** `https://tu-dominio.easypanel.io/api/v1/`

## ✅ Características en Producción

- ✅ Interfaz web como página principal
- ✅ API REST disponible en `/api/v1/`
- ✅ Documentación interactiva en `/docs`
- ✅ Panel de administración en `/ui/admin.html`
- ✅ Backend en memoria (sin persistencia, ideal para demos)

## 🔄 Cambiar a Backend Persistente

Si necesitas persistencia de datos, en las variables de entorno de EasyPanel:

```env
REPO_BACKEND=file
```

> **Nota:** Para producción real con múltiples instancias, considera usar `REPO_BACKEND=database` con una base de datos externa.

## 🛠️ Troubleshooting

### La aplicación no inicia
- Verifica que el puerto sea `8000`
- Revisa los logs en EasyPanel

### La interfaz no carga
- Asegúrate de que la ruta del Dockerfile sea `app/Dockerfile`
- Verifica que el contexto de build sea correcto

### Problemas con CORS
La aplicación tiene CORS configurado para permitir todos los orígenes. Si necesitas restringir, edita `app/main.py`.
